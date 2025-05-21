from typing_extensions import NotRequired

from scraper.action import ScraperAction, ScraperItem
from scraper.config import ScraperActionConfig


class CustomConfig(ScraperActionConfig):
    count: str
    start_index: NotRequired[int]
    index_field: str


class Repeat(ScraperAction[CustomConfig]):
    uid = "jobiq.controls.repeat"

    async def init(self):

        self.count = self.config["count"]
        self.start = self.config["start_index"] if "start_index" in self.config else 0
        self.index_field = self.config["index_field"]

        await super().init_children()

    async def _execute(self, scraper: ScraperItem):
        count = int(scraper.parse_string(self.count))
        for i in range(self.start, count + self.start):
            new_item = scraper.clone()
            new_item.item[self.index_field] = i
            await self.execute_children(new_item)
