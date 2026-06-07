import pytest
from src.utils.observer import EventBus, NotificationObserver, LoggingObserver
from src.storage.repositories import InMemoryNotificationRepository
from src.models.enums import NotificationType


class TestEventBus:
    def setup_method(self):
        self.bus = EventBus()
        self.logger = LoggingObserver()

    def test_subscribe_and_publish(self):
        self.bus.subscribe("test_event", self.logger)
        self.bus.publish("test_event", {"key": "value"})
        assert len(self.logger.get_log()) == 1

    def test_subscribe_all_receives_all_events(self):
        self.bus.subscribe_all(self.logger)
        self.bus.publish("event_a", {})
        self.bus.publish("event_b", {})
        assert len(self.logger.get_log()) == 2

    def test_unsubscribe(self):
        self.bus.subscribe("test_event", self.logger)
        self.bus.unsubscribe("test_event", self.logger)
        self.bus.publish("test_event", {})
        assert len(self.logger.get_log()) == 0

    def test_unsubscribe_all(self):
        self.bus.subscribe_all(self.logger)
        self.bus.unsubscribe_all(self.logger)
        self.bus.publish("event_a", {})
        assert len(self.logger.get_log()) == 0

    def test_no_duplicate_global_subscription(self):
        self.bus.subscribe_all(self.logger)
        self.bus.subscribe_all(self.logger)
        self.bus.publish("test", {})
        assert len(self.logger.get_log()) == 1

    def test_no_duplicate_subscription(self):
        self.bus.subscribe("test", self.logger)
        self.bus.subscribe("test", self.logger)
        self.bus.publish("test", {})
        assert len(self.logger.get_log()) == 1

    def test_clear(self):
        self.bus.subscribe_all(self.logger)
        self.bus.clear()
        self.bus.publish("test", {})
        assert len(self.logger.get_log()) == 0

    def test_unknown_event_no_crash(self):
        self.bus.publish("unknown_event", {})

    def test_log_contains_event_type(self):
        self.bus.subscribe_all(self.logger)
        self.bus.publish("my_event", {"data": 1})
        log = self.logger.get_log()
        assert log[0]["event_type"] == "my_event"

    def test_logger_clear(self):
        self.bus.subscribe_all(self.logger)
        self.bus.publish("test", {})
        self.logger.clear()
        assert len(self.logger.get_log()) == 0


class TestNotificationObserver:
    def setup_method(self):
        self.repo = InMemoryNotificationRepository()
        self.observer = NotificationObserver(self.repo)
        self.bus = EventBus()
        self.bus.subscribe_all(self.observer)

    def test_task_assigned_notification(self):
        self.bus.publish("task_assigned", {
            "user_id": "u1", "task_id": "t1", "task_title": "Book venue", "event_id": "e1"
        })
        notifs = self.repo.find_by_recipient("u1")
        assert len(notifs) == 1
        assert notifs[0].notification_type == NotificationType.TASK_ASSIGNED

    def test_task_overdue_notification(self):
        self.bus.publish("task_overdue", {
            "user_id": "u1", "task_id": "t1", "task_title": "Overdue", "event_id": "e1"
        })
        notifs = self.repo.find_by_recipient("u1")
        assert any(n.notification_type == NotificationType.TASK_OVERDUE for n in notifs)

    def test_event_updated_notification(self):
        self.bus.publish("event_updated", {
            "user_id": "u1", "event_id": "e1", "event_title": "Party"
        })
        notifs = self.repo.find_by_recipient("u1")
        assert any(n.notification_type == NotificationType.EVENT_UPDATED for n in notifs)

    def test_budget_exceeded_notification(self):
        self.bus.publish("budget_exceeded", {
            "user_id": "u1", "event_id": "e1", "event_title": "Party"
        })
        notifs = self.repo.find_by_recipient("u1")
        assert any(n.notification_type == NotificationType.BUDGET_EXCEEDED for n in notifs)

    def test_invitation_notification(self):
        self.bus.publish("invitation", {
            "user_id": "u1", "event_id": "e1", "event_title": "Party"
        })
        notifs = self.repo.find_by_recipient("u1")
        assert any(n.notification_type == NotificationType.INVITATION for n in notifs)

    def test_event_reminder_notification(self):
        self.bus.publish("event_reminder", {
            "user_id": "u1", "event_id": "e1", "event_title": "Party"
        })
        notifs = self.repo.find_by_recipient("u1")
        assert any(n.notification_type == NotificationType.EVENT_REMINDER for n in notifs)

    def test_unknown_event_type_no_notification(self):
        self.bus.publish("totally_unknown", {"user_id": "u1"})
        notifs = self.repo.find_by_recipient("u1")
        assert len(notifs) == 0

    def test_notification_is_unread_by_default(self):
        self.bus.publish("invitation", {
            "user_id": "u1", "event_id": "e1", "event_title": "Party"
        })
        notifs = self.repo.find_by_recipient("u1")
        assert all(not n.is_read for n in notifs)

    def test_notification_task_title_in_message(self):
        self.bus.publish("task_assigned", {
            "user_id": "u1", "task_id": "t1", "task_title": "Buy cake", "event_id": "e1"
        })
        notifs = self.repo.find_by_recipient("u1")
        assert any("Buy cake" in n.message for n in notifs)
