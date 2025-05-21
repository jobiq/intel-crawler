from typing import Literal


class ScraperException(Exception):
    def __init__(self, severity: Literal['fatal', 'error', 'warning', 'info', 'abort'], message: str):
        self.severity = severity
        # self.scraper = scraper
        self.message = message

        super().__init__(self.message)


class ScraperAbort(Exception):
    def __init__(self) -> None:
        super().__init__("Process Aborted")
