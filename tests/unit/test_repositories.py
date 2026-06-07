import pytest
from src.models.user import User
from src.models.event import Event
from src.models.task import Task
from src.models.enums import UserRole, EventStatus, EventType, TaskStatus, TaskPriority
from src.storage.repositories import (
    InMemoryUserRepository,
    InMemoryEventRepository,
    InMemoryTaskRepository,
    InMemoryNotificationRepository,
)
from src.models.notification import Notification
from src.models.enums import NotificationType


class TestInMemoryUserRepository:
    def setup_method(self):
        self.repo = InMemoryUserRepository()

    def test_save_and_find(self):
        u = User("Alice", "a@b.com")
        self.repo.save(u)
        result = self.repo.find_by_id(u.id)
        assert result == u

    def test_find_nonexistent(self):
        assert self.repo.find_by_id("none") is None

    def test_find_all(self):
        self.repo.save(User("Alice", "a@b.com"))
        self.repo.save(User("Bob", "b@b.com"))
        assert len(self.repo.find_all()) == 2

    def test_delete(self):
        u = User("Alice", "a@b.com")
        self.repo.save(u)
        result = self.repo.delete(u.id)
        assert result is True
        assert self.repo.find_by_id(u.id) is None

    def test_delete_nonexistent(self):
        assert self.repo.delete("none") is False

    def test_exists(self):
        u = User("Alice", "a@b.com")
        self.repo.save(u)
        assert self.repo.exists(u.id) is True
        assert self.repo.exists("other") is False

    def test_count(self):
        self.repo.save(User("Alice", "a@b.com"))
        self.repo.save(User("Bob", "b@b.com"))
        assert self.repo.count() == 2

    def test_find_by_email(self):
        u = User("Alice", "alice@example.com")
        self.repo.save(u)
        found = self.repo.find_by_email("alice@example.com")
        assert found == u

    def test_find_by_email_not_found(self):
        assert self.repo.find_by_email("nope@x.com") is None

    def test_find_active(self):
        u1 = User("Alice", "a@b.com")
        u2 = User("Bob", "b@b.com")
        u2.deactivate()
        self.repo.save(u1)
        self.repo.save(u2)
        active = self.repo.find_active()
        assert len(active) == 1
        assert u1 in active

    def test_clear(self):
        self.repo.save(User("Alice", "a@b.com"))
        self.repo.clear()
        assert self.repo.count() == 0


class TestInMemoryEventRepository:
    def setup_method(self):
        self.repo = InMemoryEventRepository()

    def test_save_and_find(self):
        e = Event("Party", "org-1")
        self.repo.save(e)
        assert self.repo.find_by_id(e.id) == e

    def test_find_by_organizer(self):
        e1 = Event("Party", "org-1")
        e2 = Event("Trip", "org-2")
        self.repo.save(e1)
        self.repo.save(e2)
        result = self.repo.find_by_organizer("org-1")
        assert e1 in result
        assert e2 not in result

    def test_find_by_status(self):
        e1 = Event("Party", "org-1")
        e2 = Event("Trip", "org-2")
        e2.transition_to(EventStatus.PLANNED)
        self.repo.save(e1)
        self.repo.save(e2)
        drafts = self.repo.find_by_status(EventStatus.DRAFT)
        assert e1 in drafts
        assert e2 not in drafts

    def test_find_by_type(self):
        e1 = Event("Party", "org-1", event_type=EventType.HOLIDAY)
        e2 = Event("Trip", "org-2", event_type=EventType.TRAVEL)
        self.repo.save(e1)
        self.repo.save(e2)
        holidays = self.repo.find_by_type(EventType.HOLIDAY)
        assert e1 in holidays
        assert e2 not in holidays

    def test_find_by_participant(self):
        e = Event("Party", "org-1")
        e.add_participant("user-1")
        self.repo.save(e)
        result = self.repo.find_by_participant("user-1")
        assert e in result
        empty = self.repo.find_by_participant("user-999")
        assert len(empty) == 0

    def test_find_with_filter(self):
        e1 = Event("Trip", "org-1", event_type=EventType.TRAVEL)
        e2 = Event("Party", "org-1", event_type=EventType.HOLIDAY)
        self.repo.save(e1)
        self.repo.save(e2)
        result = self.repo.find_with_filter(lambda e: e.event_type == EventType.TRAVEL)
        assert e1 in result
        assert e2 not in result

    def test_clear(self):
        self.repo.save(Event("Party", "org-1"))
        self.repo.clear()
        assert self.repo.count() == 0


