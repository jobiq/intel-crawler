import json

from prisma.enums import JobStatus
from prisma.types import ProcessedJobWhereInput

from api.db import connect
from scraper.action import ScraperAction, ScraperItem
from scraper.config import ScraperActionConfig


class CustomConfig(ScraperActionConfig):
    filter: str
    scraper_id: int
    target_field: str
    count_field: str
    take: int


class ListErrorAction(ScraperAction[CustomConfig]):
    uid = "jobiq.fix.list_errors"

    async def init(self):

        await super().init_children()

    async def _execute(self, scraper: ScraperItem):

        take = self.get_int_config('take', scraper, 0)
        fix_filter = self.get_string_config('filter', scraper, '')
        scraper_id = self.get_int_config('scraper_id', scraper, 12)

        db_filter: ProcessedJobWhereInput = {
            "status": JobStatus.Error,
            "scraper": scraper_id
        }

        prisma = await connect()

        if fix_filter != '':
            db_filter["message"] = {
                "contains": fix_filter
            }

        total = await prisma.processedjob.count(where=db_filter)
        total = take if take > 0 and take < total else total

        print(f"👾 Fixing {total} records")

        scraper.context.total_records = total
        single_take = 20

        if 'count_field' in self.config:
            scraper.item[self.config["count_field"]] = total

        i = 0
        skip = 0
        while total > 0:
            records = await prisma.processedjob.find_many(where=db_filter, skip=skip, take=single_take)

            if (len(records) == 0):
                print("🚀 No more records to fix")
                break

            for record in records:
                new_item = scraper.clone()
                if "index_field" in self.config:
                    new_item.item[self.config["index_field"]] = i
                new_item.item[self.config["target_field"]] = {
                    **json.loads(record.data)['result'],
                    "jobId": record.jobId,
                }
                await self.execute_children(new_item)

            total -= single_take
            skip += single_take
