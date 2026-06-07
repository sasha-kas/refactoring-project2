from typing import List, Optional
from datetime import datetime

from src.models.task import Task
from src.models.enums import TaskStatus, TaskPriority
from src.storage.repositories import (
    InMemoryTaskRepository,
    InMemoryEventRepository,
    InMemoryUserRepository,
)
from src.utils.observer import EventBus
from src.utils.strategies import ITaskPriorityStrategy, DeadlineBasedPriorityStrategy


class TaskService:
    def __init__(
        self,
        task_repo: InMemoryTaskRepository,
        event_repo: InMemoryEventRepository,
        user_repo: InMemoryUserRepository,
        event_bus: EventBus,
        priority_strategy: ITaskPriorityStrategy = None,
    ):
        self._task_repo = task_repo
        self._event_repo = event_repo
        self._user_repo = user_repo
        self._bus = event_bus
        self._priority_strategy = priority_strategy or DeadlineBasedPriorityStrategy()

    def create_task(
        self,
        title: str,
        event_id: str,
        description: str = "",
        assignee_id: Optional[str] = None,
        priority: TaskPriority = TaskPriority.MEDIUM,
        due_date: Optional[datetime] = None,
        estimated_cost: float = 0.0,
        tags: Optional[List[str]] = None,
    ) -> Task:
        if not title or not title.strip():
            raise ValueError("Task title cannot be empty")
        if not self._event_repo.exists(event_id):
            raise ValueError(f"Event {event_id} not found")
        if assignee_id and not self._user_repo.exists(assignee_id):
            raise ValueError(f"User {assignee_id} not found")
        if estimated_cost < 0:
            raise ValueError("Estimated cost cannot be negative")

        task = Task(
            title=title.strip(),
            event_id=event_id,
            description=description,
            assignee_id=assignee_id,
            priority=priority,
            due_date=due_date,
            estimated_cost=estimated_cost,
            tags=tags or [],
        )
        if assignee_id:
            task.status = TaskStatus.IN_PROGRESS

        self._task_repo.save(task)

        event = self._event_repo.find_by_id(event_id)
        if event:
            event.add_task(task.id)
            self._event_repo.save(event)

        if assignee_id:
            self._bus.publish("task_assigned", {
                "user_id": assignee_id,
                "task_id": task.id,
                "task_title": task.title,
                "event_id": event_id,
            })

        return task

    def get_task(self, task_id: str) -> Task:
        task = self._task_repo.find_by_id(task_id)
        if not task:
            raise KeyError(f"Task {task_id} not found")
        return task

    def assign_task(self, task_id: str, user_id: str) -> Task:
        task = self.get_task(task_id)
        if not self._user_repo.exists(user_id):
            raise ValueError(f"User {user_id} not found")
        task.assign_to(user_id)
        self._task_repo.save(task)
        self._bus.publish("task_assigned", {
            "user_id": user_id,
            "task_id": task.id,
            "task_title": task.title,
            "event_id": task.event_id,
        })
        return task

    def complete_task(self, task_id: str) -> Task:
        task = self.get_task(task_id)
        if task.status == TaskStatus.DONE:
            raise ValueError("Task is already completed")
        task.complete()
        self._task_repo.save(task)
        return task

    def update_task_cost(self, task_id: str, actual_cost: float) -> Task:
        if actual_cost < 0:
            raise ValueError("Actual cost cannot be negative")
        task = self.get_task(task_id)
        task.actual_cost = actual_cost
        self._task_repo.save(task)
        return task

    def add_comment(self, task_id: str, comment: str) -> Task:
        if not comment or not comment.strip():
            raise ValueError("Comment cannot be empty")
        task = self.get_task(task_id)
        task.add_comment(comment.strip())
        self._task_repo.save(task)
        return task

    def check_and_mark_overdue(self) -> List[Task]:
        overdue = []
        for task in self._task_repo.find_all():
            if task.is_overdue():
                task.mark_overdue()
                self._task_repo.save(task)
                if task.assignee_id:
                    self._bus.publish("task_overdue", {
                        "user_id": task.assignee_id,
                        "task_id": task.id,
                        "task_title": task.title,
                        "event_id": task.event_id,
                    })
                overdue.append(task)
        return overdue

    def get_sorted_by_priority(self, event_id: Optional[str] = None) -> List[Task]:
        tasks = (
            self._task_repo.find_by_event(event_id)
            if event_id
            else self._task_repo.find_all()
        )
        return sorted(tasks, key=lambda t: self._priority_strategy.compute_score(t), reverse=True)

    def get_tasks_by_event(self, event_id: str) -> List[Task]:
        return self._task_repo.find_by_event(event_id)

    def get_tasks_by_assignee(self, user_id: str) -> List[Task]:
        return self._task_repo.find_by_assignee(user_id)

    def get_unassigned_tasks(self) -> List[Task]:
        return self._task_repo.find_unassigned()

    def get_overdue_tasks(self) -> List[Task]:
        return self._task_repo.find_overdue()

    def delete_task(self, task_id: str) -> bool:
        task = self._task_repo.find_by_id(task_id)
        if task:
            event = self._event_repo.find_by_id(task.event_id)
            if event:
                event.remove_task(task_id)
                self._event_repo.save(event)
        return self._task_repo.delete(task_id)

    def get_event_progress(self, event_id: str) -> dict:
        tasks = self._task_repo.find_by_event(event_id)
        total = len(tasks)
        if total == 0:
            return {"total": 0, "done": 0, "in_progress": 0, "pending": 0, "overdue": 0, "percent": 0.0}
        done = sum(1 for t in tasks if t.status == TaskStatus.DONE)
        in_progress = sum(1 for t in tasks if t.status == TaskStatus.IN_PROGRESS)
        pending = sum(1 for t in tasks if t.status == TaskStatus.PENDING)
        overdue = sum(1 for t in tasks if t.status == TaskStatus.OVERDUE)
        return {
            "total": total,
            "done": done,
            "in_progress": in_progress,
            "pending": pending,
            "overdue": overdue,
            "percent": round(done / total * 100, 1),
        }

    def set_priority_strategy(self, strategy: ITaskPriorityStrategy):
        self._priority_strategy = strategy
