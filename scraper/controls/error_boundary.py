from scraper.action import ScraperAction, ScraperItem
from scraper.config import ScraperActionConfig


class CustomConfig(ScraperActionConfig):
    log: str


class ErrorBoundaryAction(ScraperAction[CustomConfig]):
    uid = "jobiq.controls.error_boundary"

    async def init(self):
        await super().init_children()

    async def _execute(self, scraper: ScraperItem):
        try:
            await self.execute_children(scraper)
        except Exception as e:
            print(f"🛡️ {e}")
