import os
import pg8000
import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.selector import Selector
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from urllib.parse import urljoin
import time
import logging


class PostgresPipeline:
    def open_spider(self, spider):
        max_retries = 100
        delay_seconds = 5

        for _ in range(max_retries):
            try:
                self.connection = pg8000.connect(
                    host='db',
                    port='5432',
                    user=os.environ['POSTGRES_USER'],
                    password=os.environ['POSTGRES_PASSWORD'],
                    database=os.environ['POSTGRES_DB']
                )
                break  # Connection successful, exit the retry loop
            except pg8000.Error as e:
                logging.error('Error connecting to the database: %s', str(e))
                time.sleep(delay_seconds)
        else:
            logging.error('Failed to connect to the database after multiple retries. Exiting...')

        self.cursor = self.connection.cursor()
        self.cursor.execute("DROP TABLE IF EXISTS property_table")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS property_table (title VARCHAR, image_url VARCHAR, url VARCHAR)")
        self.connection.commit()

    def close_spider(self, spider):
        self.cursor.close()
        self.connection.close()

    def process_item(self, item, spider):
        try:
            self.cursor.execute(
                "INSERT INTO property_table (title, image_url, url) VALUES (%s, %s, %s)",
                (item['title'], item['image_url'], item['url'])
            )
            self.connection.commit()
        except pg8000.Error as e:
            logging.error('Error inserting item into the database: %s', str(e))

        return item


class ListingsSpider(scrapy.Spider):
    name = 'listings'
    start_urls = ['https://www.sreality.cz/hledani/prodej/byty']
    item_limit = 500

    custom_settings = {
        'ITEM_PIPELINES': {'__main__.PostgresPipeline': 1},
        'CONCURRENT_REQUESTS': 1
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        options = webdriver.ChromeOptions()
        options.headless = True
        options.add_argument("window-size=1920x1080")
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        self.driver = webdriver.Remote("http://selenium:4444/wd/hub", DesiredCapabilities.CHROME, options=options)
        self.wait = WebDriverWait(self.driver, 10)
        self.item_count = 0

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url, self.parse)

    def parse(self, response, **kwargs):
        self.driver.get(response.url)
        try:
            self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'div.property')))
            sel = Selector(text=self.driver.page_source, type="html")
            listings = sel.css('div.property')

            for listing in listings:
                title = listing.css('span.name::text').get()
                image_urls = listing.css('a img::attr(src)').getall()
                if not image_urls:
                    logging.warning('No image URL found for listing: %s', title)
                    continue
                image_url = urljoin(response.url, image_urls[0])
                relative_url = listing.css('a.title::attr(href)').get()
                url = urljoin(response.url, relative_url)
                data = {
                    'title': title,
                    'image_url': image_url,
                    'url': url
                }

                yield data

                self.item_count += 1
                if self.item_count >= ListingsSpider.item_limit:
                    break

            next_page = sel.css('a.paging-next::attr(href)').get()
            if next_page is not None and self.item_count < ListingsSpider.item_limit:
                yield response.follow(next_page, self.parse)
        except Exception as e:
            logging.error('Error occurred while parsing the page: %s', str(e))

    def closed(self, reason):
        self.driver.quit()


if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

    # Run the spider
    process = CrawlerProcess()
    process.crawl(ListingsSpider)
    process.start()
