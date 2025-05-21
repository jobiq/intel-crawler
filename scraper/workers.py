import asyncio
import multiprocessing as mp
from typing import List
from scraper.action import AppContext

from scraper.types import (
    QueueProcessItemBase, QueueProcessResultItemBase,)

from typing import TypeVar, Generic

from libs.progress import ProgressBar

T = TypeVar('T', bound=QueueProcessItemBase)
U = TypeVar('U', bound=QueueProcessResultItemBase)
V = TypeVar('V')

class MultiProcessor(Generic[T, U]):
    def start_workers(self, num_workers: int | None = None):
        for _ in range(num_workers if num_workers is not None else self.num_processes):
            process = mp.Process(
                target=self.worker_task, args=(self.running_slots, self.task_queue, self.result_queue)
            )
            self.running_slots += 1
            # self.processes.append(process)
            process.start()

    def __init__(self, num_processes: int | None = None, auto_start_processes: bool | None = False):
        cpu_count = mp.cpu_count()
        
        self.num_processes = num_processes if num_processes is not None else cpu_count if cpu_count < 24 else 24
        self.slots = [0 for _ in range(self.num_processes)]
        self.running_slots = 0

        self.task_queue: 'mp.Queue[T | None]' = mp.Queue()
        self.result_queue: 'mp.Queue[U]' = mp.Queue()

        if auto_start_processes:
            self.start_workers(self.num_processes)
    
    def worker_task(
        self,
        i: int,
        task_queue: 'mp.Queue[T | None]',
        result_queue: 'mp.Queue[U]'
    ):
        print(f"🚀 Starting Worker Task {i}")

        app_context = AppContext()

        while True:
            task = task_queue.get()

            if task is None:
                # clean up the resources
                self.cleanup(app_context)
                
                # None is the signal to stop.
                print(f"☠️  {i} This is the end, my only friend the end!")
                break

            # run this task
            item = asyncio.run(self.process_item(i, task, app_context))
            # notify about the result
            result_queue.put(item)
            

    async def process_item(self, process: int, item: T, context: AppContext) -> U:
        raise Exception("Not implemented")
    
    def _process_result(self, result: U) -> None:
        self.slots[result["slot"]] = 0
        self.process_result(result)

    def process_result(self, result: U) -> None:
        pass

    def cleanup(self, context: AppContext) -> None:
        pass
    
    def with_slot(self, item: QueueProcessItemBase, message: str) -> QueueProcessResultItemBase:
        if 'slot' not in item:
            raise RuntimeError('Task must contain a slot')
        
        return {
            "slot": item["slot"],
            "message": message
        }
    
    def find_free_slot(self):
        for i in range(len(self.slots)):
            if self.slots[i] == 0:
                return i
        return -1  # Return -1 or any other indicator if 0 is not found
    
    def has_running_slots(self):
        for slot in self.slots:
            if slot == 1:
                return True
        return False
    
    def schedule(self, item: T, progress: ProgressBar | None = None, max_processes: int | None = None):

        # we launch a new process for each item as long as we have them
        if self.running_slots < self.num_processes and (max_processes is None or self.running_slots < max_processes):
            process = mp.Process(
                target=self.worker_task, args=(self.running_slots, self.task_queue, self.result_queue)
            )
            self.running_slots += 1
            # self.processes.append(process)
            process.start()

        # first we try to find a free slot
        index = self.find_free_slot()

        # we do not allow to run more than what is required
        if max_processes is not None and sum(self.slots) >= max_processes:
            index = -1

        if index == -1:
            # print("No slot available, waiting...")
            result = self.result_queue.get()
            self._process_result(result)

            if progress is not None:
                progress.step(result['message'])
            
            # slot freed, put it there
            index = result["slot"]
            self.slots[index] = 1
            # print("Slot freed, starting process")
            
            item["slot"] = index
            self.task_queue.put(item)
        else:
            self.slots[index] = 1
            # print("Slot available, starting process")
            item["slot"] = index
            self.task_queue.put(item)

    def process_items(self, items: List[T]):
        progress = ProgressBar(new_line=True)
        job_count = len(items)

        progress.start_sequence(job_count, f"🚀 Processing {job_count} items in {self.num_processes} processes")
        for item in items:
            self.schedule(item, progress)
            
        # wait for all slots to finish
        self.wait_for_slots_to_finish(progress)
                
        # stop all worker processes
        self.stop()

    def wait_for_slots_to_finish(self, progress: ProgressBar | None = None, stop: bool = True):
        

        # wait for all slots to finish
        while self.has_running_slots():
            result = self.result_queue.get()
            self._process_result(result)

            # stop it immediately when requested 
            if stop:
                self.running_slots -= 1
                self.task_queue.put(None)
                                                                                                                                                                        
            if progress is not None:
                progress.step(result['message'])

        if stop:
            self.stop()

    def stop(self):
        # stop all processes
        for _ in range(self.running_slots):
            self.running_slots -= 1
            self.task_queue.put(None)






