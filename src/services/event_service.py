from typing import List, Optional
from datetime import datetime

from src.models.event import Event
from src.models.enums import EventType, EventStatus
from src.storage.repositories import InMemoryEventRepository, InMemoryUserRepository
from src.utils.observer import EventBus
from src.utils.strategies import IBudgetWarningStrategy, PercentageBudgetWarningStrategy


class EventService:
    def __init__(
        self,
        event_repo: InMemoryEventRepository,
        user_repo: InMemoryUserRepository,
        event_bus: EventBus,
        budget_warning_strategy: IBudgetWarningStrategy = None,
    ):
        self._event_repo = event_repo
        self._user_repo = user_repo
        self._bus = event_bus
        self._budget_strategy = budget_warning_strategy or PercentageBudgetWarningStrategy(80.0)

    def create_event(
        self,
        title: str,
        organizer_id: str,
        event_type: EventType = EventType.OTHER,
        description: str = "",
        location: str = "",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        total_budget: float = 0.0,
        max_participants: Optional[int] = None,
    ) -> Event:
        if not title or not title.strip():
            raise ValueError("Event title cannot be empty")
        if not self._user_repo.exists(organizer_id):
            raise ValueError(f"Organizer {organizer_id} not found")
        if start_date and end_date and end_date < start_date:
            raise ValueError("end_date must be after start_date")
        if total_budget < 0:
            raise ValueError("Budget cannot be negative")

        event = Event(
            title=title.strip(),
            organizer_id=organizer_id,
            event_type=event_type,
            description=description,
            location=location,
            start_date=start_date,
            end_date=end_date,
            total_budget=total_budget,
            max_participants=max_participants,
        )
        self._event_repo.save(event)
        return event

    def get_event(self, event_id: str) -> Event:
        event = self._event_repo.find_by_id(event_id)
        if not event:
            raise KeyError(f"Event {event_id} not found")
        return event

    def update_event(self, event_id: str, **kwargs) -> Event:
        event = self.get_event(event_id)
        allowed = {"title", "description", "location", "start_date", "end_date", "total_budget", "max_participants"}
        for key, val in kwargs.items():
            if key not in allowed:
                raise ValueError(f"Cannot update field: {key}")
            setattr(event, key, val)
        event._touch()
        self._event_repo.save(event)

        # notify all participants
        for p in event.participants:
            self._bus.publish("event_updated", {
                "user_id": p.user_id,
                "event_id": event.id,
                "event_title": event.title,
            })
        return event

    def transition_status(self, event_id: str, new_status: EventStatus) -> Event:
        event = self.get_event(event_id)
        if not event.transition_to(new_status):
            raise ValueError(
                f"Cannot transition event from {event.status.value} to {new_status.value}"
            )
        self._event_repo.save(event)
        return event

    def invite_participant(self, event_id: str, user_id: str) -> bool:
        event = self.get_event(event_id)
        if not self._user_repo.exists(user_id):
            raise ValueError(f"User {user_id} not found")
        added = event.add_participant(user_id)
        if added:
            self._event_repo.save(event)
            self._bus.publish("invitation", {
                "user_id": user_id,
                "event_id": event.id,
                "event_title": event.title,
            })
        return added

    def remove_participant(self, event_id: str, user_id: str) -> bool:
        event = self.get_event(event_id)
        removed = event.remove_participant(user_id)
        if removed:
            self._event_repo.save(event)
        return removed

    def set_rsvp(self, event_id: str, user_id: str, rsvp: str) -> bool:
        if rsvp not in ("yes", "no", "maybe"):
            raise ValueError("RSVP must be 'yes', 'no', or 'maybe'")
        event = self.get_event(event_id)
        return event.set_rsvp(user_id, rsvp)

    def add_budget_entry(self, event_id: str, category: str, planned: float, note: str = "") -> Event:
        if planned < 0:
            raise ValueError("Planned budget cannot be negative")
        event = self.get_event(event_id)
        event.add_budget_entry(category, planned, note)
        self._event_repo.save(event)
        return event

    def update_actual_cost(self, event_id: str, category: str, actual: float) -> Event:
        if actual < 0:
            raise ValueError("Actual cost cannot be negative")
        event = self.get_event(event_id)
        if not event.update_budget_actual(category, actual):
            raise KeyError(f"Budget category '{category}' not found")
        self._event_repo.save(event)

        if self._budget_strategy.is_warning(event):
            recipients = {event.organizer_id} | {p.user_id for p in event.participants}
            for uid in recipients:
                self._bus.publish("budget_exceeded", {
                    "user_id": uid,
                    "event_id": event.id,
                    "event_title": event.title,
                })
        return event

    def send_reminders(self, event_id: str) -> int:
        event = self.get_event(event_id)
        count = 0
        for p in event.participants:
            self._bus.publish("event_reminder", {
                "user_id": p.user_id,
                "event_id": event.id,
                "event_title": event.title,
            })
            count += 1
        return count

    def get_events_by_organizer(self, organizer_id: str) -> List[Event]:
        return self._event_repo.find_by_organizer(organizer_id)

    def get_events_by_status(self, status: EventStatus) -> List[Event]:
        return self._event_repo.find_by_status(status)

    def get_events_for_user(self, user_id: str) -> List[Event]:
        return self._event_repo.find_by_participant(user_id)

    def get_all_events(self) -> List[Event]:
        return self._event_repo.find_all()

    def delete_event(self, event_id: str) -> bool:
        return self._event_repo.delete(event_id)

    def set_budget_warning_strategy(self, strategy: IBudgetWarningStrategy):
        self._budget_strategy = strategy
