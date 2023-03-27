import psycopg2
import uuid
import re
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

# Get domains to scrape
cur.execute("SELECT domain FROM meta.domains WHERE crawl = TRUE")
domains = cur.fetchall()

# Create the Spider
class A11ySpider(Spider):
    name = "A11ySpider"

    # Where to Start?
    def start_requests(self):
        for domain in domains:
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
                        link = f"https://{domain}{link}"
                    cur.execute("""
                        INSERT INTO staging.urls (url, python_uuid, source_url)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (url) DO NOTHING
                    """, (link, str(python_uuid), source_url))

                    conn.commit()
                    # self.logger.info(f"Inserted {link} into staging.urls")

                    # Follow links to other pages on the same domain
                    if link.startswith(f"https://{domain}"):
                        yield Request(link, callback=self.parse, meta={"domain": domain, "python_uuid": python_uuid, "source_url": source_url})

# Crawler Settings
process = CrawlerProcess(settings={
    "ROBOTSTXT_OBEY": True,
    "AUTOTHROTTLE_ENABLED": True,
    "AUTOTHROTTLE_START_DELAY": 1,
    "AUTOTHROTTLE_TARGET_CONCURRENCY": 1,
    "LOG_LEVEL": "WARNING",
    "LOG_ENABLED": True
})
process.crawl(A11ySpider)
process.start()
