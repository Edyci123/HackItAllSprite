import uuid
import time
from dataclasses import dataclass, field
from typing import Optional, Callable

from models import TaskStatus


@dataclass
class Task:
    id: str
    query: str
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[list[dict]] = None
    error: Optional[str] = None
    # Detailed progress tracking
    current_step: str = "initializing"
    step_message: str = "Preparing your search..."
    total_products: int = 0
    scored_products: list = field(default_factory=list)
    progress_percent: int = 0
    started_at: float = field(default_factory=time.time)


class TaskManager:
    def __init__(self):
        self._tasks: dict[str, Task] = {}

    def create_task(self, query: str) -> Task:
        task_id = str(uuid.uuid4())
        task = Task(id=task_id, query=query)
        self._tasks[task_id] = task
        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        return self._tasks.get(task_id)

    def update_task_status(self, task_id: str, status: TaskStatus) -> Optional[Task]:
        task = self._tasks.get(task_id)
        if task:
            task.status = status
        return task

    def complete_task(self, task_id: str, result: list[dict]) -> Optional[Task]:
        task = self._tasks.get(task_id)
        if task:
            task.status = TaskStatus.COMPLETED
            task.result = result
        return task

    def fail_task(self, task_id: str, error: str) -> Optional[Task]:
        task = self._tasks.get(task_id)
        if task:
            task.status = TaskStatus.FAILED
            task.error = error
        return task

    def update_task_progress(
        self,
        task_id: str,
        current_step: str = None,
        step_message: str = None,
        total_products: int = None,
        scored_product: dict = None,
        progress_percent: int = None
    ) -> Optional[Task]:
        """Update detailed progress information for a task."""
        task = self._tasks.get(task_id)
        if task:
            if current_step is not None:
                task.current_step = current_step
            if step_message is not None:
                task.step_message = step_message
            if total_products is not None:
                task.total_products = total_products
            if scored_product is not None:
                task.scored_products.append(scored_product)
            if progress_percent is not None:
                task.progress_percent = progress_percent
        return task


# Global task manager instance
task_manager = TaskManager()

