import asyncio
import datetime
import time
from typing import Any, Callable, Dict, List

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler  # type: ignore
from prisma import Json
from prisma.enums import ScraperRunStatus
from prisma.models import Scraper as ScraperDao

from api.db import connect
from scraper.action import AppContext
from scraper.exception import ScraperAbort
from scraper.scraper import ScraperScraper
from scraper.types import QueueProcessItem, QueueProcessResultItem
from scraper.workers import MultiProcessor
from scraper.queue_parts import (ExecutionItem, QueueDao, QueueItem,
                                  ScraperEvents)
from scraper.info import ScraperInfo
from api.mail import send_mail


def get_first_two_letters_of_day():
    day_name = datetime.datetime.now().strftime('%A')
    return day_name[:2].upper()


ReportItem = int | Dict[str, Any]


def merge_dictionaries(dict1: Dict[str, ReportItem], dict2: Dict[str, ReportItem]):
    # Iterate over items in dict2 and merge into dict1
    for key, value in dict2.items():
        if key in dict1:
            # If the key exists in both, and both values are integers, sum them
            if isinstance(value, int) and isinstance(dict1[key], int):
                dict1[key] += value  # type: ignore
            # If the key exists in both, and both values are dictionaries, recursively merge
            elif isinstance(value, dict) and isinstance(dict1[key], dict):
                merge_dictionaries(dict1[key], value)  # type: ignore
            # If types are mixed or conflict, you may raise an error or handle as needed
            elif isinstance(value, list) and isinstance(dict1[key], list):
                dict1[key].extend(value)  # type: ignore
            else:
                raise ValueError(
                    f"Conflicting types for key '{key}': {type(dict1[key])} vs {type(value)}")
        else:
            # If the key is not in dict1, add it
            dict1[key] = value
    return dict1


scheduler = AsyncIOScheduler()


