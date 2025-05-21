from typing import List

from scraper.helpers import ExtractorConfig
from scraper.action import ScraperAction, ScraperItem
from scraper.config import ScraperActionConfig
from scraper.exception import ScraperException


class FieldConfig(ExtractorConfig):
    selector: str
    target_field: str


class CustomConfig(ScraperActionConfig):
    fields: List[FieldConfig]


class ExtractSoupFieldsAction(ScraperAction[CustomConfig]):
    uid = "jobiq.extract.soup_fields"

    async def init(self):
        self.fields = self.config["fields"] if "fields" in self.config else []

    async def _execute(self, scraper: ScraperItem):

        for field in self.fields:
            selector = field["selector"]
            
            # we can select by domains
            if "domain#" in field["selector"]:
                # find domain
                domain_name = next(
                    (d for d in self.shared_config["domains"] if d in scraper.current_url), None)
                if domain_name is None:
                    raise ScraperException(
                        "error", f"Domain not found in {scraper.current_url}")
                # split selector by #
                domain = self.shared_config["domains"][domain_name]
                item = field["selector"].split("#")
                # get the selector
                if item[1] not in domain:
                    raise ScraperException(
                        "error", f"Selector {item[1]} not found in {domain}")
                selector = domain[item[1]]
            
            soup = scraper.soup.select_one(selector)
            extracted = soup.extract_field(field, scraper.item)
            scraper.item[field["target_field"]] = extracted
