from typing import Union

import scrapy
from scrapy import Selector, Spider
from scrapy.http import Response
from selenium import webdriver
from selenium.webdriver.common.by import By
from twisted.internet.defer import Deferred


class BookSpider(scrapy.Spider):
    name = "book"
    allowed_domains = ["books.toscrape.com"]
    start_urls = ["https://books.toscrape.com/"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.driver = webdriver.Chrome()

    def close(self: Spider, reason: str) -> Union[Deferred, None]:
        self.driver.quit()

    def parse(self, response: Response, **kwargs):
        for book in response.css(".product_pod"):
            yield {
                "title": book.css("a::attr(title)").get(),
                "price": float(book.css(".price_color::text").get()[1:]),
                "rating": book.css(
                    "p.star-rating::attr(class)"
                ).get().split()[-1],
                **self._get_detailed_info(response, book)
            }

        next_page = response.css(".next > a::attr(href)").get()

        if next_page:
            yield response.follow(next_page, callback=self.parse)

    def _get_detailed_info(self, response: Response, book: Selector) -> dict:
        detail_url = response.urljoin(book.css("a::attr(href)").get())
        driver = self.driver
        driver.get(detail_url)

        return {
            "amount_in_stock": int(
                driver.find_element(
                    By.CLASS_NAME, "instock"
                ).text.split()[2][1:]
            ),
            "category": driver.find_element(
                By.XPATH, "//tr[th[text()='Product Type']]/td"
            ).text,
            "description": driver.find_element(
                By.CSS_SELECTOR, "article.product_page > p"
            ).text,
            "upc": driver.find_element(
                By.XPATH, "//tr[th[text()='UPC']]/td"
            ).text
        }