class ScraperQueue:
    # queue = []
    items: List[ExecutionItem] = []

    def __init__(self, num_workers: int | None = None):
        self.listeners: List[Callable[[ScraperEvents, Any], None]] = []
        self.app_context = AppContext()

        if (num_workers != 0):
            self.worker_manager = QueueProcessor(self, num_workers, False)

    def progress(self, progress_info: Any):
        self.fire(ScraperEvents.Progress, progress_info)

    def start(self):

        loop = asyncio.get_event_loop()
        loop.create_task(self.load_queue())

    def add_listener(self, listener: Callable[[ScraperEvents, Any], None]):
        self.listeners.append(listener)

    async def stop_scraper(self, run_id: int):
        for scraper in self.items:
            if scraper.run is not None and scraper.run.id == run_id:
                await scraper.model.stop()

    async def start_scraper(self, id: int, properties: Dict[str, Any], is_server: bool = True):
        prisma = await connect(True)
        try:
            scraper = await prisma.scraper.find_first(where={"id": id})

            if scraper is None:
                raise RuntimeError(f"Scraper with id {id} does not exist")

            print("🚀 Starting scraper: " + scraper.name)

            current_time = time.localtime()
            task = QueueItem({
                "minute": current_time.tm_min,
                "hour": current_time.tm_hour,
                "day": get_first_two_letters_of_day(),
                "properties": properties
            }, scraper)

            await self.start_task(task)

            return True
        except:
            await prisma.disconnect()

    async def start_task(self, task: QueueItem):

        item = ExecutionItem(
            task,
            "single",
            self.create_scraper(task.scraper),
            False
        )
        self.items.append(item)

        prisma = await connect()

        scraper_run = await prisma.scraperrun.create({
            "start": datetime.datetime.now(pytz.timezone("Australia/Sydney")),
            "scraperId": item.info.scraper.id,
            "status": ScraperRunStatus.Running,
            "message": "",
            "report": Json([]),
            "log": "",
            "succeeded": 0,
            "failed": 0,
            "skipped": 0,
            "day": item.info.day,
            "hour": item.info.hour,
            "minute": item.info.minute
        })

        item.run = scraper_run

        self.fire(ScraperEvents.Started, {
            "id": scraper_run.id,
            "scraperId": scraper_run.scraperId,
            "hour": scraper_run.hour,
            "minute": scraper_run.minute
        })

        try:
            await item.model.start(item, self.app_context)
        except ScraperAbort:
            await self.abort_task(item)
        except Exception as e:
            await self.error(item, f"Error starting scraper: {e.args[0]}")

    def create_scraper(self, scraper: ScraperDao) -> ScraperScraper:
        info = ScraperInfo(scraper.id, scraper.name, str(scraper.type))

        return ScraperScraper(self, info)

    def sender(self, item: ExecutionItem) -> Dict[str, Any]:
        return {
            "scraper": item.info.scraper.id,
            "run":  {
                "id": item.run.id,
                "status": item.run.status,
                "scraperId": item.run.scraperId,
                "succeeded": item.run.succeeded,
                "failed": item.run.failed,
                "skipped": item.run.skipped,
            } if item.run is not None else None,
        }

    async def abort_task(self, item: ExecutionItem):
        self.worker_manager.wait_for_slots_to_finish()

        await self.finish_task(item, ScraperRunStatus.Aborted)
        self.fire(ScraperEvents.Aborted, self.sender(item))

    async def error(self, item: ExecutionItem, error: str):
        await self.finish_task(item, ScraperRunStatus.Fail)
        self.fire(ScraperEvents.Error, self.sender(item))

    async def finish_task(self, item: ExecutionItem, status: ScraperRunStatus):

        if item.run is not None and item.sub_process == False:
            report = item.model.create_report()
            scraper_name = item.info.scraper.name

            mail_text = item.model.context.create_mail("")
            mail_subject: str = ""

            if status == ScraperRunStatus.Success:
                mail_subject = f"🚀 JobIQ '{scraper_name}' process finished"
            elif status == ScraperRunStatus.Aborted:
                mail_subject = f"☠️ JobIQ '{scraper_name}' process aborted"
            elif status == ScraperRunStatus.Fail:
                mail_subject = f"💩 JobIQ '{scraper_name}' process failed"
            else:
                mail_subject = f"🥶 JobIQ '{scraper_name}' process '{status}'"

            body = mail_text[0:2000] + \
                "..." if len(mail_text) > 2000 else mail_text
            attachment = mail_text if len(mail_text) > 2000 else None

            try:
                send_mail(mail_subject.replace(".", "_"), body,
                          "t.trescak@westernsydney.edu.au", attachment)
            except Exception as e:
                print("Error sending email")
                print(e)

            prisma = await connect()

            await prisma.scraperrun.update(
                where={
                    "id": item.run.id},
                data={
                    "status": status,
                    "log": item.model.log,
                    "report": Json(report) if report is not None else Json(None),
                    "skipped": item.model.skipped,
                    "existing": item.model.existing,
                    "succeeded": item.model.succeeded,
                    "failed": item.model.failed,
                    "finish": datetime.datetime.now(pytz.timezone("Australia/Sydney")),
                })

            if item in self.items:
                self.items.remove(item)

            print(f"Ω Process finished with: {status}")

            if status == ScraperRunStatus.Fail:
                self.fire(ScraperEvents.Error, self.sender(item))
            elif status == ScraperRunStatus.Aborted:
                self.fire(ScraperEvents.Aborted, self.sender(item))
            else:
                self.fire(ScraperEvents.Finished, self.sender(item))

        # if item.type == 'queue':
        #     self.item = await self.next_idle_queue_item(item.info)
        return True

    def fire(self, name: ScraperEvents, args: Any):
        for listener in self.listeners:
            listener(name, args)

    async def load_queue(self):
        prisma = await connect()

        # get all scrapers
        scrapers = await prisma.scraper.find_many()

        # remove all jobs
        scheduler.remove_all_jobs()

        # we can pause some scrappers
        available_scrapers = [x for x in scrapers if x.active]

        for scraper in available_scrapers:
            schedules: List[QueueDao] = scraper.schedule  # type: ignore
            for schedule in schedules:

                day = schedule["day"] if schedule["day"] != "" else "*"
                item = QueueItem(
                    {
                        **schedule,
                        "day": day
                    },
                    scraper
                )
                print(
                    f"Added job for {scraper.name} at {schedule['hour']}:{schedule['minute']} on {day}")
                scheduler.add_job(self.start_task,
                                  'cron',
                                  day=day,
                                  hour=schedule["hour"],
                                  minute=schedule["minute"],
                                  args=[item],
                                  name=f"{scraper.name}",
                                  misfire_grace_time=60 * 60 * 23
                                  )

        scheduler.start()


