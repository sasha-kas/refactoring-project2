import pytest
from datetime import datetime, timedelta
from src.models.enums import EventType, EventStatus
from tests.conftest import *


class TestEventServiceCreate:
    def test_create_basic_event(self, event_service, sample_user):
        e = event_service.create_event("Trip", sample_user.id, EventType.TRAVEL)
        assert e.title == "Trip"
        assert e.organizer_id == sample_user.id
        assert e.event_type == EventType.TRAVEL

    def test_create_with_dates(self, event_service, sample_user):
        start = datetime.now() + timedelta(days=10)
        end = datetime.now() + timedelta(days=12)
        e = event_service.create_event("Trip", sample_user.id, start_date=start, end_date=end)
        assert e.start_date == start
        assert e.end_date == end

    def test_create_with_budget(self, event_service, sample_user):
        e = event_service.create_event("Trip", sample_user.id, total_budget=1000.0)
        assert e.total_budget == pytest.approx(1000.0)

    def test_create_empty_title_raises(self, event_service, sample_user):
        with pytest.raises(ValueError):
            event_service.create_event("", sample_user.id)

    def test_create_whitespace_title_raises(self, event_service, sample_user):
        with pytest.raises(ValueError):
            event_service.create_event("   ", sample_user.id)

    def test_create_unknown_organizer_raises(self, event_service):
        with pytest.raises(ValueError):
            event_service.create_event("Trip", "unknown-id")

    def test_create_end_before_start_raises(self, event_service, sample_user):
        start = datetime.now() + timedelta(days=5)
        end = datetime.now() + timedelta(days=3)
        with pytest.raises(ValueError):
            event_service.create_event("Trip", sample_user.id, start_date=start, end_date=end)

    def test_create_negative_budget_raises(self, event_service, sample_user):
        with pytest.raises(ValueError):
            event_service.create_event("Trip", sample_user.id, total_budget=-100.0)

    def test_create_strips_whitespace_from_title(self, event_service, sample_user):
        e = event_service.create_event("  Party  ", sample_user.id)
        assert e.title == "Party"

    def test_create_with_max_participants(self, event_service, sample_user):
        e = event_service.create_event("Trip", sample_user.id, max_participants=10)
        assert e.max_participants == 10


class TestEventServiceGetUpdate:
    def test_get_event(self, event_service, sample_event):
        found = event_service.get_event(sample_event.id)
        assert found == sample_event

    def test_get_nonexistent_raises(self, event_service):
        with pytest.raises(KeyError):
            event_service.get_event("nope")

    def test_update_event_title(self, event_service, sample_event):
        event_service.update_event(sample_event.id, title="New Title")
        assert sample_event.title == "New Title"

    def test_update_unknown_field_raises(self, event_service, sample_event):
        with pytest.raises(ValueError):
            event_service.update_event(sample_event.id, hacker_field="bad")

    def test_delete_event(self, event_service, sample_event):
        result = event_service.delete_event(sample_event.id)
        assert result is True
        with pytest.raises(KeyError):
            event_service.get_event(sample_event.id)


class TestEventServiceParticipants:
    def test_invite_participant(self, event_service, sample_event, sample_user2):
        result = event_service.invite_participant(sample_event.id, sample_user2.id)
        assert result is True
        assert sample_event.participant_count() == 1

    def test_invite_unknown_user_raises(self, event_service, sample_event):
        with pytest.raises(ValueError):
            event_service.invite_participant(sample_event.id, "ghost")

    def test_invite_duplicate_returns_false(self, event_service, sample_event, sample_user2):
        event_service.invite_participant(sample_event.id, sample_user2.id)
        result = event_service.invite_participant(sample_event.id, sample_user2.id)
        assert result is False

    def test_remove_participant(self, event_service, sample_event, sample_user2):
        event_service.invite_participant(sample_event.id, sample_user2.id)
        result = event_service.remove_participant(sample_event.id, sample_user2.id)
        assert result is True
        assert sample_event.participant_count() == 0

    def test_set_rsvp(self, event_service, sample_event, sample_user2):
        event_service.invite_participant(sample_event.id, sample_user2.id)
        result = event_service.set_rsvp(sample_event.id, sample_user2.id, "yes")
        assert result is True

    def test_set_invalid_rsvp_raises(self, event_service, sample_event, sample_user2):
        with pytest.raises(ValueError):
            event_service.set_rsvp(sample_event.id, sample_user2.id, "maybe-later")


class TestEventServiceBudget:
    def test_add_budget_entry(self, event_service, sample_event):
        event_service.add_budget_entry(sample_event.id, "catering", 1000.0)
        assert len(sample_event.budget_entries) == 1

    def test_add_negative_budget_raises(self, event_service, sample_event):
        with pytest.raises(ValueError):
            event_service.add_budget_entry(sample_event.id, "catering", -100.0)

    def test_update_actual_cost(self, event_service, sample_event):
        event_service.add_budget_entry(sample_event.id, "catering", 1000.0)
        event_service.update_actual_cost(sample_event.id, "catering", 900.0)
        assert sample_event.total_actual_budget() == pytest.approx(900.0)

    def test_update_nonexistent_category_raises(self, event_service, sample_event):
        with pytest.raises(KeyError):
            event_service.update_actual_cost(sample_event.id, "ghost_cat", 100.0)

    def test_update_negative_actual_raises(self, event_service, sample_event):
        event_service.add_budget_entry(sample_event.id, "venue", 500.0)
        with pytest.raises(ValueError):
            event_service.update_actual_cost(sample_event.id, "venue", -10.0)


class TestEventServiceStatus:
    def test_transition_to_planned(self, event_service, sample_event):
        result = event_service.transition_status(sample_event.id, EventStatus.PLANNED)
        assert result.status == EventStatus.PLANNED

    def test_invalid_transition_raises(self, event_service, sample_event):
        with pytest.raises(ValueError):
            event_service.transition_status(sample_event.id, EventStatus.COMPLETED)


class TestEventServiceNotifications:
    def test_invite_sends_notification(self, event_service, sample_event, sample_user2, notification_service):
        event_service.invite_participant(sample_event.id, sample_user2.id)
        notifs = notification_service.get_notifications(sample_user2.id)
        assert any("invited" in n.message.lower() for n in notifs)

    def test_send_reminders(self, event_service, sample_event, sample_user2, notification_service):
        event_service.invite_participant(sample_event.id, sample_user2.id)
        count = event_service.send_reminders(sample_event.id)
        assert count == 1

    def test_get_events_by_organizer(self, event_service, sample_user):
        e1 = event_service.create_event("Event1", sample_user.id)
        e2 = event_service.create_event("Event2", sample_user.id)
        result = event_service.get_events_by_organizer(sample_user.id)
        assert len(result) >= 2

    def test_get_all_events(self, event_service, sample_user):
        event_service.create_event("A", sample_user.id)
        event_service.create_event("B", sample_user.id)
        all_events = event_service.get_all_events()
        assert len(all_events) >= 2
