import time

from typing_extensions import NotRequired

from scraper.helpers import fetch_json
from scraper.action import ScraperAction, ScraperItem
from scraper.config import ScraperActionConfig


class CustomConfig(ScraperActionConfig):
    url: str
    target_field: str
    url_field: NotRequired[str]
    validation: NotRequired[str] = None


class RequestJsonAction(ScraperAction[CustomConfig]):
    uid = "jobiq.request.json"

    async def init(self):
        self.url = self.config["url"]
        self.validation = self.config["validation"] if "validation" in self.config else None

    async def _execute(self, scraper: ScraperItem):
        # process url
        url = scraper.parse_string(self.url)

        data = fetch_json(url, self.validation)

        scraper.url = url
        scraper.source = data
        scraper.item[self.config["target_field"]] = data

        if "url_field" in self.config:
            scraper.item[self.config["url_field"]] = url

        time.sleep(1)
