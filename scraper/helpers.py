import datetime
import json
import re
import unicodedata
from os import mkdir
from os.path import exists
from typing import Any, Dict, Literal, cast

import dateutil.parser
import pytz
import requests
from bs4 import BeautifulSoup, Tag
from typing_extensions import NotRequired, TypedDict

from scraper.exception import ScraperException
from html_to_markdown import convert_to_markdown
import time
import random


def perfect_string(text: str):
    text = re.sub(r'(?<!\.)</li>', '.', text)
    text = BeautifulSoup(text, "lxml").text
    text = unicodedata.normalize("NFKD", text)
    text = text.replace(".", ". ")
    text = text.strip()
    return text


def current_date():
    return datetime.datetime.now(pytz.timezone("Australia/Sydney"))


def fetch_graphql(url: str, query: str, variables: Any):
    # store the response of URL
    # response = requests.post(url, json={"query": query})

    headers = {
        'User-Agent': linux_useragent,
        'Content-Type': 'application/json',
        # 'Authorization': 'Bearer YOUR_AUTH_TOKEN'  # if you have authentication; otherwise, remove this line
    }

    payload = {
        'query': query,
        'variables': variables
    }

    response = requests.post(url, headers=headers, json=payload)

    # storing the JSON response
    # from url in data
    data_json = response.json()

    return data_json


def fetch_json(url: str):
    retries = 0

    while retries < 5:
        try:
            # store the response of URL
            response = requests.get(url)

            # storing the JSON response
            # from url in data
            data_json = response.json()

            return data_json
        except Exception as e:
            print(f"❌  Error fetching JSON from {url}: {e}, retrying... ({retries + 1}/5)")
            retries += 1
            if retries >= 5:
                raise ScraperException(
                  "error", f"Failed to fetch JSON from {url} after multiple attempts")
            time.sleep(random.uniform(3, 60))



def post_json(url: str, body: Any):
    # store the response of URL
    response = requests.post(url, json=body)

    # storing the JSON response
    # from url in data
    data_json = response.json()

    return data_json


def fetch_page(page: int):
    # store the response of URL
    return fetch_json(
        f"https://www.workforceaustralia.gov.au/api/v1/global/vacancies/?pageNumber={page}&sort=DateAddedDescending"
    )


def fetch_details(id: int):
    return fetch_json(f"https://www.workforceaustralia.gov.au/api/v1/global/vacancies/{str(id)}")


def parse_relative_date(relative_date_str: str) -> datetime.datetime:
    """
    Parse a relative date string such as '1d ago' or '1h ago' and return the corresponding datetime object.

    :param relative_date_str: A string representing the relative date (e.g., '1d ago', '2h ago').
    :return: A datetime object representing the time calculated from the relative date.
    """
    # Regular expression to match the pattern
    pattern = re.compile(r'(\d+)([dhm]) ago')
    match = pattern.match(relative_date_str)

    if not match:
        raise ValueError(
            "Invalid format. Please use the format like '1d ago', '2h ago', etc.")

    # Extract the quantity and the time unit (days, hours, minutes)
    quantity, unit = match.groups()
    quantity = int(quantity)

    # Calculate the time difference
    if unit == 'd':   # Days
        return datetime.datetime.now() - datetime.timedelta(days=quantity)
    elif unit == 'h':  # Hours
        return datetime.datetime.now() - datetime.timedelta(hours=quantity)
    elif unit == 'm':  # Minutes
        return datetime.datetime.now() - datetime.timedelta(minutes=quantity)

    raise ValueError("Invalid time unit. Please use 'd', 'h', or 'm'.")


linux_useragent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36"


class RegexConfig(TypedDict):
    match: NotRequired[str]
    search: str
    group: NotRequired[int]
    index: NotRequired[int]
    replace: NotRequired[str]


class OptionalOptions(TypedDict):
    fallback: NotRequired[str]
    value: NotRequired[Any]


class ExtractorConfig(TypedDict):
    type: NotRequired[Literal["text"] | Literal["normalised_text"] | Literal["markdown"]]
    attribute: NotRequired[str]
    regex: NotRequired[RegexConfig]
    group: NotRequired[int]
    translate: NotRequired[str]
    optional: NotRequired[bool | OptionalOptions]
    convert: str | Dict[str, Any]
    validate: NotRequired[Dict[str, Any]]