class QueueProcessor(MultiProcessor[QueueProcessItem, QueueProcessResultItem]):
    def __init__(self, queue: ScraperQueue, num_processes: int | None = None, auto_start_processes: bool | None = False):
        super().__init__(num_processes, auto_start_processes)
        self.queue = queue
        self.selenium = None

    def cleanup(self, context: AppContext) -> None:
        super().cleanup(context)

        context.cleanup()

    async def process_item(self, process: int, item: QueueProcessItem, context: AppContext) -> QueueProcessResultItem:
        queue = ScraperQueue(0)

        # if context is None:
        #     raise Exception("Context must be the Queue")

        if 'slot' not in item:
            raise Exception("There must be slot in the worker item")

        scraper_id: int = item["scraper_id"]
        run_id: int = item["run_id"]
        slot: int = item["slot"]

        item["item"]["slot_id"] = slot
        item["item"]["process_id"] = process

        prisma = await connect(True)

        try:
            scraper = await prisma.scraper.find_first(where={"id": scraper_id})
            run = await prisma.scraperrun.find_first(where={"id": run_id})

            if (scraper is None):
                raise Exception(f"Scraper with id {scraper_id} does not exist")
            if (run is None):
                raise Exception(f"Run with id {run_id} does not exist")

            current_time = time.localtime()

            queue_item: QueueItem = QueueItem({
                "minute": current_time.tm_min,
                "hour": current_time.tm_hour,
                "day": get_first_two_letters_of_day(),
                "properties": item["item"]
            }, scraper)

            execution_item = ExecutionItem(
                queue_item,
                "single",
                queue.create_scraper(queue_item.scraper),
                True
            )
            execution_item.run = run

            queue.items.append(execution_item)

            try:
                await execution_item.model.start(execution_item, context, config=item["config"])
            except ScraperAbort:
                await queue.error(execution_item, f"Aborted")
            except Exception as e:
                await queue.error(execution_item, f"Error starting scraper: {e.args[0]}")

            scraper_context = execution_item.model.context

            message = '\n'.join(scraper_context.info) if len(scraper_context.info) > 0 else (
                '\n'.join(scraper_context.warnings) if len(scraper_context.warnings) > 0 else (
                    '\n'.join(scraper_context.errors) if len(
                        scraper_context.errors) > 0 else ""
                )
            )

            result: QueueProcessResultItem = {
                "run_id": item["run_id"],
                "errors": scraper_context.errors,
                "skipped": scraper_context.skipped,
                "succeeded": scraper_context.succeeded,
                "existing": scraper_context.existing,
                "failed": scraper_context.failed,
                "info": scraper_context.info,
                "log": scraper_context.log,
                "warnings": scraper_context.warnings,
                "reports": scraper_context.reports,
                "message": message,
                "slot": slot
            }

            return result
        finally:
            if prisma.is_connected():
                await prisma.disconnect()

    def process_result(self, result: QueueProcessResultItem) -> None:

        execution_item = next(
            (x for x in self.queue.items if x.run is not None and x.run.id == result["run_id"]), None)

        if execution_item is None:
            raise RuntimeError(
                f"Process with run id {result['run_id']} does not exist")

        queue_context = execution_item.model.context

        # if 'exception' in result:
        #     queue_context.errors.append(result["exception"])
        #     queue_context.failed += 1

        #     raise ScraperException('abort', result["exception"])

        queue_context.succeeded += result["succeeded"]
        queue_context.failed += result["failed"]
        queue_context.existing += result["existing"]
        queue_context.skipped += result["skipped"]
        queue_context.errors += result["errors"]
        queue_context.warnings += result["warnings"]
        queue_context.info += result["info"]
        queue_context.reports = merge_dictionaries(
            queue_context.reports, result["reports"]
        )

        # queue_context.log_progress(result["message"], 1)

        # if (result["failed"] > 0):
        #     raise ScraperException('abort', '\n'.join(result["errors"]))
