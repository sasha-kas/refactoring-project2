"""
Strategy Pattern — різні алгоритми розрахунку балів відповідальності
та пріоритизації задач на дошці планування.
"""
from abc import ABC, abstractmethod
from typing import List
from src.models.task import Task
from src.models.event import Event


class ITaskPriorityStrategy(ABC):
    """Strategy for computing task priority score."""

    @abstractmethod
    def compute_score(self, task: Task) -> float:
        pass

    @abstractmethod
    def get_name(self) -> str:
        pass


class DeadlineBasedPriorityStrategy(ITaskPriorityStrategy):
    """Prioritize tasks closer to deadline."""

    def compute_score(self, task: Task) -> float:
        from datetime import datetime
        if task.due_date is None:
            return 0.0
        delta = (task.due_date - datetime.now()).total_seconds()
        if delta <= 0:
            return 1000.0  # Overdue — highest priority
        hours_left = delta / 3600
        return max(0.0, 100.0 - hours_left)

    def get_name(self) -> str:
        return "deadline_based"


class CostBasedPriorityStrategy(ITaskPriorityStrategy):
    """Prioritize tasks with highest estimated cost."""

    def compute_score(self, task: Task) -> float:
        return task.estimated_cost

    def get_name(self) -> str:
        return "cost_based"


class PriorityEnumStrategy(ITaskPriorityStrategy):
    """Prioritize by task's own priority enum value."""

    def compute_score(self, task: Task) -> float:
        return float(task.priority.value)

    def get_name(self) -> str:
        return "enum_priority"


class CompositePriorityStrategy(ITaskPriorityStrategy):
    """Combine multiple strategies with weights."""

    def __init__(self, strategies: List[tuple[ITaskPriorityStrategy, float]]):
        self._strategies = strategies  # list of (strategy, weight)

    def compute_score(self, task: Task) -> float:
        total_weight = sum(w for _, w in self._strategies)
        if total_weight == 0:
            return 0.0
        return sum(
            s.compute_score(task) * w for s, w in self._strategies
        ) / total_weight

    def get_name(self) -> str:
        names = [s.get_name() for s, _ in self._strategies]
        return f"composite({', '.join(names)})"


class IBudgetWarningStrategy(ABC):
    """Strategy for budget warning thresholds."""

    @abstractmethod
    def is_warning(self, event: Event) -> bool:
        pass

    @abstractmethod
    def warning_message(self, event: Event) -> str:
        pass


class PercentageBudgetWarningStrategy(IBudgetWarningStrategy):
    def __init__(self, threshold_percent: float = 80.0):
        self._threshold = threshold_percent

    def is_warning(self, event: Event) -> bool:
        return event.budget_utilization_percent() >= self._threshold

    def warning_message(self, event: Event) -> str:
        pct = event.budget_utilization_percent()
        return f"Budget utilization is {pct:.1f}% (threshold: {self._threshold}%)"


class AbsoluteBudgetWarningStrategy(IBudgetWarningStrategy):
    def __init__(self, max_overspend: float = 0.0):
        self._max_overspend = max_overspend

    def is_warning(self, event: Event) -> bool:
        variance = event.total_actual_budget() - event.total_planned_budget()
        return variance > self._max_overspend

    def warning_message(self, event: Event) -> str:
        variance = event.total_actual_budget() - event.total_planned_budget()
        return f"Budget overspend: {variance:.2f} (max allowed: {self._max_overspend:.2f})"