def find_parent(path: str, root: Any) -> Any:
    # split the path
    # for each part of the path
    #   if it is a list
    #       return that element
    #   else
    #       if the item has a key
    #           if the key matches the path
    #               return the item
    optional = path.startswith("?")
    if optional:
        path = path[1:]

    parts = path.split(".")
    parent = root
    for part in parts:
        if isinstance(parent, list):
            parent = parent[int(part)]
        else:
            if isinstance(parent, dict):
                if part in parent:
                    parent = parent[part]
                elif optional:
                    return None
                else:
                    raise ScraperException(
                        "error", f"Could not find {part} in {parent}")
            elif parent is None:
                if optional:
                    return None
                else:
                    raise ScraperException(
                        "error", f"Could not find {part} in {parent}")
            else:
                raise ScraperException(
                    "error", f"Expected dictionary {part} in {parent}")
    return parent


def extract_text(original_text: Any | None, extractor: ExtractorConfig, item: Dict[str, Any]):
    value = __process_text(original_text, extractor)

    if value is None:
        # by default everything is optional and returns none in that case
        if "optional" in extractor:
            fallback_options = extractor["optional"]
            if fallback_options == False:
                raise ScraperException(
                    'error',
                    f"Extraction failed in '{original_text}' for {str(extractor)}")
            else:
                if fallback_options == True:
                    return None
                elif "fallback" in fallback_options:
                    return find_parent(fallback_options["fallback"], item)
                elif "value" in fallback_options:
                    return fallback_options["value"]
                else:
                    raise ScraperException(
                        'fatal',
                        f"No fallback options provided for {str(extractor)}")

    return value


def __process_text(text: Any | None, extractor: ExtractorConfig) -> Any:

    if text is None:
        return None

    # process regex
    if "regex" in extractor:
        regex_options = extractor["regex"]

        # we can first check if the regex matches
        if "match" in regex_options:
            reg = re.compile(regex_options["match"])
            if reg.search(text) is None:
                return None

        reg = re.compile(regex_options["search"])

        # we can search for multiple items
        if "index" in regex_options and regex_options["index"] != 0:
            results = [x for x in reg.finditer(text)]

            if regex_options["index"] < len(results):
                result = results[regex_options["index"]]
            else:
                return None
        else:
            result = reg.search(text)

        # get the group number
        group_number = int(
            regex_options["group"]) if "group" in regex_options else 1

        # in case we did not find the match
        if result is None or (len(result.groups())) < group_number:
            return None
        else:
            text = result.group(group_number)

    if text is None:
        return None

    # process translation
    # if "translate" in extractor:
    #     text = Translator.instance().translate(text, {
    #         "source_language": extractor["translate"]
    #     })

    # process function conversion
    if "convert" in extractor:
        if isinstance(extractor["convert"], dict):
            converter = extractor["convert"]

            if converter["type"] == "string_to_json":
                try:
                    text = json.loads(text)
                except:
                    if "default" in converter:
                        if converter["default"] == "None":
                            return None
                        return converter["default"]
            else:
                raise Exception("Invalid converter")

        else:
            try:
                if extractor["convert"] == "html_to_text":
                    soup = BeautifulSoup(text, "html.parser")
                    text = soup.get_text()
                elif extractor["convert"] == "relative_date_to_date":
                    return parse_relative_date(text)
                elif extractor["convert"] == "iso_string_to_date":
                    return dateutil.parser.isoparse(text)
                elif extractor["convert"] == "int":
                    return int(text.replace(',', ''))
                else:
                    raise Exception("Invalid converter")
            except:
                raise ScraperException(
                    "error", f"Could not convert {text} to {extractor['convert']}")

    if text is None:
        return None

    # process type conversions
    if "split" in extractor:
        split = str.split(
            text, extractor["split"]["with"] if "with" in extractor["split"] else " ")
        if extractor["split"]["index"] < len(split):
            text = split[extractor["split"]["index"]]

    if "string_join" in extractor:
        separator: str = extractor["string_join"]
        # separator = separator.replace("$line", "\n")
        text = separator.join(text)

    if "validate" in extractor:
        if any(x not in text for x in extractor["validate"].keys()):
            return None
        return text

    return text


