from __future__ import annotations

import asyncio
import datetime
from enum import Enum
from typing import Any, Dict, List, Union
from api import db

from fastapi import FastAPI, WebSocket, BackgroundTasks
from prisma.models import ScraperRun
from prisma import Json
from prisma.enums import ScraperType
from pydantic import BaseModel

from scraper.queue import ScraperQueue, scheduler
from scraper.queue_parts import QueueDao, ScraperEvents

import uvicorn
import os
import json

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting event queue")
    asyncio.create_task(notification_task())
    print("Starting FASTAPI server")
    manager_context.queue.start()
    yield

app = FastAPI(lifespan=lifespan)
active_connections: List[WebSocket] = []

event_data = {}
event = asyncio.Event()

async def notification_task():
    while True:
        await event.wait()

        # Process the data after the event is set
        data = event_data.get("data")
        event_info = event_data.get("event")

        if data is None or event_info is None:
            return

        await asyncNotify(event_info, data) 

        # Clear the event for future use
        event.clear()

def notify(e: ScraperEvents, data: Any):
    event_data["data"] = data
    event_data["event"] = e
    event.set()  # Trigger the event

uid = 0

class ManagerContext:
    def __init__(self):
        global uid
        uid = uid + 1
        self.id = uid
        self._queue: ScraperQueue | None = None

    @property 
    def queue(self):
        if self._queue is None:
            self._queue = ScraperQueue(int(os.getenv('MANAGER_PROCESSES') or 4))
            self._queue.add_listener(notify)
        return self._queue

manager_context = ManagerContext()


class RunInfo(BaseModel):
    id: int
    scraper_id: int
    start: datetime.datetime
    finish: Union[datetime.datetime, None]
    status: str
    message: str
    succeeded: int
    failed:  int
    skipped:  int

    def serialise(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "scraperId": self.scraper_id,
            "start": self.start,
            "finish": self.finish,
            "status": self.status,
            "message": self.message,
            "succeeded": self.succeeded,
            "failed": self.failed,
            "skipped": self.skipped
        }


class QueueItem(BaseModel):
    scraper_id: int
    run: Union[RunInfo, None]
    minute: int
    hour: int
    day: int
    properties: Dict[str, Any]

    def serialise(self) -> Dict[str, Any]:
        return {
            "scraperId": self.scraper_id,
            "run": self.run.serialise() if self.run is not None else None,
            "minute": self.minute,
            "hour": self.hour,
            "day": self.day
        }


class QueuedInfo(BaseModel):
    name: str
    run: Union[datetime.datetime, None]


async def asyncNotify(event: ScraperEvents, data: Any):
    for connection in active_connections:
        try:
            await connection.send_json({
                "event": event.value,
                "data": data
            })

        except:
            print("Removing closed connection ...")
            active_connections.remove(connection)


def create_run_info(run: Union[ScraperRun, None]):
    if run is None:
        return None

    return RunInfo(
        id=run.id,
        scraper_id=run.scraperId,
        start=run.start,
        finish=run.finish,
        status=str(run.status),
        message=run.message,
        succeeded=run.succeeded,
        failed=run.failed,
        skipped=run.skipped
    )

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    if websocket not in active_connections:
        active_connections.append(websocket)

    connected = True
    while connected:
        try:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message text was: {data}")
        except:
            print("Connection closed") 
            connected = False

def sync_start_scraper(id: int, pages: Dict[str, Any]):
    asyncio.run(manager_context.queue.start_scraper(id, pages))

@app.post("/scraper/start/{id}")
async def start_scraper(background_tasks: BackgroundTasks, id: int, pages: Dict[str, Any]) -> None:
    background_tasks.add_task(sync_start_scraper, id, pages)

class ScraperInput(BaseModel):
    id: int
    name: str
    schedule: List[ScraperSchedule]
    type: ScraperType
    logo: str
    url: str
    content: str

@app.post("/scraper/update")
async def update_scraper(info: ScraperInput) -> bool:
    prisma = await db.connect(True)
    await prisma.scraper.update(
        where={"id": info.id},
        data={
            "name": info.name,
            "source": info.content,
            "logo": info.logo,
            "url": info.url,
            "source": info.content,
            "schedule": Json([
                {
                    "minute": s.minute,
                    "hour": s.hour,
                    "day": s.day,
                    "properties": json.loads(s.properties) if s.properties else {}
                } for s in info.schedule
            ] if info.schedule else []),
        }
    )
    return True

