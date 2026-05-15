"""Supervisor-Worker Pattern for RAG Application."""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class WorkerType(Enum):
    EMBEDDING = "embedding"
    RETRIEVAL = "retrieval"
    GENERATION = "generation"
    VALIDATION = "validation"


@dataclass
class Task:
    task_id: str
    worker_type: WorkerType
    input_data: dict[str, Any]
    priority: int = 0


@dataclass
class TaskResult:
    task_id: str
    success: bool
    output_data: dict[str, Any] | None = None
    error: str | None = None


class Worker(ABC):
    """Base Worker class."""

    def __init__(self, worker_type: WorkerType):
        self.worker_type = worker_type
        self.is_busy = False

    @abstractmethod
    async def process(self, task: Task) -> TaskResult:
        """Process a task and return result."""
        pass

    async def initialize(self) -> None:
        """Initialize worker resources."""
        pass

    async def cleanup(self) -> None:
        """Cleanup worker resources."""
        pass


class Supervisor:
    """Supervor orchestrates workers for task processing."""

    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.workers: dict[WorkerType, list[Worker]] = {}
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.results: dict[str, asyncio.Future] = {}
        self._running = False

    def register_worker(self, worker: Worker) -> None:
        """Register a worker."""
        if worker.worker_type not in self.workers:
            self.workers[worker.worker_type] = []
        self.workers[worker.worker_type].append(worker)
        logger.info(f"Registered {worker.worker_type.value} worker")

    async def _process_task(self, worker_type: WorkerType) -> None:
        """Process tasks from queue."""
        workers = self.workers.get(worker_type, [])
        if not workers:
            return

        worker = workers[0]
        while self._running:
            try:
                task = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
            except TimeoutError:
                continue

            worker.is_busy = True
            try:
                result = await worker.process(task)
                if task.task_id in self.results:
                    self.results[task.task_id].set_result(result)
            except Exception as e:
                logger.error(f"Task {task.task_id} failed: {e}")
                if task.task_id in self.results:
                    self.results[task.task_id].set_result(
                        TaskResult(task.task_id, False, error=str(e))
                    )
            finally:
                worker.is_busy = False
                self.task_queue.task_done()

    async def submit_task(self, task: Task) -> TaskResult:
        """Submit a task and wait for result."""
        future = asyncio.Future()
        self.results[task.task_id] = future
        await self.task_queue.put(task)

        try:
            result = await asyncio.wait_for(future, timeout=60.0)
            return result
        except TimeoutError:
            return TaskResult(task.task_id, False, error="Task timeout")
        finally:
            self.results.pop(task.task_id, None)

    async def start(self) -> None:
        """Start the supervisor."""
        self._running = True
        for worker_type in self.workers:
            for _ in range(min(2, self.max_workers)):
                asyncio.create_task(self._process_task(worker_type))
        logger.info("Supervisor started")

    async def stop(self) -> None:
        """Stop the supervisor."""
        self._running = False
        for workers in self.workers.values():
            for worker in workers:
                await worker.cleanup()
        logger.info("Supervisor stopped")
