import pytest
from datetime import datetime, timedelta
from src.models.task import Task
from src.models.enums import TaskStatus, TaskPriority


class TestTaskCreation:
    def test_task_has_id(self):
        t = Task("Buy flowers", "event-1")
        assert t.id is not None

    def test_task_default_status(self):
        t = Task("Buy flowers", "event-1")
        assert t.status == TaskStatus.PENDING

    def test_task_default_priority(self):
        t = Task("Buy flowers", "event-1")
        assert t.priority == TaskPriority.MEDIUM

    def test_task_default_cost(self):
        t = Task("Buy flowers", "event-1")
        assert t.estimated_cost == 0.0
        assert t.actual_cost == 0.0

    def test_task_created_at(self):
        t = Task("Buy flowers", "event-1")
        assert isinstance(t.created_at, datetime)

    def test_task_no_assignee_by_default(self):
        t = Task("Buy flowers", "event-1")
        assert t.assignee_id is None


class TestTaskBehavior:
    def test_assign_sets_assignee(self):
        t = Task("Buy flowers", "event-1")
        t.assign_to("user-1")
        assert t.assignee_id == "user-1"

    def test_assign_changes_status_to_in_progress(self):
        t = Task("Buy flowers", "event-1")
        t.assign_to("user-1")
        assert t.status == TaskStatus.IN_PROGRESS

    def test_complete_sets_done(self):
        t = Task("Buy flowers", "event-1")
        t.complete()
        assert t.status == TaskStatus.DONE

    def test_complete_sets_completed_at(self):
        t = Task("Buy flowers", "event-1")
        t.complete()
        assert t.completed_at is not None

    def test_mark_overdue(self):
        t = Task("Buy flowers", "event-1")
        t.mark_overdue()
        assert t.status == TaskStatus.OVERDUE

    def test_is_overdue_past_due_date(self):
        t = Task("Buy flowers", "event-1", due_date=datetime.now() - timedelta(hours=1))
        assert t.is_overdue() is True

    def test_is_overdue_future_due_date(self):
        t = Task("Buy flowers", "event-1", due_date=datetime.now() + timedelta(hours=1))
        assert t.is_overdue() is False

    def test_is_overdue_no_due_date(self):
        t = Task("Buy flowers", "event-1")
        assert t.is_overdue() is False

    def test_is_overdue_done_not_overdue(self):
        t = Task("Buy flowers", "event-1", due_date=datetime.now() - timedelta(hours=1))
        t.complete()
        assert t.is_overdue() is False

    def test_add_comment(self):
        t = Task("Buy flowers", "event-1")
        t.add_comment("First comment")
        assert "First comment" in t.comments

    def test_add_multiple_comments(self):
        t = Task("Buy flowers", "event-1")
        t.add_comment("First")
        t.add_comment("Second")
        assert len(t.comments) == 2

    def test_add_tag(self):
        t = Task("Buy flowers", "event-1")
        t.add_tag("urgent")
        assert "urgent" in t.tags

    def test_add_duplicate_tag_ignored(self):
        t = Task("Buy flowers", "event-1")
        t.add_tag("urgent")
        t.add_tag("urgent")
        assert t.tags.count("urgent") == 1

    def test_cost_variance_positive(self):
        t = Task("Buy flowers", "event-1", estimated_cost=100.0)
        t.actual_cost = 120.0
        assert t.cost_variance() == pytest.approx(20.0)

    def test_cost_variance_negative(self):
        t = Task("Buy flowers", "event-1", estimated_cost=100.0)
        t.actual_cost = 80.0
        assert t.cost_variance() == pytest.approx(-20.0)

    def test_cost_variance_zero(self):
        t = Task("Buy flowers", "event-1", estimated_cost=100.0)
        t.actual_cost = 100.0
        assert t.cost_variance() == pytest.approx(0.0)

    def test_equality_same_id(self):
        t = Task("Buy flowers", "event-1")
        import copy
        t2 = copy.copy(t)
        assert t == t2

    def test_inequality_different_tasks(self):
        t1 = Task("Task A", "event-1")
        t2 = Task("Task B", "event-1")
        assert t1 != t2

    def test_hash_consistency(self):
        t = Task("Buy flowers", "event-1")
        assert hash(t) == hash(t)

    def test_to_dict_keys(self):
        t = Task("Buy flowers", "event-1")
        d = t.to_dict()
        for k in ("id", "title", "event_id", "status", "priority"):
            assert k in d

    def test_repr_contains_title(self):
        t = Task("Buy flowers", "event-1")
        assert "Buy flowers" in repr(t)

    def test_assign_does_not_change_status_if_already_in_progress(self):
        t = Task("Buy flowers", "event-1")
        t.status = TaskStatus.IN_PROGRESS
        t.assign_to("user-2")
        assert t.status == TaskStatus.IN_PROGRESS
