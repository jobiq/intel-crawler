from scraper.action import ScraperAction, ScraperItem
from scraper.config import ScraperActionConfig


class CustomConfig(ScraperActionConfig):
    expression: str
    target_field: str


class EvalAction(ScraperAction[CustomConfig]):
    uid = "jobiq.eval"

    async def _execute(self, scraper: ScraperItem):
        scraper.item[self.config["target_field"]] = eval(
            scraper.parse_string(self.config["expression"])
        )
