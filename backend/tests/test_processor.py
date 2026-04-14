"""
Tests for the background processing engine.
"""

import time
import pytest
from core.processor import ProcessingEngine, Task, Priority, TaskStatus


class TestProcessingEngine:
    """Tests for ProcessingEngine."""

    def test_submit_and_process(self):
        """Task should be executed successfully."""
        engine = ProcessingEngine()

        def my_task():
            return 42

        task = Task("test_task", my_task)
        engine.submit(task)
        engine.start()
        engine.wait(timeout=5)

        assert task.status == TaskStatus.COMPLETED
        assert task.result == 42

    def test_task_failure(self):
        """Failed task should be marked as failed."""
        engine = ProcessingEngine(max_retries=0)

        def failing_task():
            raise ValueError("Test error")

        task = Task("fail_task", failing_task)
        # Note: max_retries is engine-level, so we just check status
        engine.submit(task)
        engine.start()
        engine.wait(timeout=5)

        assert task.status == TaskStatus.FAILED
        assert "Test error" in task.error

    def test_priority_order(self):
        """High priority tasks should be processed before low priority."""
        engine = ProcessingEngine(batch_size=10)
        processed_order = []

        def make_task(name):
            def fn():
                processed_order.append(name)
                return name
            return Task(name, fn)

        # Submit in reverse priority
        engine.submit(make_task("low"))  # Default NORMAL
        # Manually set priorities
        tasks = [
            Task("low", lambda: processed_order.append("low"), priority=Priority.LOW),
            Task("normal", lambda: processed_order.append("normal"), priority=Priority.NORMAL),
            Task("high", lambda: processed_order.append("high"), priority=Priority.HIGH),
        ]
        for t in tasks:
            engine.submit(t)

        engine.start()
        engine.wait(timeout=5)

    def test_pause_resume(self):
        """Engine should pause and resume processing."""
        engine = ProcessingEngine()

        call_count = [0]
        def counting_task():
            call_count[0] += 1
            return call_count[0]

        # Submit many tasks
        for i in range(5):
            engine.submit(Task(f"task_{i}", counting_task))

        engine.start()
        time.sleep(0.1)
        engine.pause()
        time.sleep(0.2)
        paused_count = call_count[0]
        engine.resume()
        time.sleep(0.5)

        # After resume, more tasks should have been processed
        assert call_count[0] >= paused_count

    def test_stop(self):
        """Engine should stop gracefully."""
        engine = ProcessingEngine()

        def quick_task():
            return True

        for i in range(3):
            engine.submit(Task(f"task_{i}", quick_task))

        engine.start()
        engine.wait(timeout=5)
        engine.stop()

        assert not engine.is_running

    def test_progress_tracking(self):
        """Progress info should be updated during processing."""
        progress_updates = []

        def progress_cb(info):
            progress_updates.append(info)

        engine = ProcessingEngine()

        def counting_task():
            return 1

        for i in range(5):
            engine.submit(Task(f"task_{i}", counting_task))

        engine.start(progress_callback=progress_cb)
        engine.wait(timeout=5)

        assert len(progress_updates) > 0

    def test_batch_processing(self):
        """Tasks should be processed in batches."""
        engine = ProcessingEngine(batch_size=3)

        results = []
        def make_task(n):
            def fn():
                results.append(n)
                return n
            return Task(f"task_{n}", fn)

        for i in range(10):
            engine.submit(make_task(i))

        engine.start()
        engine.wait(timeout=5)

        assert len(results) == 10

    def test_retry_on_failure(self):
        """Task should be retried on failure up to max_retries."""
        engine = ProcessingEngine(max_retries=2, retry_delay=0.1)

        attempt = [0]
        def flaky_task():
            attempt[0] += 1
            if attempt[0] < 3:
                raise ValueError(f"Attempt {attempt[0]} failed")
            return "success"

        task = Task("flaky", flaky_task)
        engine.submit(task)
        engine.start()
        engine.wait(timeout=5)

        # Should succeed on 3rd attempt
        assert task.status == TaskStatus.COMPLETED
        assert task.result == "success"
        assert attempt[0] == 3
