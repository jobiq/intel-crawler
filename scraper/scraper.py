from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:

    from scraper.info import ScraperInfo
    from scraper.action import AppContext
    from scraper.config import ScraperConfig

import yaml
from prisma.enums import ScraperRunStatus

from scraper.action import ScraperContext, ScraperItem
from scraper.exception import ScraperAbort, ScraperException
from scraper.repository import repository
from scraper.wrapper_action import WrapperAction
from scraper.queue_parts import ExecutionItem


class ScraperScraper():
    def __init__(self, queue: Any, item: ScraperInfo):
        self.scraper = item
        self.queue = queue

        self.context = ScraperContext(
            self.queue,
            self.scraper,
            None,
        )

    @property
    def log(self):
        return self.context.info_text

    @property
    def succeeded(self):
        return self.context.succeeded

    @property
    def failed(self):
        return self.context.failed

    @property
    def existing(self):
        return self.context.existing

    @property
    def skipped(self):
        return self.context.skipped

    @property
    def running(self):
        return self.context.running

    async def start(self, item: ExecutionItem, app: AppContext, config: ScraperConfig | None = None):

        # load the spec
        if config is None:
            self.config: ScraperConfig = yaml.safe_load(item.info.scraper.source)
        else:
            self.config = config

        # init context
        self.context = ScraperContext(
            self.queue,
            self.scraper,
            item.run.id if item.run is not None else None,
        )

        scraper = ScraperItem(self.context, app, item.info.properties)
        wrapper = WrapperAction(
            self.config,
            self.config["properties"] if "properties" in self.config else {
            }, repository.actions
        )

        try:
            await wrapper.init()
            await wrapper.execute(scraper)

            if len(self.context.errors) > 0:
                await self.queue.finish_task(item, ScraperRunStatus.Fail)
            else:
                await self.queue.finish_task(item, ScraperRunStatus.Success)
        except ScraperException as e:
            if 'slot_id' not in scraper.item:
                print(e)
                print("No boundary caught this error")
                await self.queue.finish_task(item, ScraperRunStatus.Fail)
            else:
                # self.queue.result_queue.put({
                #     "slot": scraper.item['slot_id'],
                #     "message": str(e),
                #     "exception": str(e)
                # }) #type: ignore
                print('Sub-process failed')
        except ScraperAbort as e:
            await self.queue.abort_task(item)
        except Exception as e:
            self.context.errors.append("UNEXPECTED: " + str(e))
            await self.queue.finish_task(item, ScraperRunStatus.Fail)

    async def stop(self) -> None:
        self.context.running = False

    def create_report(self) -> Any | None:
        return self.context.reports

    # def create_mail(self) -> str | None:
    #     return f"""
    #     <>Hello Master
    #     <br />
    #     I have finished processing scraper: <i>{self.scraper.name}</i><br />
    #     <br />
    #     {self.context.info_text}
    #     <br />
    #     {self.context.mail}
    #     <br />
    #     <br />
    #     🧠 JobIQ Manager
    #     """
    #     return
