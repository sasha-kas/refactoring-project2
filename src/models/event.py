from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict
import uuid

from src.models.enums import EventType, EventStatus


@dataclass
class BudgetEntry:
    category: str
    planned: float
    actual: float = 0.0
    note: str = ""

    def variance(self) -> float:
        return self.actual - self.planned

    def is_over_budget(self) -> bool:
        return self.actual > self.planned


@dataclass
class EventParticipant:
    user_id: str
    role: str = "participant"
    joined_at: datetime = field(default_factory=datetime.now)
    rsvp: Optional[str] = None  # "yes", "no", "maybe"


@dataclass
class Event:
    title: str
    organizer_id: str
    event_type: EventType = EventType.OTHER
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    location: str = ""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: EventStatus = EventStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    total_budget: float = 0.0
    budget_entries: List[BudgetEntry] = field(default_factory=list)
    participants: List[EventParticipant] = field(default_factory=list)
    task_ids: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    max_participants: Optional[int] = None

    def __eq__(self, other):
        if not isinstance(other, Event):
            return False
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

    def __repr__(self):
        return f"Event(id={self.id[:8]}, title={self.title}, status={self.status.value})"

    def add_participant(self, user_id: str, role: str = "participant") -> bool:
        if self.max_participants and len(self.participants) >= self.max_participants:
            return False
        if any(p.user_id == user_id for p in self.participants):
            return False
        self.participants.append(EventParticipant(user_id=user_id, role=role))
        self._touch()
        return True

    def remove_participant(self, user_id: str) -> bool:
        before = len(self.participants)
        self.participants = [p for p in self.participants if p.user_id != user_id]
        if len(self.participants) < before:
            self._touch()
            return True
        return False

    def set_rsvp(self, user_id: str, rsvp: str) -> bool:
        for p in self.participants:
            if p.user_id == user_id:
                p.rsvp = rsvp
                self._touch()
                return True
        return False

    def add_task(self, task_id: str):
        if task_id not in self.task_ids:
            self.task_ids.append(task_id)
            self._touch()

    def remove_task(self, task_id: str):
        if task_id in self.task_ids:
            self.task_ids.remove(task_id)
            self._touch()

    def add_budget_entry(self, category: str, planned: float, note: str = ""):
        self.budget_entries.append(BudgetEntry(category=category, planned=planned, note=note))
        self._touch()

    def update_budget_actual(self, category: str, actual: float) -> bool:
        for entry in self.budget_entries:
            if entry.category == category:
                entry.actual = actual
                self._touch()
                return True
        return False

    def total_planned_budget(self) -> float:
        return sum(e.planned for e in self.budget_entries)

    def total_actual_budget(self) -> float:
        return sum(e.actual for e in self.budget_entries)

    def budget_utilization_percent(self) -> float:
        planned = self.total_planned_budget()
        if planned == 0:
            return 0.0
        return (self.total_actual_budget() / planned) * 100

    def is_over_budget(self) -> bool:
        return self.total_actual_budget() > self.total_planned_budget()

    def transition_to(self, new_status: EventStatus) -> bool:
        valid_transitions = {
            EventStatus.DRAFT: [EventStatus.PLANNED, EventStatus.CANCELLED],
            EventStatus.PLANNED: [EventStatus.IN_PROGRESS, EventStatus.CANCELLED],
            EventStatus.IN_PROGRESS: [EventStatus.COMPLETED, EventStatus.CANCELLED],
            EventStatus.COMPLETED: [],
            EventStatus.CANCELLED: [],
        }
        if new_status in valid_transitions.get(self.status, []):
            self.status = new_status
            self._touch()
            return True
        return False

    def duration_days(self) -> Optional[int]:
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days
        return None

    def participant_count(self) -> int:
        return len(self.participants)

    def _touch(self):
        self.updated_at = datetime.now()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "organizer_id": self.organizer_id,
            "event_type": self.event_type.value,
            "description": self.description,
            "location": self.location,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "status": self.status.value,
            "total_budget": self.total_budget,
            "total_planned": self.total_planned_budget(),
            "total_actual": self.total_actual_budget(),
            "participant_count": self.participant_count(),
            "task_count": len(self.task_ids),
            "tags": self.tags,
        }
