from typing_extensions import NotRequired

from scraper.action import ScraperAction, ScraperItem
from scraper.config import ScraperActionConfig


class CustomConfig(ScraperActionConfig):
    step_name: str
    step_number: int
    step_count: NotRequired[int]


class LogStepAction(ScraperAction[CustomConfig]):
    uid = "jobiq.log_step"

    async def init(self):
        pass

    async def _execute(self, scraper: ScraperItem):
        scraper.context.step_name = self.config["step_name"]
        scraper.context.step = self.config["step_number"]

        if "step_count" in self.config:
            scraper.context.steps = self.config["step_count"]
