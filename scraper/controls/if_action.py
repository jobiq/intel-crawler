from typing_extensions import NotRequired

from scraper.action import ScraperAction, ScraperItem
from scraper.config import ScraperActionConfig


class CustomConfig(ScraperActionConfig):
    condition: str
    true: str
    false: NotRequired[str]


class IfAction(ScraperAction[CustomConfig]):
    uid = "jobiq.controls.if"

    async def init(self):
        await super().init_children()

    async def _execute(self, scraper: ScraperItem):
        should_execute = eval(scraper.parse_string(self.config["condition"]))

        if should_execute:
            await self.execute_children(scraper)
