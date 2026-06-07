import pytest
from datetime import datetime, timedelta
from src.models.event import Event, BudgetEntry, EventParticipant
from src.models.enums import EventType, EventStatus


class TestEventCreation:
    def test_event_has_id(self):
        e = Event("Party", "org-1")
        assert e.id is not None

    def test_event_default_status(self):
        e = Event("Party", "org-1")
        assert e.status == EventStatus.DRAFT

    def test_event_default_type(self):
        e = Event("Party", "org-1")
        assert e.event_type == EventType.OTHER

    def test_event_no_participants_by_default(self):
        e = Event("Party", "org-1")
        assert len(e.participants) == 0

    def test_event_no_tasks_by_default(self):
        e = Event("Party", "org-1")
        assert len(e.task_ids) == 0

    def test_event_created_at(self):
        e = Event("Party", "org-1")
        assert isinstance(e.created_at, datetime)


class TestEventParticipants:
    def test_add_participant(self):
        e = Event("Party", "org-1")
        result = e.add_participant("user-1")
        assert result is True
        assert e.participant_count() == 1

    def test_add_duplicate_participant_fails(self):
        e = Event("Party", "org-1")
        e.add_participant("user-1")
        result = e.add_participant("user-1")
        assert result is False
        assert e.participant_count() == 1

    def test_remove_participant(self):
        e = Event("Party", "org-1")
        e.add_participant("user-1")
        result = e.remove_participant("user-1")
        assert result is True
        assert e.participant_count() == 0

    def test_remove_nonexistent_participant(self):
        e = Event("Party", "org-1")
        result = e.remove_participant("user-999")
        assert result is False

    def test_max_participants_respected(self):
        e = Event("Party", "org-1", max_participants=2)
        e.add_participant("user-1")
        e.add_participant("user-2")
        result = e.add_participant("user-3")
        assert result is False
        assert e.participant_count() == 2

    def test_set_rsvp_yes(self):
        e = Event("Party", "org-1")
        e.add_participant("user-1")
        result = e.set_rsvp("user-1", "yes")
        assert result is True

    def test_set_rsvp_no(self):
        e = Event("Party", "org-1")
        e.add_participant("user-1")
        e.set_rsvp("user-1", "no")
        assert e.participants[0].rsvp == "no"

    def test_set_rsvp_nonexistent_user(self):
        e = Event("Party", "org-1")
        result = e.set_rsvp("user-999", "yes")
        assert result is False


class TestEventBudget:
    def test_add_budget_entry(self):
        e = Event("Party", "org-1")
        e.add_budget_entry("catering", 1000.0)
        assert len(e.budget_entries) == 1

    def test_total_planned_budget(self):
        e = Event("Party", "org-1")
        e.add_budget_entry("catering", 1000.0)
        e.add_budget_entry("venue", 2000.0)
        assert e.total_planned_budget() == pytest.approx(3000.0)

    def test_total_actual_budget_initially_zero(self):
        e = Event("Party", "org-1")
        e.add_budget_entry("catering", 1000.0)
        assert e.total_actual_budget() == pytest.approx(0.0)

    def test_update_budget_actual(self):
        e = Event("Party", "org-1")
        e.add_budget_entry("catering", 1000.0)
        result = e.update_budget_actual("catering", 900.0)
        assert result is True
        assert e.total_actual_budget() == pytest.approx(900.0)

    def test_update_nonexistent_category(self):
        e = Event("Party", "org-1")
        result = e.update_budget_actual("decoration", 200.0)
        assert result is False

    def test_is_over_budget(self):
        e = Event("Party", "org-1")
        e.add_budget_entry("catering", 500.0)
        e.update_budget_actual("catering", 600.0)
        assert e.is_over_budget() is True

    def test_is_not_over_budget(self):
        e = Event("Party", "org-1")
        e.add_budget_entry("catering", 500.0)
        e.update_budget_actual("catering", 400.0)
        assert e.is_over_budget() is False

    def test_budget_utilization_percent(self):
        e = Event("Party", "org-1")
        e.add_budget_entry("catering", 1000.0)
        e.update_budget_actual("catering", 750.0)
        assert e.budget_utilization_percent() == pytest.approx(75.0)

    def test_budget_utilization_no_planned(self):
        e = Event("Party", "org-1")
        assert e.budget_utilization_percent() == pytest.approx(0.0)


