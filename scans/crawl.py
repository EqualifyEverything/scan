import psycopg2
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
            url = "https://" + domain[0]
            yield Request(url, callback=self.parse, meta={"domain": domain[0]})

    # How are we parsing this?
    def parse(self, response):
        domain = response.meta["domain"]

        # Get all links from the page
        links = response.css("a::attr(href)").getall()

        # Insert link to Postgres
        for link in links:
            if link is not None:
                cur.execute("INSERT INTO staging.urls (url) VALUES (%s)", (link,))
                conn.commit()
                self.logger.info(f"Inserted {link} into staging.urls")

# Crawler Settings
process = CrawlerProcess(settings={
    "ROBOTSTXT_OBEY": True,
    "AUTOTHROTTLE_ENABLED": True,
    "AUTOTHROTTLE_START_DELAY": 1,
    "AUTOTHROTTLE_TARGET_CONCURRENCY": 1,
})
process.crawl(A11ySpider)
process.start()
