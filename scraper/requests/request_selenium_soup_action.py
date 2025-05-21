from bs4 import BeautifulSoup

from scraper.helpers import Souped
from scraper.action import ScraperAction, ScraperItem
from scraper.config import ScraperActionConfig


class CustomConfig(ScraperActionConfig):
    url: str
    wait_css: str
    wait_xpath: str


class SeleniumRequest(ScraperAction[CustomConfig]):
    uid = "jobiq.request.selenium.soup"

    async def init(self):
        self.wait_css = self.config["wait_css"] if "wait_css" in self.config else None
        self.wait_xpath = self.config["wait_xpath"] if "wait_xpath" in self.config else None

    async def _execute(self, scraper: ScraperItem):
        # process url
        url = scraper.parse_string(self.config["url"])

        data = scraper.app.selenium.load_page(url, self.wait_css, self.wait_xpath)

        scraper.url = url
        scraper.current_url = scraper.app.selenium.driver.current_url
        
        scraper.source = data
        scraper.soup = Souped(BeautifulSoup(data, "html.parser"))