@app.post("/scraper/create")
async def create_scraper(info: ScraperInput) -> None:
    prisma = await db.connect(True)
    await prisma.scraper.create(

        data={
            "name": info.name,
            "source": info.content,
            "logo": info.logo,
            "url": info.url,
            "source": info.content,
            "type": info.type,
            "schedule": Json([
                {
                    "minute": s.minute,
                    "hour": s.hour,
                    "day": s.day,
                    "properties": json.loads(s.properties) if s.properties else {}
                } for s in info.schedule
            ] if info.schedule else []),
        }
    )
    await asyncNotify(ScraperEvents.Idle, {"message": "Scraper updated successfully"})

@app.get("/message/{text}")
async def message(text: str) -> None:
    await asyncNotify(ScraperEvents.Idle, {"hello": "world "})


@app.get("/scraper/stop/{runId}")
async def stop_scraper(runId: int) -> None:
    await manager_context.queue.stop_scraper(runId)


@app.get("/scraper/{runId}/report")
async def running_report(runId: int):
    item = next(
        x for x in manager_context.queue.items if x.run is not None and x.run.id == runId)
    return item.model.create_report()


@app.get("/scraper/{runId}/log")
async def running_log(runId: int) -> str:
    item = next(
        x for x in manager_context.queue.items if x.run is not None and x.run.id == runId)
    return item.model.log

class ScraperSchedule(BaseModel):
    minute: int
    hour: int
    day: str  
    properties: str

class ScraperListInfo(BaseModel):
    id: int
    name: str
    schedule: List[ScraperSchedule]

@app.get("/scraper/list", response_model=List[ScraperListInfo])
async def scraper_list() -> List[ScraperListInfo]:
    prisma = await db.connect(True)
    scrapers = await prisma.scraper.find_many()
    items: List[ScraperListInfo] = []
    for item in scrapers:
        schedule: List[QueueDao] = item.schedule # type: ignore
        items.append(
            ScraperListInfo(
                id=item.id,
                name=item.name,
                schedule=[
                    ScraperSchedule(
                        minute=s["minute"],
                        hour=s["hour"],
                        day=s["day"],
                        properties=json.dumps(s["properties"] if "properties" in s else {})
                    ) for s in schedule
                ] if schedule else []
            )
        )
    return items

class ScraperTypeEnum(str, Enum):
    Job = 'Job'
    Content = 'Content'
    MicroCredentials = 'MicroCredentials'
    Process = 'Process'

class ScraperInfo(BaseModel):
    id: int
    name: str
    schedule: List[ScraperSchedule]
    type: ScraperType
    logo: str
    url: str
    content: str

@app.get("/scraper/detail/{id}", response_model=ScraperInfo | None)
async def scraper_detail(id: str) -> ScraperInfo | None:
    prisma = await db.connect(True)
    scraper = await prisma.scraper.find_first(
        where={"id": int(id)},
    )
    schedule: List[QueueDao] = scraper.schedule #type: ignore

    return ScraperInfo(
        id=scraper.id,
        name=scraper.name,
        type=scraper.type,
        schedule=[
            ScraperSchedule(
                minute=s["minute"],
                hour=s["hour"],
                day=s["day"],
                properties=json.dumps(s["properties"] if "properties" in s else {})
            ) for s in schedule
        ] if schedule else [],
        logo=scraper.logo if scraper.logo else "",
        url=scraper.url if scraper.url else "",
        content=scraper.source
    ) if scraper else None

@app.get("/scraper/content/{id}", response_model=str | None)
async def scraper_content(id: str) -> str | None:
    prisma = await db.connect(True)
    scraper = await prisma.scraper.find_first(
        where={"id": int(id)},
    )
    return scraper.source if scraper else None

@app.get("/scraper/queue", response_model=List[QueuedInfo])
async def scraper_queue() -> List[QueuedInfo]:
    result = []
    jobs = scheduler.get_jobs()
    print("Scheduled Jobs:")
    for job in jobs:
        result.append(
            QueuedInfo(
                name=job.name,
                run=job.next_run_time
            )
        )
    return result

@app.get("/")
async def root():
    return {"name": "JobIQ Data Manager Backend", "version": "1.0.0"}

if __name__ == '__main__':
    port = os.getenv('MANAGER_PORT')
    if port is None:
        raise Exception("You must specify the port")
    
    reload = os.getenv('MANAGER_RELOAD') == 'True'

    # Use uvicorn to run the app. Here we specify the host and port, and
    # specify that the app is located in the current file (main.py) with
    # the instance name 'app'.
    uvicorn.run(app="main:app", host="127.0.0.1", port=int(port), reload=reload)
