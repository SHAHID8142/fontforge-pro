from __future__ import annotations

"""
Background processing engine — queue-based, pause/resume, batch processing.
"""

import logging
import queue
import threading
import time
from enum import Enum
from typing import Callable, Any, Optional

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Priority(Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2


class Task:
    """A single unit of work."""

    def __init__(self, name: str, func: Callable, args: tuple = (),
                 kwargs: dict = None, priority: Priority = Priority.NORMAL):
        self.name = name
        self.func = func
        self.args = args
        self.kwargs = kwargs or {}
        self.priority = priority
        self.status = TaskStatus.PENDING
        self.result: Any = None
        self.error: str = ""
        self.created_at = time.time()

    def execute(self) -> bool:
        """Run the task. Returns True on success."""
        self.status = TaskStatus.RUNNING
        try:
            self.result = self.func(*self.args, **self.kwargs)
            self.status = TaskStatus.COMPLETED
            logger.debug(f"Task completed: {self.name}")
            return True
        except Exception as e:
            self.status = TaskStatus.FAILED
            self.error = str(e)
            logger.error(f"Task failed: {self.name}: {e}")
            return False


class ProgressInfo:
    """Progress tracking information."""

    def __init__(self):
        self.total = 0
        self.completed = 0
        self.failed = 0
        self.current = ""
        self.percentage = 0.0
        self.eta_seconds = 0.0
        self.items_per_second = 0.0
        self.started_at = time.time()

    def update(self, completed: int, failed: int, total: int, current: str = ""):
        """Update progress metrics."""
        self.completed = completed
        self.failed = failed
        self.total = total
        self.current = current

        done = completed + failed
        if total > 0:
            self.percentage = (done / total) * 100

        elapsed = time.time() - self.started_at
        if elapsed > 0:
            self.items_per_second = done / elapsed
            remaining = total - done
            if self.items_per_second > 0:
                self.eta_seconds = remaining / self.items_per_second

    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "completed": self.completed,
            "failed": self.failed,
            "current": self.current,
            "percentage": round(self.percentage, 1),
            "eta_seconds": round(self.eta_seconds, 1),
            "items_per_second": round(self.items_per_second, 1),
        }


class ProcessingEngine:
    """
    Queue-based background processor with pause/resume and batch support.

    Features:
    - Priority queue (HIGH > NORMAL > LOW)
    - Pause/resume
    - Batch checkpointing
    - Progress tracking with ETA
    - Auto-retry on transient failures
    """

    def __init__(
        self,
        batch_size: int = 50,
        max_retries: int = 2,
        retry_delay: float = 1.0,
    ):
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        self._queue: queue.PriorityQueue = queue.PriorityQueue()
        self._counter = 0  # For stable sort in priority queue
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()  # Not paused initially

        self._progress = ProgressInfo()
        self._progress_callback: Callable | None = None
        self._worker_thread: threading.Thread | None = None

    def submit(self, task: Task):
        """Add a task to the processing queue."""
        with self._lock:
            # Negate priority value so HIGH priority tasks come first
            self._queue.put((-task.priority.value, self._counter, task))
            self._counter += 1
        logger.debug(f"Task submitted: {task.name} (priority: {task.priority.name})")

    def submit_batch(self, tasks: list[Task]):
        """Add multiple tasks to the queue."""
        for task in tasks:
            self.submit(task)
        logger.info(f"Batch submitted: {len(tasks)} tasks")

    def start(self, progress_callback: Callable | None = None):
        """Start the worker thread."""
        self._progress_callback = progress_callback
        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()
        logger.info("Processing engine started")

    def stop(self):
        """Stop the worker thread."""
        self._stop_event.set()
        self._pause_event.set()  # Unpause to allow graceful shutdown
        if self._worker_thread:
            self._worker_thread.join(timeout=10)
        logger.info("Processing engine stopped")

    def pause(self):
        """Pause processing."""
        self._pause_event.clear()
        logger.info("Processing paused")

    def resume(self):
        """Resume processing."""
        self._pause_event.set()
        logger.info("Processing resumed")

    @property
    def is_paused(self) -> bool:
        return not self._pause_event.is_set()

    @property
    def is_running(self) -> bool:
        return self._worker_thread is not None and self._worker_thread.is_alive()

    @property
    def progress(self) -> ProgressInfo:
        return self._progress

    def _worker_loop(self):
        """Main worker loop — processes tasks in batches."""
        batch_count = 0

        while not self._stop_event.is_set():
            # Wait if paused
            self._pause_event.wait()

            if self._queue.empty():
                time.sleep(0.1)
                continue

            batch_count += 1
            batch_tasks = []
            batch_size = min(self.batch_size, self._queue.qsize())

            # Dequeue a batch
            for _ in range(batch_size):
                if self._queue.empty():
                    break
                try:
                    _, _, task = self._queue.get_nowait()
                    batch_tasks.append(task)
                except queue.Empty:
                    break

            if not batch_tasks:
                continue

            logger.info(f"Processing batch {batch_count} ({len(batch_tasks)} tasks)")

            for task in batch_tasks:
                if self._stop_event.is_set():
                    break

                # Wait if paused
                self._pause_event.wait()

                self._progress.update(
                    completed=self._progress.completed,
                    failed=self._progress.failed,
                    total=self._queue.qsize() + len(batch_tasks),
                    current=task.name,
                )

                # Execute with retry
                success = False
                for attempt in range(self.max_retries + 1):
                    success = task.execute()
                    if success:
                        break
                    if attempt < self.max_retries:
                        logger.warning(f"Retrying {task.name} (attempt {attempt + 2})")
                        time.sleep(self.retry_delay * (attempt + 1))

                if success:
                    self._progress.completed += 1
                else:
                    self._progress.failed += 1

                # Report progress
                if self._progress_callback:
                    self._progress_callback(self._progress.to_dict())

        logger.info("Worker loop exited")

    def wait(self, timeout: float | None = None) -> bool:
        """Wait for all tasks to complete."""
        if self._worker_thread:
            self._worker_thread.join(timeout=timeout)
            return not self._worker_thread.is_alive()
        return True

    def queue_size(self) -> int:
        """Get number of tasks remaining in queue."""
        return self._queue.qsize()
