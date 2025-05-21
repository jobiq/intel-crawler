from typing import Any, Dict

from typing_extensions import NotRequired

from scraper.helpers import fetch_graphql
from scraper.action import ScraperAction, ScraperItem
from scraper.config import ScraperActionConfig


class CustomConfig(ScraperActionConfig):
    url: str
    query: str
    query_name: str
    target_field: NotRequired[str]
    variables: Dict[str, Any]


class GraphqlRequest(ScraperAction[CustomConfig]):
    uid = "jobiq.request.graphql"

    async def init(self):
        self.url = self.config["url"]
        self.query = self.config["query"]
        self.variables = self.config["variables"]
        self.target_field = self.config["target_field"] if "target_field" in self.config else None

    async def _execute(self, scraper: ScraperItem):
        # process url
        url = scraper.parse_string(self.url)

        # parse variables and add values from the item
        parsed_variables = {}
        for key, value in self.variables.items():
            parsed_variables[key] = scraper.parse_string(value)

        data = fetch_graphql(url, self.query, parsed_variables)

        scraper.url = url
        scraper.source = data

        if self.target_field is not None:
            scraper.item[self.target_field] = next(iter(data["data"].values()))
        else:
            scraper.item = {
                **scraper.item,
                **data["data"][self.config["query_name"]]
            }
