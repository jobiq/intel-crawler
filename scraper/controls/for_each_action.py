from typing_extensions import NotRequired

from scraper.helpers import find_parent
from scraper.action import ScraperAction, ScraperItem
from scraper.config import ScraperActionConfig


class CustomConfig(ScraperActionConfig):
    source_field: str
    target_field: str
    index_field: NotRequired[str]
    record_count: NotRequired[str]


class ForEachAction(ScraperAction[CustomConfig]):
    uid = "jobiq.controls.for_each"

    async def init(self):

        await super().init_children()

    async def _execute(self, scraper: ScraperItem):

        values = find_parent(self.config["source_field"], scraper.item)

        # if record_count is specified, set the count
        if "record_count" in self.config:
            page_count = int(scraper.parse_string(self.config["record_count"]))
            scraper.context.total_records = page_count * len(values)

        i = 0
        for i, value in enumerate(values):
            new_item = scraper.clone()
            if "index_field" in self.config:
                new_item.item[self.config["index_field"]] = i
            new_item.item[self.config["target_field"]] = value
            await self.execute_children(new_item)
