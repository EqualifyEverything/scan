import psycopg2
import uuid
import re
import time

import logging
from lxml import etree
from scrapy import Spider, Request
from scrapy.crawler import CrawlerProcess
from twisted.internet.error import DNSLookupError, TCPTimedOutError


logger = logging.getLogger(__name__)


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
print(f"Selected {domain} to crawl next")  # add this line to print the selected domain
if not domain:
    # No active domains left to crawl
    exit()

# Update crawl status for selected domain
cur.execute("UPDATE meta.domains SET crawl = FALSE, last_crawl_at = now() WHERE domain = %s", (domain[0],))

class A11ySpider(Spider):
    name = "A11ySpider"

    # Lets ROLL
    def start_requests(self):
        # Generate UUID
        python_uuid = uuid.uuid4()

        # Insert domain and UUID
        cur.execute("INSERT INTO results.crawls (domain, python_uuid) VALUES (%s, %s)", (domain[0], str(python_uuid)))
        conn.commit()  # commit the transaction
        self.logger.info(f"Created crawl for {domain} with python_uuid of: {python_uuid}")

        url = "https://" + domain[0]
        yield Request(url, callback=self.parse, meta={"domain": domain[0], "python_uuid": python_uuid}, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36'}, errback=self.errback)


    # Parse All The Things!
    def parse(self, response):
        domain = response.meta["domain"] # Get the domain from meta.domains
        python_uuid = response.meta["python_uuid"] # Get the python_uuid
        source_url = response.url  # Get the source URL

        # Get all links from the page
        links = response.xpath("//a/@href").getall()


        # Insert link to Postgres
        for link in links:
            if link is not None:

                # Filter out URLs with "#" and remove trailing "/"
                link = re.sub(r"#.*$", "", link).rstrip("/")
                if not re.search(r'tel:|mailto:| ', link):
                    # Determine the file type of the URL based on its extension
                    file_extension = link.split(".")[-1].lower()
                    if file_extension in ["pdf", "doc", "docx", "ppt", "pptx", "xls", "xlsx", "xml", "csv", "zip", "pages"]:
                        # Add document URLs to the staging.doc_urls table
                        cur.execute("""
                            INSERT INTO staging.doc_urls (url, source_url, python_uuid)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (url) DO NOTHING
                        """, (link, source_url, str(python_uuid)))
                        conn.commit()  # commit the transaction
                        logger.debug(f"Doc: +1 URL to staging.doc_urls table: {link}")
                    elif file_extension in ["jpg", "jpeg", "png", "gif", "svg", "bmp"]:
                        # Add image URLs to the staging.image_urls table
                        cur.execute("""
                            INSERT INTO staging.image_urls (url, source_url, python_uuid)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (url) DO NOTHING
                        """, (link, source_url, str(python_uuid)))
                        logger.debug(f"Image: +1 URL to staging.image_urls table: {link}")
                        conn.commit()  # commit the transaction
                    else:
                        # Add URLs that do not fit into either of the above to the staging.urls table
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
                        conn.commit()  # commit the transaction
                        logger.debug(f"URL: +1 URL to staging.urls table: {link}")


                        # Follow links to other pages on the same domain
                        if link.startswith(f"https://{domain}"):
                            yield Request(link, callback=self.parse, meta={"domain": domain, "python_uuid": python_uuid, "source_url": source_url})

        # Check if the response is a Request object and it didn't follow any link
        if isinstance(response, Request) and not response.follows:
            cur.execute("UPDATE results.crawls SET complete = TRUE WHERE python_uuid = %s", (str(python_uuid),))
            cur.execute("UPDATE meta.domains SET crawl = TRUE, last_crawl_at = now(), last_crawl_uuid = %s WHERE domain = %s", (str(python_uuid), domain[0]))
            conn.commit()
            logger.info(f"Crawl Complete for: {domain} ")
            cur.execute("SELECT process_staging_urls()")
            logger.info(f"Staging URLs Processed, Moving to Next Domain :)")

    # Bringing errBack!
    def errback(self, failure):
        url = failure.request.url
        python_uuid = str(failure.request.meta["python_uuid"])
        source_url = failure.request.meta.get("source_url")

        # Add naughty URLs to the staging.bad_urls table
        if not url.startswith("http"):
            if url.startswith("/"):
                url = f"https://{domain}{url}"
            else:
                url = f"https://{domain}/{url}"
        cur.execute("""
            INSERT INTO staging.bad_urls (url, python_uuid, source_url)
            VALUES (%s, %s, %s)
            ON CONFLICT (url) DO NOTHING
        """, (url, python_uuid, source_url))
        conn.commit()  # commit the transaction
        logger.warning(f"Bad URL: Added 1 URL to staging.bad_urls table: {link}")

        # Stalk links to other pages on the same domain
        if url.startswith(f"https://{domain}"):
            yield Request(url, callback=self.parse, meta={"domain": domain, "python_uuid": python_uuid, "source_url": source_url}, errback=self.errback)



# Crawler Settings
# Mote info:    https://docs.scrapy.org/en/latest/topics/settings.html
#
# Testing out Autothrottle: https://docs.scrapy.org/en/latest/topics/autothrottle.html#autothrottle-algorithm
#
process = CrawlerProcess(settings={
    "BOT_NAME": "A11yCheck Bot",            # Name of Bot
    #"DOWNLOAD_DELAY": 1,                   # Minimum seconds to delay between requests
    #"RANDOMIZE_DOWNLOAD_DELAY": True,      # Randomize DOWNLOAD_DELAY between 0.5 & 1.5x
    "COOKIES_ENABLED": False,               # Disable cookies
    "CONCURRENT_ITEMS": 50,                 # Number of concurrent items (per response) to process
    "CONCURRENT_REQUESTS": 16,              # Maximum concurrent requests
    #"DEPTH_LIMIT": 3,                      # Max depth that will be crawled. 0 for no limit
    "DNSCACHE_ENABLED": True,               # Enable DNS in-memory cache
    "DNS_TIMEOUT": 60,                      # Timeout for processing DNS queries
    "HTTPCACHE_ENABLED": False,             # Enable or disable caching

    "CONCURRENT_REQUESTS_PER_DOMAIN": 16,   # Maximum concurrent requests per domain
    "ROBOTSTXT_OBEY": True,                 # Obey robots.txt rules
    "AUTOTHROTTLE_ENABLED": True,           # Enable AutoThrottle extension
    "AUTOTHROTTLE_START_DELAY": 5,          # Initial delay before AutoThrottle starts adjusting the delay

    "AUTOTHROTTLE_TARGET_CONCURRENCY": 2,   # Target concurrency for AutoThrottle
    # Logging Settings
    "AUTOTHROTTLE_DEBUG": False,             # Debug logs on Autothrottle
    "LOG_LEVEL": "INFO",                   # Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL
    #"LOG_FILE": "logs/crawl.log",          # Where to save lovs

    "LOG_ENABLED": True                     # Enable logging
})

process.crawl(A11ySpider)
process.start()
