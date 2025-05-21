import json
from typing import Any

from api.db import connect
from scraper.helpers import current_date
from scraper.action import ScraperAction, ScraperItem
from scraper.exception import ScraperException

class FlagProcessedJob(ScraperAction[Any]):
    uid = "jobiq.check_processed_job"

    async def init(self):
        self.prisma = await connect()
        self.selector = self.config["selector"] if "selector" in self.config else None
        self.source_field = self.config["source_field"] if "source_field" in self.config else None

    async def _execute(self, scraper: ScraperItem):

        if self.selector is not None:
            id = scraper.resolve(self.selector)
        else:
            id = scraper.item["jobId"]

        existing = await self.prisma.processedjob.find_first(where={
            "jobId": str(id)
        })

        if (existing is not None):
            scraper.context.existing += 1
            scraper.item["processedJobId"] = existing.id
            raise ScraperException(
                "info", f"Job {id} has already been processed")

        # bj = await self.prisma.job.find_first(where={
        #     "jobId": id
        # })
        # if (bj is not None):
        #     raise ScraperException(
        #         "info", f"Job {id} has already been processed")

        if existing is None:
            existing = await self.prisma.processedjob.create(data={
                "data": json.dumps(
                    scraper.resolve(
                        self.source_field) if self.source_field is not None else scraper.item
                ),
                "date": current_date(),
                "scraper": scraper.context.scraper.id,
                "jobId": str(id)
            })

        scraper.item["processedJobId"] = existing.id
