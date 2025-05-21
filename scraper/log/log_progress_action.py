from scraper.action import ScraperAction, ScraperItem
from scraper.config import ScraperActionConfig


class CustomConfig(ScraperActionConfig):
    message: str
    increase_current: int


class LogProgressAction(ScraperAction[CustomConfig]):
    uid = "jobiq.log_progress"

    async def init(self):
        pass

    async def _execute(self, scraper: ScraperItem):
        if "increase_current" in self.config:
            scraper.context.current_record += self.config["increase_current"]

        scraper.context.log_progress(scraper.parse_string(self.config["message"]))