class TestInMemoryTaskRepository:
    def setup_method(self):
        self.repo = InMemoryTaskRepository()

    def test_save_and_find(self):
        t = Task("Buy flowers", "event-1")
        self.repo.save(t)
        assert self.repo.find_by_id(t.id) == t

    def test_find_by_event(self):
        t1 = Task("Task A", "event-1")
        t2 = Task("Task B", "event-2")
        self.repo.save(t1)
        self.repo.save(t2)
        result = self.repo.find_by_event("event-1")
        assert t1 in result
        assert t2 not in result

    def test_find_by_assignee(self):
        t1 = Task("Task A", "event-1")
        t2 = Task("Task B", "event-1")
        t1.assignee_id = "user-1"
        self.repo.save(t1)
        self.repo.save(t2)
        result = self.repo.find_by_assignee("user-1")
        assert t1 in result
        assert t2 not in result

    def test_find_by_status(self):
        t1 = Task("Task A", "event-1")
        t2 = Task("Task B", "event-1")
        t2.complete()
        self.repo.save(t1)
        self.repo.save(t2)
        pending = self.repo.find_by_status(TaskStatus.PENDING)
        assert t1 in pending
        assert t2 not in pending

    def test_find_by_priority(self):
        t1 = Task("Task A", "event-1", priority=TaskPriority.HIGH)
        t2 = Task("Task B", "event-1", priority=TaskPriority.LOW)
        self.repo.save(t1)
        self.repo.save(t2)
        result = self.repo.find_by_priority(TaskPriority.HIGH)
        assert t1 in result
        assert t2 not in result

    def test_find_overdue(self):
        from datetime import timedelta, datetime
        t1 = Task("Overdue", "event-1", due_date=datetime.now() - timedelta(hours=1))
        t2 = Task("On time", "event-1", due_date=datetime.now() + timedelta(hours=1))
        self.repo.save(t1)
        self.repo.save(t2)
        overdue = self.repo.find_overdue()
        assert t1 in overdue
        assert t2 not in overdue

    def test_find_unassigned(self):
        t1 = Task("Task A", "event-1")
        t2 = Task("Task B", "event-1")
        t2.assignee_id = "user-1"
        self.repo.save(t1)
        self.repo.save(t2)
        unassigned = self.repo.find_unassigned()
        assert t1 in unassigned
        assert t2 not in unassigned

    def test_clear(self):
        self.repo.save(Task("Task A", "event-1"))
        self.repo.clear()
        assert self.repo.count() == 0


class TestInMemoryNotificationRepository:
    def setup_method(self):
        self.repo = InMemoryNotificationRepository()

    def test_save_and_find(self):
        n = Notification("user-1", NotificationType.INVITATION, "You are invited")
        self.repo.save(n)
        assert self.repo.find_by_id(n.id) == n

    def test_find_by_recipient(self):
        n1 = Notification("user-1", NotificationType.INVITATION, "Msg1")
        n2 = Notification("user-2", NotificationType.TASK_ASSIGNED, "Msg2")
        self.repo.save(n1)
        self.repo.save(n2)
        result = self.repo.find_by_recipient("user-1")
        assert n1 in result
        assert n2 not in result

    def test_find_unread(self):
        n1 = Notification("user-1", NotificationType.INVITATION, "Msg1")
        n2 = Notification("user-1", NotificationType.INVITATION, "Msg2")
        n2.mark_read()
        self.repo.save(n1)
        self.repo.save(n2)
        unread = self.repo.find_unread("user-1")
        assert n1 in unread
        assert n2 not in unread

    def test_clear(self):
        self.repo.save(Notification("user-1", NotificationType.INVITATION, "Msg"))
        self.repo.clear()
        assert self.repo.count() == 0
