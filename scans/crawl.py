import psycopg2
import uuid
import re
import time
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
cur.execute("SELECT domain FROM meta.domains WHERE crawl = TRUE AND active = TRUE ORDER BY created_at LIMIT 1")
domain = cur.fetchone()
if not domain:
    # No active domains left to crawl
    exit()

# Update crawl status for selected domain
cur.execute("UPDATE meta.domains SET crawl = FALSE, last_crawl_at = now() WHERE domain = %s", (domain[0],))

# Create the Spider
class A11ySpider(Spider):
    name = "A11ySpider"

    # Where to Start?
    def start_requests(self):
        # Generate UUID
        python_uuid = uuid.uuid4()

        # Insert Domain and UUID
        cur.execute("INSERT INTO results.crawls (domain, python_uuid) VALUES (%s, %s)", (domain[0], str(python_uuid)))

        url = "https://" + domain[0]
        yield Request(url, callback=self.parse, meta={"domain": domain[0], "python_uuid": python_uuid})

    # How are we parsing this?
    def parse(self, response):
        domain = response.meta["domain"] # get the domain from meta.domains
        python_uuid = response.meta["python_uuid"] # get the python_uuid
        source_url = response.url  # get the source URL

        # Get all links from the page
        try:
            links = response.css("a::attr(href)").getall()
        except Exception as e:
            self.logger.warning(f"Failed to parse {response.url} with error: {e}")
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
                    self.logger.info(f"Inserted {link} into staging.urls")

                    # Follow links to other pages on the same domain
                    if link.startswith(f"https://{domain}"):
                        #time.sleep(1) # wait for 1 second before crawling the next page on the same domain
                        yield Request(link, callback=self.parse, meta={"domain": domain, "python_uuid": python_uuid, "source_url": source_url})

        # Update crawl status for completed crawl
        cur.execute("UPDATE results.crawls SET complete = TRUE WHERE python_uuid = %s", (str(response.meta["python_uuid"]),))

        conn.commit()




# Crawler Settings
# Mote info:    https://docs.scrapy.org/en/latest/topics/settings.html
#
#       Testing out Autothrottle: https://docs.scrapy.org/en/latest/topics/autothrottle.html#autothrottle-algorithm
#
process = CrawlerProcess(settings={
    "BOT_NAME": "A11yCheck Bot",            # Name of Bot
    "DOWNLOAD_DELAY": 1,                # Minimum seconds to delay between requests
    "RANDOMIZE_DOWNLOAD_DELAY": True,      # Randomize DOWNLOAD_DELAY between 0.5 & 1.5x
    "COOKIES_ENABLED": False,               # Disable cookies
    "CONCURRENT_ITEMS": 50,                # Number of concurrent items (per response) to process
    "CONCURRENT_REQUESTS": 16,              # Maximum concurrent requests
    "DEPTH_LIMIT": 3,                        # Max depth that will be crawled. 0 for no limit
    "DNSCACHE_ENABLED": True,               # Enable DNS in-memory cache
    "DNS_TIMEOUT": 60,                      # Timeout for processing DNS queries
    "HTTPCACHE_ENABLED": True,              # Disable caching
    "CONCURRENT_REQUESTS_PER_DOMAIN": 16,   # Maximum concurrent requests per domain
    "ROBOTSTXT_OBEY": True,                 # Obey robots.txt rules
    "AUTOTHROTTLE_ENABLED": True,           # Enable AutoThrottle extension
    "AUTOTHROTTLE_START_DELAY": 5,          # Initial delay before AutoThrottle starts adjusting the delay
    "AUTOTHROTTLE_TARGET_CONCURRENCY": 1,   # Target concurrency for AutoThrottle
    "AUTOTHROTTLE_DEBUG": True,             # Debug logs on Autothrottle
    "LOG_LEVEL": "WARNING",                 # Logging level
    "LOG_ENABLED": True                     # Enable logging
})

process.crawl(A11ySpider)
process.start()
