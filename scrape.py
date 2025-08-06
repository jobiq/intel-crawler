import asyncio
import getopt 
import json
import sys
from typing import Any, Dict, List

from scraper.queue import ScraperQueue
import os

from dotenv import load_dotenv
load_dotenv()

DEFAULT_START = "{}"


async def do_the_job(properties: Dict[str, Any], queue: ScraperQueue, scrapers: List[int]):
    for scraper in scrapers:
        await queue.start_scraper(scraper, properties, False)


help = "python -m scrape --pages <pages> --props <properties> --workers <worker_count> --start <start_index> -s <scraper_ids>"

def main(argv: Any):
    properties = DEFAULT_START
    workers = 1
    scrapers = []
  
    try:
        opts, _ = getopt.getopt(
            argv, "hp:s:p:w:t", ["pages=", "scrapers=", "workers=", "start="])
    except getopt.GetoptError:
        print(help)
        sys.exit(2)

    parameters = {}

    for opt, arg in opts:
        if opt == "-h":
            print(help)
            sys.exit()
        elif opt in ("-p", "--properties"):
            parsed = json.loads(arg)
            parameters = {
                **parameters,
                **parsed
            }
        elif opt in ("-w", "--workers"):
            workers = int(arg)
            if workers < 1:
                print("Number of workers must be at least 1.")
                sys.exit(2)
        elif opt in ("-g", "--pages"):
            parameters["pages"] = int(arg)
        elif opt in ("-t", "--start"):
            print("Setting start index to", arg)
            parameters["start_index"] = int(arg)
            if parameters["start_index"] < 0:
                print("Start index must be a positive integer.")
                sys.exit(2)
        elif opt in ("-s", "--scrapers"):
            scraper_ids = arg.split(",")
            # queue.add_listener(lambda x, y: print(
            #     f"{x.value}: {y['message'] if 'message' in y else ''}"))

            scrapers = [int(x) for x in scraper_ids]

    properties = json.dumps(parameters)
    print(properties)

    queue = ScraperQueue(num_workers=workers)

    asyncio.run(do_the_job(json.loads(properties), queue, scrapers))
    queue.worker_manager.stop()


if __name__ == "__main__":
    # torch.multiprocessing.set_start_method('spawn')  # good solution !!!!
    main(sys.argv[1:])
