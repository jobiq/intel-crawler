from bs4 import BeautifulSoup

from scraper.helpers import Souped, fetch_url
from scraper.action import ScraperAction, ScraperItem
from scraper.config import ScraperActionConfig


class CustomConfig(ScraperActionConfig):
    url: str
    query: str
    variables: str


class RequestSoup(ScraperAction[CustomConfig]):
    uid = "jobiq.request.soup"

    async def init(self):
        self.url = self.config["url"]

    async def _execute(self, scraper: ScraperItem):
        # process url
        url = scraper.parse_string(self.url)

        data = fetch_url(url)

        scraper.url = url
        scraper.current_url = url
        scraper.source = data
        scraper.soup = Souped(BeautifulSoup(data, "html.parser"))