def fetch_url(url: str):
    # store the response of URL
    headers = {
        'User-Agent': linux_useragent}

    response = requests.get(url, headers=headers)

    # storing the JSON response
    # from url in data
    return response.text


class Souped:
    def __init__(self, element: Tag | Any | None, selector: str | None = None):
        if element is None:
            raise RuntimeError(f"Could not find element at {selector}")
        if not isinstance(element, Tag):
            raise RuntimeError(f"Expected tag at {selector}")
        self.element: Tag = element

    def extract_field(self, extractor: ExtractorConfig | None, item: Dict[str, Any]):
        if extractor is not None:
            # take the raw value
            if "attribute" in extractor:
                text = self.attrs[extractor["attribute"]]
            elif "type" in extractor and extractor["type"] == "text":
                text = self.text
            elif "type" in extractor and extractor["type"] == "markdown":
                text = perfect_string(convert_to_markdown(self.element)) # type: ignore
                text = text.replace("\\", "")
            elif "type" in extractor and extractor["type"] == "normalised_text":
                text = str(self.element.contents[0])
                text = perfect_string(text)
            else:
                raise Exception("Invalid extractor type")

            # extract the text
            return extract_text(text, extractor, item)

        else:
            return self

    def select_one(self, selector: str):
        return Souped(self.element.select_one(selector), selector)

    def select_one_optional(self, selector: str):
        element = self.element.select_one(selector)
        if element is not None:
            return Souped(element, selector)
        return None

    def select_text(self, selector: str, default_text: str):
        item = self.element.select_one(selector)
        if item is None:
            return default_text
        return item.text

    def select(self, selector: str):
        return [Souped(x, selector) for x in self.element.select(selector)]

    def find(self, selector: Any, string: str | None = None):
        if string is not None:
            return Souped(self.element.find(selector, string=string))
        return Souped(self.element.find(selector), selector)

    def find_optional(self, selector: Any, string: str | None = None, partial: bool | None = None):
        if string is not None:
            if partial is not None and partial == True:
                element = self.element.find(
                    selector, string=lambda s: string in s if s else False)
            else:
                element = self.element.find(selector, string=string)
        else:
            element = self.element.find(selector)

        if element is not None:
            return Souped(element, selector)
        return None

    def get(self, selector: str):
        return self.element.get(selector)

    @property
    def next_sibling(self):
        return Souped(cast(Any, self.element.next_sibling))

    @property
    def parent(self):
        return Souped(cast(Any, self.element.parent))

    @property
    def number(self):
        match = re.search(r'(\d+)', self.element.text)
        if match:
            number = int(match.group(1))
            return number
        else:
            raise RuntimeError("Expected number in " + self.element.text)

    @property
    def tag(self):
        return self.element

    @property
    def text(self):
        return self.element.text

    @property
    def contents(self):
        return [Souped(x) for x in self.element.contents if isinstance(x, Tag)]

    @property
    def attrs(self):
        return self.element.attrs


def fetch_soup(url: str):
    data = fetch_url(url)
    return Souped(BeautifulSoup(data, "html.parser"))


def parse_json(text: str):
    try:
        json_object = json.loads(text)
    except ValueError:
        return None
    return json_object


def log_error(code: str, id: int, text: str):
    dir = f"./data/errors"
    if not exists(dir):
        mkdir(dir)

    dir = f"./data/errors/{code}"
    if not exists(dir):
        mkdir(dir)

    with open(f"{dir}/{id}.txt", "w") as file:
        file.write(text)


def sg(obj: Any, path: str):
    parts = path.split(".")

    try:
        for part in parts:
            if part in obj:
                obj = obj[part]
            else:
                return None
        return obj
    except:
        return None


def outer(x: int):
    def inner():
        print("x is", x)
    return inner


def finder(obj: Any):
    def find(path: str):
        parts = path.split(".")
        inner = obj

        try:
            for part in parts:
                inner = inner[part]
            return inner
        except:
            return None
    return find
