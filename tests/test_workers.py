"""Unit tests for workers."""

import pytest
import asyncio
import numpy as np
from src.core.workers import Supervisor, Worker, Task, TaskResult, WorkerType


class MockWorker(Worker):
    """Mock worker for testing."""

    def __init__(self, worker_type: WorkerType, should_fail: bool = False):
        super().__init__(worker_type)
        self.should_fail = should_fail

    async def process(self, task: Task) -> TaskResult:
        if self.should_fail:
            return TaskResult(task.task_id, False, error="Mock failure")
        return TaskResult(task.task_id, True, {"result": "ok"})


@pytest.mark.asyncio
async def test_supervisor_registration():
    """Test worker registration."""
    supervisor = Supervisor(max_workers=2)
    worker = MockWorker(WorkerType.RETRIEVAL)

    supervisor.register_worker(worker)

    assert WorkerType.RETRIEVAL in supervisor.workers
    assert len(supervisor.workers[WorkerType.RETRIEVAL]) == 1


@pytest.mark.asyncio
async def test_supervisor_task_submission():
    """Test task submission."""
    supervisor = Supervisor(max_workers=2)
    worker = MockWorker(WorkerType.RETRIEVAL)
    supervisor.register_worker(worker)

    await supervisor.start()

    task = Task(
        task_id="test-1", worker_type=WorkerType.RETRIEVAL, input_data={"query": "test"}
    )

    result = await supervisor.submit_task(task)

    await supervisor.stop()

    assert result.success is True
    assert result.output_data["result"] == "ok"


@pytest.mark.asyncio
async def test_supervisor_task_failure():
    """Test task failure handling."""
    supervisor = Supervisor(max_workers=2)
    worker = MockWorker(WorkerType.RETRIEVAL, should_fail=True)
    supervisor.register_worker(worker)

    await supervisor.start()

    task = Task(
        task_id="test-fail",
        worker_type=WorkerType.RETRIEVAL,
        input_data={"query": "test"},
    )

    result = await supervisor.submit_task(task)

    await supervisor.stop()

    assert result.success is False
    assert result.error == "Mock failure"
