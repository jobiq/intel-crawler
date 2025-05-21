from scraper.action import ScraperAction, ScraperItem
from scraper.config import ScraperActionConfig
from scraper.types import QueueProcessItem


class CustomConfig(ScraperActionConfig):
    max_processes: int

class StartProcess(ScraperAction[CustomConfig]):
    uid = "jobiq.multiprocessing.start"

    # async def init(self):
    #     await super().init_children()

    async def _execute(self, scraper: ScraperItem):
        runId = scraper.context.runId
        if runId is None:
            raise Exception("RunId is required")

        children = self.config["CHILDREN"] if "CHILDREN" in self.config else []
        if len(children) == 0:
            raise Exception("This action needs to have children")

        item: QueueProcessItem = {
            "item": scraper.item,
            "slot": 0,
            "scraper_id": scraper.context.scraper.id,
            "run_id": runId,
            "config": {
                "actions": children,
                "properties": self.shared_config,
            },
        }

        max_processes = self.config['max_processes'] if 'max_processes' in self.config else None

        scraper.context.queue.worker_manager.schedule(item, max_processes=max_processes)
