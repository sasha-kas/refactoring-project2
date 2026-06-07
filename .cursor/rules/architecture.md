# Architecture — Event Planning Board

## Overview

This project uses a **Layered In-Memory Architecture** with no external databases or APIs.
All data lives in Python dicts during process lifetime.

## Layers

```
┌─────────────────────────────────────────┐
│              Services Layer             │
│  EventService  TaskService  UserService │
│         NotificationService             │
└────────────────┬────────────────────────┘
                 │ depends on interfaces
┌────────────────▼────────────────────────┐
│             Storage Layer               │
│  IRepository[T]  (ABC interface)        │
│  InMemoryUserRepository                 │
│  InMemoryEventRepository                │
│  InMemoryTaskRepository                 │
│  InMemoryNotificationRepository         │
└────────────────┬────────────────────────┘
                 │ stores
┌────────────────▼────────────────────────┐
│              Models Layer               │
│  User  Event  Task  Notification        │
│  Enums: EventType, TaskStatus, ...      │
└─────────────────────────────────────────┘
```

## Design Patterns

### Strategy Pattern
- **ITaskPriorityStrategy** — pluggable algorithms for task prioritization:
  - `DeadlineBasedPriorityStrategy` — ranks by proximity to due_date
  - `CostBasedPriorityStrategy` — ranks by estimated_cost
  - `PriorityEnumStrategy` — ranks by TaskPriority enum value
  - `CompositePriorityStrategy` — weighted combination of strategies
- **IBudgetWarningStrategy** — pluggable budget threshold algorithms:
  - `PercentageBudgetWarningStrategy` — warns when utilization % ≥ threshold
  - `AbsoluteBudgetWarningStrategy` — warns when overspend > max_overspend

### Observer Pattern
- **IEventObserver** — all observers implement `on_event(event_type, payload)`
- **EventBus** — central dispatcher; supports per-type and global subscriptions
- **NotificationObserver** — creates Notification entities in the repo
- **LoggingObserver** — logs all events to an in-memory list (useful for tests)

## Key Invariants

1. `InMemoryXxxRepository` is the ONLY storage mechanism
2. Services receive repos and EventBus via constructor injection
3. Status transitions are validated via `Event.transition_to()`
4. Budget warnings fire via EventBus — services never call notification repo directly
5. `shared_context` fixture in conftest ensures bus and repos are shared in tests

## Adding New Features

1. Define model fields in `src/models/`
2. Add repository method to `InMemoryXxxRepository`
3. Add business logic to corresponding Service
4. Add Strategy/Observer if behavior is pluggable
5. Write unit tests, then integration test in `test_scenarios.py`
