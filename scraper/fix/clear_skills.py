from api.db import connect
from scraper.action import ScraperAction, ScraperItem
from scraper.config import ScraperActionConfig


class CustomConfig(ScraperActionConfig):
    filter: str
    scraper_id: int
    target_field: str


class ClearSkills(ScraperAction[CustomConfig]):
    uid = "jobiq.fix.clear_skills"

    async def _execute(self, scraper: ScraperItem):

        prisma = await connect()
        jobId = scraper.item["jobId"]
        item = await prisma.job.find_first(where={"jobId": jobId})
        if item is not None:
            await prisma.jobskill.delete_many(where={
                "jobId": item.id
            })
            await prisma.job.delete(where={"id": item.id})
            print("CLEARED JOB")
