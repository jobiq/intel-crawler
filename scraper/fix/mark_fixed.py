
from prisma.enums import JobStatus

from api.db import connect
from scraper.action import ScraperAction, ScraperItem
from scraper.config import ScraperActionConfig


class CustomConfig(ScraperActionConfig):
    filter: str
    scraper_id: int
    target_field: str


class MarkFixed(ScraperAction[CustomConfig]):
    uid = "jobiq.fix.mark_fixed"

    async def _execute(self, scraper: ScraperItem):

        prisma = await connect()
        jobId = str(scraper.item["jobId"])
        item = await prisma.processedjob.find_first(where={"jobId": jobId})
        if item is not None:
            await prisma.processedjob.update(where={
                "id": item.id
            }, data={
                "status": JobStatus.Processed,
                "message": "fixed"
            })
            print("🎉 FIXED!")
