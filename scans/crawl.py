import psycopg2
import uuid
import re
import time
from lxml import etree
from scrapy import Spider, Request
from scrapy.crawler import CrawlerProcess

# Postgre connection info
db_host = "localhost"
db_port = 8432
db_user = "a11yPython"
db_password = "SnakeInTheWeb"
db_name = "a11y"

# Connect to database
conn = psycopg2.connect(host=db_host, port=db_port, user=db_user, password=db_password, database=db_name)
cur = conn.cursor()

# Get a single domain to scrape
cur.execute("SELECT domain, last_crawl_at FROM meta.domains WHERE crawl = TRUE AND active = TRUE ORDER BY last_crawl_at ASC NULLS FIRST LIMIT 1")
domain = cur.fetchone()
if not domain:
    # No active domains left to crawl
    exit()

# Update crawl status for selected domain
cur.execute("UPDATE meta.domains SET crawl = FALSE, last_crawl_at = now() WHERE domain = %s", (domain[0],))

# Create the Spider
class A11ySpider(Spider):
    name = "A11ySpider"

    # Define errback function
    def errback(self, failure):
        self.logger.warning(f"Request failed: {failure.value.response.url}. Inserting to staging.bad_urls table.")
        # Insert failed URL to staging.bad_urls table
        cur.execute("""
            INSERT INTO staging.bad_urls (url, source_url, python_uuid)
            VALUES (%s, %s, %s)
            ON CONFLICT (url) DO NOTHING
        """, (failure.value.response.url, failure.request.meta["source_url"], str(failure.request.meta["python_uuid"])))
        conn.commit()

    # Where to Start?
    def start_requests(self):
        # Generate UUID
        python_uuid = uuid.uuid4()

        # Insert Domain and UUID
        cur.execute("INSERT INTO results.crawls (domain, python_uuid) VALUES (%s, %s)", (domain[0], str(python_uuid)))

        url = "https://" + domain[0]
        yield Request(url, callback=self.parse, meta={"domain": domain[0], "python_uuid": python_uuid}, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36'})


    # How are we parsing this?
    def parse(self, response):
        domain = response.meta["domain"] # get the domain from meta.domains
        python_uuid = response.meta["python_uuid"] # get the python_uuid
        source_url = response.url  # get the source URL

        # Get all links from the page
        try:
            links = response.xpath("//a/@href").getall()
        except twisted.internet.error.ResponseNeverReceived as e:
            self.logger.warning(f"Failed to parse {response.url} because: {e}. Inserting to staging.doc_urls table.")
            # Insert failed URL to staging.doc_urls table
            cur.execute("""
                INSERT INTO staging.doc_urls (url, source_url, python_uuid)
                VALUES (%s, %s, %s)
                ON CONFLICT (url) DO NOTHING
            """, (response.url, source_url, str(python_uuid)))
            conn.commit()
            return

        # Insert link to Postgres
        for link in links:
            if link is not None:
                # filter out urls with "#" and remove trailing "/"
                link = re.sub(r"#.*$", "", link).rstrip("/")
                if not re.search(r'tel:|mailto:| ', link):
                    if not link.startswith("http"):
                        if link.startswith("/"):
                            link = f"https://{domain}{link}"
                        else:
                            link = f"https://{domain}/{link}"
                    cur.execute("""
                        INSERT INTO staging.urls (url, python_uuid, source_url)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (url) DO NOTHING
                    """, (link, str(python_uuid), source_url))

                    conn.commit()
                   # self.logger.info(f"Inserted {link} into staging.urls")

                    # Follow links to other pages on the same domain
                    if link.startswith(f"https://{domain}"):
                        #time.sleep(1) # wait for 1 second before crawling the next page on the same domain
                        yield Request(link, callback=self.parse, meta={"domain": domain, "python_uuid": python_uuid, "source_url": source_url})






# Crawler Settings
# Mote info:    https://docs.scrapy.org/en/latest/topics/settings.html
#
#       Testing out Autothrottle: https://docs.scrapy.org/en/latest/topics/autothrottle.html#autothrottle-algorithm
#
process = CrawlerProcess(settings={
    "BOT_NAME": "A11yCheck Bot",            # Name of Bot
    #"DOWNLOAD_DELAY": 1,                    # Minimum seconds to delay between requests
    #"RANDOMIZE_DOWNLOAD_DELAY": True,       # Randomize DOWNLOAD_DELAY between 0.5 & 1.5x
    "COOKIES_ENABLED": False,               # Disable cookies
    "CONCURRENT_ITEMS": 50,                 # Number of concurrent items (per response) to process
    "CONCURRENT_REQUESTS": 16,              # Maximum concurrent requests
    #"DEPTH_LIMIT": 3,                       # Max depth that will be crawled. 0 for no limit
    "DNSCACHE_ENABLED": True,               # Enable DNS in-memory cache
    "DNS_TIMEOUT": 60,                      # Timeout for processing DNS queries
    "HTTPCACHE_ENABLED": False,             # Enable or disable caching
    "CONCURRENT_REQUESTS_PER_DOMAIN": 16,   # Maximum concurrent requests per domain
    "ROBOTSTXT_OBEY": True,                 # Obey robots.txt rules
    "AUTOTHROTTLE_ENABLED": True,           # Enable AutoThrottle extension
    "AUTOTHROTTLE_START_DELAY": 5,          # Initial delay before AutoThrottle starts adjusting the delay
    "AUTOTHROTTLE_TARGET_CONCURRENCY": 2,   # Target concurrency for AutoThrottle
    "AUTOTHROTTLE_DEBUG": True,             # Debug logs on Autothrottle
    "LOG_LEVEL": "DEBUG",                   # Logging level
    #"LOG_FILE": "logs/crawl.log",           # Where to save lovs
    "LOG_ENABLED": True                     # Enable logging
})

process.crawl(A11ySpider)
process.start()
