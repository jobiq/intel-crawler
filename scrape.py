import asyncio
import getopt
import json
import sys
from typing import Any, Dict, List

from scraper.queue import ScraperQueue

DEFAULT_START = "{}"


async def do_the_job(properties: Dict[str, Any], queue: ScraperQueue, scrapers: List[int]):
    for scraper in scrapers:
        await queue.start_scraper(scraper, properties, False)


def main(argv: Any):
    properties = DEFAULT_START
    scrapers = []

    queue = ScraperQueue(num_workers=1)
  
    try:
        opts, _ = getopt.getopt(
            argv, "hp:s:", ["pages=", "scrapers="])
    except getopt.GetoptError:
        print("python pipelines -p <properties> -s <scraper_ids>")
        sys.exit(2)
    for opt, arg in opts:
        if opt == "-h":
            print(
                "python pipelines -p <properties> -s <scraper_ids>")
            sys.exit()
        elif opt in ("-p", "--properties"):
            properties = arg
        elif opt in ("-s", "--scrapers"):
            scraper_ids = arg.split(",")
            # queue.add_listener(lambda x, y: print(
            #     f"{x.value}: {y['message'] if 'message' in y else ''}"))

            scrapers = [int(x) for x in scraper_ids]

    asyncio.run(do_the_job(json.loads(properties), queue, scrapers))
    queue.worker_manager.stop()


if __name__ == "__main__":
    # torch.multiprocessing.set_start_method('spawn')  # good solution !!!!
    main(sys.argv[1:])
