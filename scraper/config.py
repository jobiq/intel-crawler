from __future__ import annotations

import re
from typing import Any, Dict, List

from typing_extensions import NotRequired, TypedDict


class ScraperActionConfig(TypedDict):
    name: str
    boundary: NotRequired[bool]
    CHILDREN: NotRequired[List[ScraperActionConfig]]


class ScraperConfig(TypedDict):
    # properties: List[ScraperProperty]
    actions: List[ScraperActionConfig]
    properties: NotRequired[Dict[str, Any]]


def get_id_from_name(name: str) -> str:
    match = re.search(r"\((.*?)\)", name)
    if match is None:
        raise Exception(f"Expected (id) in action name: {name}")
    # the id is specified in between parenthesis ()
    return match.group(1)  # type: ignore
