from scraper.action import ScraperAction, ScraperItem
from scraper.config import ScraperActionConfig


class CustomConfig(ScraperActionConfig):
    text: str
    field: str


class LogAction(ScraperAction[CustomConfig]):
    uid = "jobiq.log"

    async def init(self):
        pass

    async def _execute(self, scraper: ScraperItem):
        # process url
        print(
            (scraper.parse_string(self.config["text"]) if "text" in self.config else "") +
            (scraper.resolve(self.config["field"])
             if "field" in self.config else "")
        )
