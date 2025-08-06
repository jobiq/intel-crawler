from typing_extensions import NotRequired

from scraper.action import ScraperAction, ScraperItem
from scraper.config import ScraperActionConfig


class CustomConfig(ScraperActionConfig):
    count: str
    start_index: str
    index_field: str


class Repeat(ScraperAction[CustomConfig]):
    uid = "jobiq.controls.repeat"

    async def init(self):

        self.count = self.config["count"]
        self.start_index = self.config["start_index"] 
        self.index_field = self.config["index_field"]

        await super().init_children()

    async def _execute(self, scraper: ScraperItem):
        count = int(scraper.parse_string(self.count))
        start = int(scraper.parse_string(self.start_index))

        for i in range(start, count + start):
            new_item = scraper.clone()
            new_item.item[self.index_field] = i
            await self.execute_children(new_item)
