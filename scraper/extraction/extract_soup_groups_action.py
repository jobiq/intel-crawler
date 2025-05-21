from typing import List

from typing_extensions import NotRequired

from scraper.helpers import ExtractorConfig
from scraper.action import ScraperAction, ScraperItem
from scraper.config import ScraperActionConfig


class FieldConfig(ExtractorConfig):
    selector: str
    target_field: str


class CustomConfig(ScraperActionConfig, ExtractorConfig):
    fields: NotRequired[List[FieldConfig]]
    selector: str
    target_field: str
    count_field: NotRequired[str]
    record_count: NotRequired[str]

    on_none: NotRequired[str]
    on_value: NotRequired[str]


class ExtractSoupGroupsAction(ScraperAction[CustomConfig]):
    uid = "jobiq.extract.soup_groups"

    async def init(self):

        self.selector = self.config["selector"]
        self.target_field = self.config["target_field"]
        self.fields = self.config["fields"] if "fields" in self.config else []

        await super().init_children()

    async def _execute(self, scraper: ScraperItem):
        

        # select all parent fields
        soups = scraper.soup.select(self.selector)

        # if count_field is specified, set the count
        if "count_field" in self.config:
            scraper.item[self.config["count_field"]] = len(soups)

        # if record_count is specified, set the count
        if "record_count" in self.config:
            page_count = int(scraper.parse_string(self.config["record_count"]))
            scraper.context.total_records = page_count * len(soups)

        found = False

        # in each selected field extract what is necessary
        for parent in soups:

            # first extract the field
            if len(self.fields) == 0:
                item = parent.extract_field(self.config, scraper.item)
            else:
                item = {}
                # construct the new field
                for field in self.fields:
                    soup = parent.select_one(field["selector"])
                    extracted = soup.extract_field(field, scraper.item)
                    item[field["target_field"]] = extracted

            # if we have no value we may choose to skip
            if item is None and "on_none" in self.config:
                if self.config["on_none"] == "skip":
                    continue

            # now process the children with the new context
            child_item = scraper.clone()
            child_item.item[self.target_field] = item

            await self.execute_children(child_item)

            found = True

            # we can stop after first item
            if "on_value" in self.config and item is not None:
                if self.config["on_value"] == "break":
                    break

        if found is False:
            raise Exception(
                f"Error fixing record ({scraper.url}, {scraper.item["filter"]}) - no items found for selector {self.selector}")
            

