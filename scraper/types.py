from typing import Any, Dict, List, TypedDict
from typing_extensions import NotRequired

from scraper.config import ScraperConfig

class QueueProcessItemBase(TypedDict):
    slot: NotRequired[int]

class QueueProcessItem(QueueProcessItemBase):

    item: Dict[str, Any]
    scraper_id: int
    run_id: int
    config: ScraperConfig

class QueueProcessResultItemBase(TypedDict):
    slot: int
    message: str
    exception: NotRequired[str]

class QueueProcessResultItem(QueueProcessResultItemBase):
    run_id: int
    succeeded: int
    failed: int
    existing: int
    skipped: int
    errors: List[str]
    warnings: List[str]
    info: List[str]
    reports: Dict[str, Any]
    log: str
