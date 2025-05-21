from typing import Any

from scraper.action import ActionRepository, ScraperAction, ScraperItem
from scraper.config import ScraperConfig


class WrapperAction(ScraperAction[Any]):
    uid = "jobiq.wrapper"

    def __init__(self, config: ScraperConfig, shared_config: Any, repository: ActionRepository):
        wrapped_config: Any = {
            "name": f"Wrapper (jobiq.wrapper)",
            "CHILDREN": config["actions"]
        }
        super().__init__(wrapped_config, shared_config, repository)

    async def init(self):
        await super().init_children()

    async def _execute(self, scraper: ScraperItem):
        await self.execute_children(scraper)
