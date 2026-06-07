from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
import uuid

from src.models.enums import TaskStatus, TaskPriority


@dataclass
class Task:
    title: str
    event_id: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    assignee_id: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    estimated_cost: float = 0.0
    actual_cost: float = 0.0
    tags: List[str] = field(default_factory=list)
    comments: List[str] = field(default_factory=list)

    def __eq__(self, other):
        if not isinstance(other, Task):
            return False
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

    def __repr__(self):
        return f"Task(id={self.id[:8]}, title={self.title}, status={self.status.value})"

    def assign_to(self, user_id: str):
        self.assignee_id = user_id
        if self.status == TaskStatus.PENDING:
            self.status = TaskStatus.IN_PROGRESS

    def complete(self):
        self.status = TaskStatus.DONE
        self.completed_at = datetime.now()

    def mark_overdue(self):
        self.status = TaskStatus.OVERDUE

    def is_overdue(self) -> bool:
        if self.due_date is None:
            return False
        return datetime.now() > self.due_date and self.status not in (
            TaskStatus.DONE,
            TaskStatus.OVERDUE,
        )

    def add_comment(self, comment: str):
        self.comments.append(comment)

    def add_tag(self, tag: str):
        if tag not in self.tags:
            self.tags.append(tag)

    def cost_variance(self) -> float:
        return self.actual_cost - self.estimated_cost

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "event_id": self.event_id,
            "description": self.description,
            "assignee_id": self.assignee_id,
            "status": self.status.value,
            "priority": self.priority.value,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "estimated_cost": self.estimated_cost,
            "actual_cost": self.actual_cost,
            "tags": self.tags,
            "comments": self.comments,
        }
