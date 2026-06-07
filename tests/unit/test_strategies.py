import pytest
from datetime import datetime, timedelta
from src.models.task import Task
from src.models.event import Event
from src.models.enums import TaskPriority
from src.utils.strategies import (
    DeadlineBasedPriorityStrategy,
    CostBasedPriorityStrategy,
    PriorityEnumStrategy,
    CompositePriorityStrategy,
    PercentageBudgetWarningStrategy,
    AbsoluteBudgetWarningStrategy,
)


class TestDeadlineBasedPriority:
    def test_overdue_task_highest_score(self):
        strat = DeadlineBasedPriorityStrategy()
        t = Task("T", "e")
        t.due_date = datetime.now() - timedelta(hours=1)
        assert strat.compute_score(t) == 1000.0

    def test_no_due_date_zero_score(self):
        strat = DeadlineBasedPriorityStrategy()
        t = Task("T", "e")
        assert strat.compute_score(t) == 0.0

    def test_future_task_lower_score_than_overdue(self):
        strat = DeadlineBasedPriorityStrategy()
        future = Task("T", "e")
        future.due_date = datetime.now() + timedelta(days=30)
        overdue = Task("T2", "e")
        overdue.due_date = datetime.now() - timedelta(hours=1)
        assert strat.compute_score(overdue) > strat.compute_score(future)

    def test_closer_deadline_higher_score(self):
        strat = DeadlineBasedPriorityStrategy()
        t1 = Task("Near", "e")
        t1.due_date = datetime.now() + timedelta(hours=1)
        t2 = Task("Far", "e")
        t2.due_date = datetime.now() + timedelta(days=10)
        assert strat.compute_score(t1) > strat.compute_score(t2)

    def test_name(self):
        assert DeadlineBasedPriorityStrategy().get_name() == "deadline_based"


class TestCostBasedPriority:
    def test_higher_cost_higher_score(self):
        strat = CostBasedPriorityStrategy()
        t1 = Task("Expensive", "e", estimated_cost=1000.0)
        t2 = Task("Cheap", "e", estimated_cost=50.0)
        assert strat.compute_score(t1) > strat.compute_score(t2)

    def test_zero_cost_zero_score(self):
        strat = CostBasedPriorityStrategy()
        t = Task("T", "e")
        assert strat.compute_score(t) == 0.0

    def test_name(self):
        assert CostBasedPriorityStrategy().get_name() == "cost_based"


class TestPriorityEnumStrategy:
    def test_critical_higher_than_low(self):
        strat = PriorityEnumStrategy()
        t_crit = Task("T", "e", priority=TaskPriority.CRITICAL)
        t_low = Task("T", "e", priority=TaskPriority.LOW)
        assert strat.compute_score(t_crit) > strat.compute_score(t_low)

    def test_name(self):
        assert PriorityEnumStrategy().get_name() == "enum_priority"


class TestCompositePriorityStrategy:
    def test_composite_combines_scores(self):
        s1 = CostBasedPriorityStrategy()
        s2 = PriorityEnumStrategy()
        composite = CompositePriorityStrategy([(s1, 1.0), (s2, 1.0)])
        t = Task("T", "e", estimated_cost=100.0, priority=TaskPriority.HIGH)
        score = composite.compute_score(t)
        expected = (100.0 + 3.0) / 2.0
        assert score == pytest.approx(expected)

    def test_zero_weight_returns_zero(self):
        composite = CompositePriorityStrategy([])
        t = Task("T", "e")
        assert composite.compute_score(t) == 0.0

    def test_name_contains_strategies(self):
        s1 = CostBasedPriorityStrategy()
        composite = CompositePriorityStrategy([(s1, 1.0)])
        assert "cost_based" in composite.get_name()


class TestPercentageBudgetWarning:
    def test_warning_when_over_threshold(self):
        strat = PercentageBudgetWarningStrategy(threshold_percent=80.0)
        e = Event("Party", "org-1")
        e.add_budget_entry("catering", 100.0)
        e.update_budget_actual("catering", 85.0)
        assert strat.is_warning(e) is True

    def test_no_warning_under_threshold(self):
        strat = PercentageBudgetWarningStrategy(threshold_percent=80.0)
        e = Event("Party", "org-1")
        e.add_budget_entry("catering", 100.0)
        e.update_budget_actual("catering", 70.0)
        assert strat.is_warning(e) is False

    def test_warning_message_contains_percent(self):
        strat = PercentageBudgetWarningStrategy(80.0)
        e = Event("Party", "org-1")
        e.add_budget_entry("catering", 100.0)
        e.update_budget_actual("catering", 85.0)
        msg = strat.warning_message(e)
        assert "85.0" in msg

    def test_no_budget_no_warning(self):
        strat = PercentageBudgetWarningStrategy(80.0)
        e = Event("Party", "org-1")
        assert strat.is_warning(e) is False


class TestAbsoluteBudgetWarning:
    def test_warning_when_overspent(self):
        strat = AbsoluteBudgetWarningStrategy(max_overspend=0.0)
        e = Event("Party", "org-1")
        e.add_budget_entry("catering", 100.0)
        e.update_budget_actual("catering", 101.0)
        assert strat.is_warning(e) is True

    def test_no_warning_within_budget(self):
        strat2 = AbsoluteBudgetWarningStrategy(max_overspend=50.0)
        e2 = Event("Party2", "org-1")
        e2.add_budget_entry("catering", 100.0)
        e2.update_budget_actual("catering", 130.0)
        # 130 - 100 = 30 which is NOT > 50
        assert strat2.is_warning(e2) is False

    def test_warning_message(self):
        strat = AbsoluteBudgetWarningStrategy(max_overspend=0.0)
        e = Event("Party", "org-1")
        e.add_budget_entry("catering", 100.0)
        e.update_budget_actual("catering", 150.0)
        msg = strat.warning_message(e)
        assert "50.00" in msg
