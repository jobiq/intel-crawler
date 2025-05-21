from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scraper.scraper import ScraperScraper

from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, Literal, TypedDict, Union

from prisma.models import Scraper, ScraperRun

days = {
    "MO": "0",
    "TU": "1",
    "WE": "2",
    "TH": "3",
    "FR": "4",
    "SA": "5",
    "SU": "6"
}


def get_week_start_and_end(day: datetime):
    # set day to midnight
    input_date = day.replace(hour=0, minute=0, second=0, microsecond=0)

    # Calculate the day of the week (0 = Monday, 6 = Sunday)
    day_of_week = input_date.weekday()

    # Calculate the start of the week (Monday)
    start_of_week = input_date - timedelta(days=day_of_week)

    # Calculate the end of the week (Sunday)
    end_of_week = start_of_week + \
        timedelta(days=6-day_of_week, hours=23, minutes=59, seconds=59)

    # Format the results as strings
    print(start_of_week.strftime("%Y-%m-%d %H:%M:%S"))
    print(end_of_week.strftime("%Y-%m-%d %H:%M:%S"))

    return start_of_week, end_of_week


class ScraperEvents(Enum):
    Started = "started"
    Finished = "finished"
    Idle = "idle"
    Error = "error"
    Progress = "progress"
    Aborted = "abort"


class QueueDao(TypedDict):
    minute: int
    hour: int
    day: str
    properties: Dict[str, None]


class QueueItem:
    scraper: Scraper
    minute: int
    hour: int
    day: str
    # skill_frameworks: List[str]
    # role_frameworks: List[str]
    properties: Dict[str, Any]

    def __init__(self, item: QueueDao, scraper: Scraper):
        self.scraper = scraper
        self.minute = item["minute"]
        self.hour = item["hour"]
        self.day = "*" if item["day"] == "*" else days[item["day"]]
        self.properties = item["properties"] if "properties" in item else {}

    def serialise(self) -> Dict[str, Any]:
        return {
            "scraper_id": self.scraper.id,
            "minute": self.minute,
            "hour": self.hour,
            "day": self.day,
            "properties": self.properties
        }


ExecutionType = Literal["queue", "single"]

class ExecutionItem:

    def __init__(self, item: QueueItem, type: ExecutionType, model: ScraperScraper, sub_process: bool):
        self.info = item
        self.model = model
        self.type = type
        self.run: Union[ScraperRun, None] = None
        self.sub_process = sub_process


class Notifier:
    pass
