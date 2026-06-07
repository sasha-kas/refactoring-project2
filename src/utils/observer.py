"""
Observer Pattern — сповіщення учасників про зміни в подіях та задачах.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Set
from src.models.notification import Notification
from src.models.enums import NotificationType
from src.storage.repositories import InMemoryNotificationRepository


class IEventObserver(ABC):
    @abstractmethod
    def on_event(self, event_type: str, payload: dict):
        pass


class NotificationObserver(IEventObserver):
    """Creates in-memory notifications for users."""

    def __init__(self, notification_repo: InMemoryNotificationRepository):
        self._repo = notification_repo

    def on_event(self, event_type: str, payload: dict):
        notification = self._build_notification(event_type, payload)
        if notification:
            self._repo.save(notification)

    def _build_notification(self, event_type: str, payload: dict):
        handlers = {
            "task_assigned": self._task_assigned,
            "task_overdue": self._task_overdue,
            "event_updated": self._event_updated,
            "budget_exceeded": self._budget_exceeded,
            "invitation": self._invitation,
            "event_reminder": self._event_reminder,
        }
        handler = handlers.get(event_type)
        return handler(payload) if handler else None

    def _task_assigned(self, payload: dict) -> Notification:
        return Notification(
            recipient_id=payload["user_id"],
            notification_type=NotificationType.TASK_ASSIGNED,
            message=f"You have been assigned task: {payload.get('task_title', '')}",
            related_event_id=payload.get("event_id"),
            related_task_id=payload.get("task_id"),
        )

    def _task_overdue(self, payload: dict) -> Notification:
        return Notification(
            recipient_id=payload["user_id"],
            notification_type=NotificationType.TASK_OVERDUE,
            message=f"Task overdue: {payload.get('task_title', '')}",
            related_event_id=payload.get("event_id"),
            related_task_id=payload.get("task_id"),
        )

    def _event_updated(self, payload: dict) -> Notification:
        return Notification(
            recipient_id=payload["user_id"],
            notification_type=NotificationType.EVENT_UPDATED,
            message=f"Event '{payload.get('event_title', '')}' was updated",
            related_event_id=payload.get("event_id"),
        )

    def _budget_exceeded(self, payload: dict) -> Notification:
        return Notification(
            recipient_id=payload["user_id"],
            notification_type=NotificationType.BUDGET_EXCEEDED,
            message=f"Budget exceeded for event: {payload.get('event_title', '')}",
            related_event_id=payload.get("event_id"),
        )

    def _invitation(self, payload: dict) -> Notification:
        return Notification(
            recipient_id=payload["user_id"],
            notification_type=NotificationType.INVITATION,
            message=f"You are invited to: {payload.get('event_title', '')}",
            related_event_id=payload.get("event_id"),
        )

    def _event_reminder(self, payload: dict) -> Notification:
        return Notification(
            recipient_id=payload["user_id"],
            notification_type=NotificationType.EVENT_REMINDER,
            message=f"Reminder: '{payload.get('event_title', '')}' is coming up",
            related_event_id=payload.get("event_id"),
        )


class LoggingObserver(IEventObserver):
    """Simple logging observer for auditing."""

    def __init__(self):
        self.log: List[dict] = []

    def on_event(self, event_type: str, payload: dict):
        from datetime import datetime
        self.log.append({
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "payload": payload,
        })

    def get_log(self) -> List[dict]:
        return list(self.log)

    def clear(self):
        self.log.clear()


class EventBus:
    """Central event bus — manages observers and dispatches events."""

    def __init__(self):
        self._observers: Dict[str, List[IEventObserver]] = {}
        self._global_observers: List[IEventObserver] = []

    def subscribe(self, event_type: str, observer: IEventObserver):
        if event_type not in self._observers:
            self._observers[event_type] = []
        if observer not in self._observers[event_type]:
            self._observers[event_type].append(observer)

    def subscribe_all(self, observer: IEventObserver):
        if observer not in self._global_observers:
            self._global_observers.append(observer)

    def unsubscribe(self, event_type: str, observer: IEventObserver):
        if event_type in self._observers:
            self._observers[event_type] = [
                o for o in self._observers[event_type] if o is not observer
            ]

    def unsubscribe_all(self, observer: IEventObserver):
        self._global_observers = [o for o in self._global_observers if o is not observer]

    def publish(self, event_type: str, payload: dict):
        for observer in self._global_observers:
            observer.on_event(event_type, payload)
        for observer in self._observers.get(event_type, []):
            observer.on_event(event_type, payload)

    def clear(self):
        self._observers.clear()
        self._global_observers.clear()
