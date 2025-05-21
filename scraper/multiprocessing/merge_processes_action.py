from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scraper.action import ScraperItem
    # from scraper.queue import ScraperQueue

from scraper.action import ScraperAction
from scraper.config import ScraperActionConfig

class MergeProcess(ScraperAction[ScraperActionConfig]):
    uid = "jobiq.multiprocessing.merge"

    async def _execute(self, scraper: ScraperItem):
        queue = scraper.context.queue
        queue.worker_manager.wait_for_slots_to_finish()
