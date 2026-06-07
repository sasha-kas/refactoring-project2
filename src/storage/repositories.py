from typing import List, Optional, Callable
from src.storage.interfaces import IRepository
from src.models.user import User
from src.models.event import Event
from src.models.task import Task
from src.models.notification import Notification
from src.models.enums import EventStatus, EventType, TaskStatus, TaskPriority


class InMemoryUserRepository(IRepository[User]):
    def __init__(self):
        self._store: dict[str, User] = {}

    def save(self, user: User) -> User:
        self._store[user.id] = user
        return user

    def find_by_id(self, user_id: str) -> Optional[User]:
        return self._store.get(user_id)

    def find_all(self) -> List[User]:
        return list(self._store.values())

    def delete(self, user_id: str) -> bool:
        if user_id in self._store:
            del self._store[user_id]
            return True
        return False

    def exists(self, user_id: str) -> bool:
        return user_id in self._store

    def count(self) -> int:
        return len(self._store)

    def find_by_email(self, email: str) -> Optional[User]:
        for user in self._store.values():
            if user.email == email:
                return user
        return None

    def find_active(self) -> List[User]:
        return [u for u in self._store.values() if u.is_active]

    def clear(self):
        self._store.clear()


class InMemoryEventRepository(IRepository[Event]):
    def __init__(self):
        self._store: dict[str, Event] = {}

    def save(self, event: Event) -> Event:
        self._store[event.id] = event
        return event

    def find_by_id(self, event_id: str) -> Optional[Event]:
        return self._store.get(event_id)

    def find_all(self) -> List[Event]:
        return list(self._store.values())

    def delete(self, event_id: str) -> bool:
        if event_id in self._store:
            del self._store[event_id]
            return True
        return False

    def exists(self, event_id: str) -> bool:
        return event_id in self._store

    def count(self) -> int:
        return len(self._store)

    def find_by_organizer(self, organizer_id: str) -> List[Event]:
        return [e for e in self._store.values() if e.organizer_id == organizer_id]

    def find_by_status(self, status: EventStatus) -> List[Event]:
        return [e for e in self._store.values() if e.status == status]

    def find_by_type(self, event_type: EventType) -> List[Event]:
        return [e for e in self._store.values() if e.event_type == event_type]

    def find_by_participant(self, user_id: str) -> List[Event]:
        return [
            e for e in self._store.values()
            if any(p.user_id == user_id for p in e.participants)
        ]

    def find_with_filter(self, predicate: Callable[[Event], bool]) -> List[Event]:
        return [e for e in self._store.values() if predicate(e)]

    def clear(self):
        self._store.clear()


class InMemoryTaskRepository(IRepository[Task]):
    def __init__(self):
        self._store: dict[str, Task] = {}

    def save(self, task: Task) -> Task:
        self._store[task.id] = task
        return task

    def find_by_id(self, task_id: str) -> Optional[Task]:
        return self._store.get(task_id)

    def find_all(self) -> List[Task]:
        return list(self._store.values())

    def delete(self, task_id: str) -> bool:
        if task_id in self._store:
            del self._store[task_id]
            return True
        return False

    def exists(self, task_id: str) -> bool:
        return task_id in self._store

    def count(self) -> int:
        return len(self._store)

    def find_by_event(self, event_id: str) -> List[Task]:
        return [t for t in self._store.values() if t.event_id == event_id]

    def find_by_assignee(self, user_id: str) -> List[Task]:
        return [t for t in self._store.values() if t.assignee_id == user_id]

    def find_by_status(self, status: TaskStatus) -> List[Task]:
        return [t for t in self._store.values() if t.status == status]

    def find_by_priority(self, priority: TaskPriority) -> List[Task]:
        return [t for t in self._store.values() if t.priority == priority]

    def find_overdue(self) -> List[Task]:
        return [t for t in self._store.values() if t.is_overdue()]

    def find_unassigned(self) -> List[Task]:
        return [t for t in self._store.values() if t.assignee_id is None]

    def clear(self):
        self._store.clear()


class InMemoryNotificationRepository(IRepository[Notification]):
    def __init__(self):
        self._store: dict[str, Notification] = {}

    def save(self, notification: Notification) -> Notification:
        self._store[notification.id] = notification
        return notification

    def find_by_id(self, notification_id: str) -> Optional[Notification]:
        return self._store.get(notification_id)

    def find_all(self) -> List[Notification]:
        return list(self._store.values())

    def delete(self, notification_id: str) -> bool:
        if notification_id in self._store:
            del self._store[notification_id]
            return True
        return False

    def exists(self, notification_id: str) -> bool:
        return notification_id in self._store

    def count(self) -> int:
        return len(self._store)

    def find_by_recipient(self, user_id: str) -> List[Notification]:
        return [n for n in self._store.values() if n.recipient_id == user_id]

    def find_unread(self, user_id: str) -> List[Notification]:
        return [
            n for n in self._store.values()
            if n.recipient_id == user_id and not n.is_read
        ]

    def clear(self):
        self._store.clear()
