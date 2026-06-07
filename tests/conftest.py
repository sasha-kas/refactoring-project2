import pytest
from datetime import datetime, timedelta
from src.models.user import User
from src.models.event import Event
from src.models.task import Task
from src.models.enums import UserRole, EventType, EventStatus, TaskPriority, TaskStatus
from src.storage.repositories import (
    InMemoryUserRepository,
    InMemoryEventRepository,
    InMemoryTaskRepository,
    InMemoryNotificationRepository,
)
from src.services.event_service import EventService
from src.services.task_service import TaskService
from src.services.user_service import UserService, NotificationService
from src.utils.observer import EventBus, NotificationObserver, LoggingObserver


@pytest.fixture
def user_repo():
    return InMemoryUserRepository()


@pytest.fixture
def event_repo():
    return InMemoryEventRepository()


@pytest.fixture
def task_repo():
    return InMemoryTaskRepository()


@pytest.fixture
def notification_repo():
    return InMemoryNotificationRepository()


@pytest.fixture
def event_bus():
    return EventBus()


@pytest.fixture
def logging_observer():
    return LoggingObserver()


@pytest.fixture
def full_bus(notification_repo):
    bus = EventBus()
    observer = NotificationObserver(notification_repo)
    bus.subscribe_all(observer)
    return bus


@pytest.fixture
def user_service(user_repo):
    return UserService(user_repo)


@pytest.fixture
def event_service(event_repo, user_repo, full_bus):
    return EventService(event_repo, user_repo, full_bus)


@pytest.fixture
def task_service(task_repo, event_repo, user_repo, full_bus):
    return TaskService(task_repo, event_repo, user_repo, full_bus)


@pytest.fixture
def notification_service(notification_repo):
    return NotificationService(notification_repo)


@pytest.fixture
def sample_user(user_service):
    return user_service.register("Alice", "alice@example.com", UserRole.ORGANIZER)


@pytest.fixture
def sample_user2(user_service):
    return user_service.register("Bob", "bob@example.com")


@pytest.fixture
def sample_user3(user_service):
    return user_service.register("Carol", "carol@example.com")


@pytest.fixture
def sample_event(event_service, sample_user):
    return event_service.create_event(
        title="Summer Party",
        organizer_id=sample_user.id,
        event_type=EventType.HOLIDAY,
        description="Annual summer party",
        location="City Park",
        start_date=datetime.now() + timedelta(days=30),
        end_date=datetime.now() + timedelta(days=31),
        total_budget=5000.0,
    )


@pytest.fixture
def sample_task(task_service, sample_event, sample_user):
    return task_service.create_task(
        title="Book venue",
        event_id=sample_event.id,
        description="Find and book the venue",
        priority=TaskPriority.HIGH,
        estimated_cost=1000.0,
    )


@pytest.fixture
def shared_context():
    """All services sharing the same bus and notification_repo instance."""
    _user_repo = InMemoryUserRepository()
    _event_repo = InMemoryEventRepository()
    _task_repo = InMemoryTaskRepository()
    _notif_repo = InMemoryNotificationRepository()
    _bus = EventBus()
    _bus.subscribe_all(NotificationObserver(_notif_repo))
    return {
        "user_service": UserService(_user_repo),
        "event_service": EventService(_event_repo, _user_repo, _bus),
        "task_service": TaskService(_task_repo, _event_repo, _user_repo, _bus),
        "notification_service": NotificationService(_notif_repo),
    }
