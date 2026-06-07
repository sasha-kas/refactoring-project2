import pytest
from datetime import datetime, timedelta
from src.models.enums import TaskPriority, TaskStatus
from tests.conftest import *


class TestTaskServiceCreate:
    def test_create_basic_task(self, task_service, sample_event):
        t = task_service.create_task("Buy flowers", sample_event.id)
        assert t.title == "Buy flowers"
        assert t.event_id == sample_event.id

    def test_create_with_priority(self, task_service, sample_event):
        t = task_service.create_task("Urgent thing", sample_event.id, priority=TaskPriority.CRITICAL)
        assert t.priority == TaskPriority.CRITICAL

    def test_create_with_due_date(self, task_service, sample_event):
        due = datetime.now() + timedelta(days=5)
        t = task_service.create_task("Task", sample_event.id, due_date=due)
        assert t.due_date == due

    def test_create_with_assignee(self, task_service, sample_event, sample_user2):
        t = task_service.create_task("Task", sample_event.id, assignee_id=sample_user2.id)
        assert t.assignee_id == sample_user2.id
        assert t.status == TaskStatus.IN_PROGRESS

    def test_create_empty_title_raises(self, task_service, sample_event):
        with pytest.raises(ValueError):
            task_service.create_task("", sample_event.id)

    def test_create_unknown_event_raises(self, task_service):
        with pytest.raises(ValueError):
            task_service.create_task("Task", "ghost-event-id")

    def test_create_unknown_assignee_raises(self, task_service, sample_event):
        with pytest.raises(ValueError):
            task_service.create_task("Task", sample_event.id, assignee_id="ghost-user")

    def test_create_negative_cost_raises(self, task_service, sample_event):
        with pytest.raises(ValueError):
            task_service.create_task("Task", sample_event.id, estimated_cost=-1.0)

    def test_create_registers_in_event(self, task_service, sample_event):
        t = task_service.create_task("Task", sample_event.id)
        assert t.id in sample_event.task_ids

    def test_create_with_tags(self, task_service, sample_event):
        t = task_service.create_task("Task", sample_event.id, tags=["food", "urgent"])
        assert "food" in t.tags
        assert "urgent" in t.tags

    def test_create_strips_whitespace(self, task_service, sample_event):
        t = task_service.create_task("  Buy flowers  ", sample_event.id)
        assert t.title == "Buy flowers"


class TestTaskServiceAssignComplete:
    def test_assign_task(self, task_service, sample_task, sample_user2):
        task_service.assign_task(sample_task.id, sample_user2.id)
        assert sample_task.assignee_id == sample_user2.id

    def test_assign_unknown_user_raises(self, task_service, sample_task):
        with pytest.raises(ValueError):
            task_service.assign_task(sample_task.id, "ghost")

    def test_assign_unknown_task_raises(self, task_service, sample_user2):
        with pytest.raises(KeyError):
            task_service.assign_task("ghost-task", sample_user2.id)

    def test_complete_task(self, task_service, sample_task):
        task_service.complete_task(sample_task.id)
        assert sample_task.status == TaskStatus.DONE

    def test_complete_already_done_raises(self, task_service, sample_task):
        task_service.complete_task(sample_task.id)
        with pytest.raises(ValueError):
            task_service.complete_task(sample_task.id)

    def test_complete_unknown_task_raises(self, task_service):
        with pytest.raises(KeyError):
            task_service.complete_task("ghost")


class TestTaskServiceCostComments:
    def test_update_actual_cost(self, task_service, sample_task):
        task_service.update_task_cost(sample_task.id, 850.0)
        assert sample_task.actual_cost == pytest.approx(850.0)

    def test_update_negative_cost_raises(self, task_service, sample_task):
        with pytest.raises(ValueError):
            task_service.update_task_cost(sample_task.id, -10.0)

    def test_add_comment(self, task_service, sample_task):
        task_service.add_comment(sample_task.id, "Check the venue first")
        assert "Check the venue first" in sample_task.comments

    def test_add_empty_comment_raises(self, task_service, sample_task):
        with pytest.raises(ValueError):
            task_service.add_comment(sample_task.id, "")

    def test_add_whitespace_comment_raises(self, task_service, sample_task):
        with pytest.raises(ValueError):
            task_service.add_comment(sample_task.id, "   ")


class TestTaskServiceOverdue:
    def test_check_and_mark_overdue(self, task_service, sample_event):
        t = task_service.create_task(
            "Overdue task",
            sample_event.id,
            due_date=datetime.now() - timedelta(hours=2),
        )
        overdue = task_service.check_and_mark_overdue()
        assert t in overdue
        assert t.status == TaskStatus.OVERDUE

    def test_check_not_overdue_task_skipped(self, task_service, sample_event):
        t = task_service.create_task(
            "Future task",
            sample_event.id,
            due_date=datetime.now() + timedelta(days=5),
        )
        overdue = task_service.check_and_mark_overdue()
        assert t not in overdue


class TestTaskServiceProgress:
    def test_event_progress_all_pending(self, task_service, sample_event):
        task_service.create_task("T1", sample_event.id)
        task_service.create_task("T2", sample_event.id)
        progress = task_service.get_event_progress(sample_event.id)
        assert progress["total"] == 2
        assert progress["pending"] == 2
        assert progress["percent"] == 0.0

    def test_event_progress_all_done(self, task_service, sample_event):
        t1 = task_service.create_task("T1", sample_event.id)
        t2 = task_service.create_task("T2", sample_event.id)
        task_service.complete_task(t1.id)
        task_service.complete_task(t2.id)
        progress = task_service.get_event_progress(sample_event.id)
        assert progress["percent"] == 100.0

    def test_event_progress_empty_event(self, task_service, sample_event):
        # fresh sample_event has sample_task; test fresh event
        from src.services.event_service import EventService
        progress = task_service.get_event_progress("empty-event")
        assert progress["total"] == 0
        assert progress["percent"] == 0.0

    def test_get_sorted_by_priority(self, task_service, sample_event):
        t_low = task_service.create_task("Low", sample_event.id, priority=TaskPriority.LOW)
        t_high = task_service.create_task("High", sample_event.id, priority=TaskPriority.HIGH)
        from src.utils.strategies import PriorityEnumStrategy
        task_service.set_priority_strategy(PriorityEnumStrategy())
        sorted_tasks = task_service.get_sorted_by_priority(sample_event.id)
        scores = [t.priority.value for t in sorted_tasks]
        assert scores == sorted(scores, reverse=True)


class TestTaskServiceDelete:
    def test_delete_task(self, task_service, sample_task, sample_event):
        result = task_service.delete_task(sample_task.id)
        assert result is True
        assert sample_task.id not in sample_event.task_ids

    def test_delete_nonexistent_task(self, task_service):
        result = task_service.delete_task("ghost")
        assert result is False

    def test_get_unassigned_tasks(self, task_service, sample_event, sample_task):
        unassigned = task_service.get_unassigned_tasks()
        assert sample_task in unassigned

    def test_get_tasks_by_event(self, task_service, sample_event, sample_task):
        result = task_service.get_tasks_by_event(sample_event.id)
        assert sample_task in result
