import uuid
from dataclasses import dataclass, field
from typing import Optional

from models import TaskStatus


@dataclass
class Task:
    id: str
    query: str
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[list[dict]] = None
    error: Optional[str] = None


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


# Global task manager instance
task_manager = TaskManager()