class TestEventStatusTransitions:
    def test_draft_to_planned(self):
        e = Event("Party", "org-1")
        result = e.transition_to(EventStatus.PLANNED)
        assert result is True
        assert e.status == EventStatus.PLANNED

    def test_planned_to_in_progress(self):
        e = Event("Party", "org-1")
        e.transition_to(EventStatus.PLANNED)
        result = e.transition_to(EventStatus.IN_PROGRESS)
        assert result is True

    def test_in_progress_to_completed(self):
        e = Event("Party", "org-1")
        e.transition_to(EventStatus.PLANNED)
        e.transition_to(EventStatus.IN_PROGRESS)
        result = e.transition_to(EventStatus.COMPLETED)
        assert result is True

    def test_invalid_transition_draft_to_completed(self):
        e = Event("Party", "org-1")
        result = e.transition_to(EventStatus.COMPLETED)
        assert result is False
        assert e.status == EventStatus.DRAFT

    def test_completed_is_terminal(self):
        e = Event("Party", "org-1")
        e.transition_to(EventStatus.PLANNED)
        e.transition_to(EventStatus.IN_PROGRESS)
        e.transition_to(EventStatus.COMPLETED)
        result = e.transition_to(EventStatus.PLANNED)
        assert result is False

    def test_cancel_from_draft(self):
        e = Event("Party", "org-1")
        result = e.transition_to(EventStatus.CANCELLED)
        assert result is True

    def test_cancelled_is_terminal(self):
        e = Event("Party", "org-1")
        e.transition_to(EventStatus.CANCELLED)
        result = e.transition_to(EventStatus.PLANNED)
        assert result is False


class TestEventDuration:
    def test_duration_days(self):
        e = Event("Party", "org-1",
                  start_date=datetime(2025, 8, 1),
                  end_date=datetime(2025, 8, 5))
        assert e.duration_days() == 4

    def test_duration_no_dates(self):
        e = Event("Party", "org-1")
        assert e.duration_days() is None

    def test_duration_same_day(self):
        d = datetime(2025, 8, 1)
        e = Event("Party", "org-1", start_date=d, end_date=d)
        assert e.duration_days() == 0


class TestEventTasks:
    def test_add_task(self):
        e = Event("Party", "org-1")
        e.add_task("task-1")
        assert "task-1" in e.task_ids

    def test_add_duplicate_task_ignored(self):
        e = Event("Party", "org-1")
        e.add_task("task-1")
        e.add_task("task-1")
        assert e.task_ids.count("task-1") == 1

    def test_remove_task(self):
        e = Event("Party", "org-1")
        e.add_task("task-1")
        e.remove_task("task-1")
        assert "task-1" not in e.task_ids

    def test_to_dict_structure(self):
        e = Event("Party", "org-1")
        d = e.to_dict()
        assert "id" in d
        assert "title" in d
        assert "status" in d

    def test_repr(self):
        e = Event("Party", "org-1")
        assert "Party" in repr(e)


class TestBudgetEntry:
    def test_variance_positive(self):
        b = BudgetEntry("catering", 100.0, actual=120.0)
        assert b.variance() == pytest.approx(20.0)

    def test_variance_zero(self):
        b = BudgetEntry("catering", 100.0, actual=100.0)
        assert b.variance() == pytest.approx(0.0)

    def test_is_over_budget(self):
        b = BudgetEntry("catering", 100.0, actual=101.0)
        assert b.is_over_budget() is True

    def test_is_not_over_budget(self):
        b = BudgetEntry("catering", 100.0, actual=99.0)
        assert b.is_over_budget() is False
