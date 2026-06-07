# Testing Strategy — Event Planning Board

## Framework & Tools
- **pytest** — test runner
- **pytest-cov** — coverage measurement
- **Coverage target**: ≥70% (currently ~97%)
- **Reports**: `junit.xml` (CI integration), `htmlcov/` (visual HTML), `coverage.xml` (SonarCloud)

## Test Structure

```
tests/
├── conftest.py              — shared fixtures for ALL tests
├── unit/
│   ├── test_user_model.py
│   ├── test_task_model.py
│   ├── test_event_model.py
│   ├── test_repositories.py
│   ├── test_user_service.py
│   ├── test_event_service.py
│   ├── test_task_service.py
│   ├── test_strategies.py
│   ├── test_observer.py
│   └── test_notification_service.py
└── integration/
    └── test_scenarios.py    — full end-to-end scenarios
```

## Fixture Guidelines for AI Agents

### Unit tests — use per-layer fixtures:
```python
def test_something(event_service, sample_user, sample_event):
    ...
```

### Integration tests — ALWAYS use shared_context:
```python
def test_full_flow(self, shared_context):
    us = shared_context["user_service"]
    es = shared_context["event_service"]
    ts = shared_context["task_service"]
    ns = shared_context["notification_service"]
```
**Reason**: All services share the same EventBus instance → notifications work correctly.
Using individual `event_service` + `notification_service` fixtures will NOT share the bus.

## Test Naming Convention
```
test_<method>_<scenario>_<expected>
test_create_task_with_empty_title_raises_value_error
test_invite_participant_when_full_returns_false
```

## What to Test

### Models
- Default field values
- State transitions (Task.complete(), Event.transition_to())
- Edge: equality, hash, repr, to_dict keys

### Repositories
- save/find_by_id round-trip
- find_all, delete, exists, count
- Specialized queries (find_by_status, find_by_organizer)

### Services
- Happy path for each public method
- ValueError for invalid inputs (empty strings, negative costs)
- KeyError for missing entities
- Side effects (EventBus publishing, status changes)

### Strategies
- Each strategy produces correct score ordering
- Boundary: zero cost, no due_date, exact threshold

### Observer / EventBus
- subscribe → publish → observer receives event
- Duplicate subscription ignored
- Unknown event type → no crash

## Running Tests Locally

```bash
# All tests with coverage
python -m pytest tests/ -v

# Unit only
python -m pytest tests/unit/ -v

# Integration only
python -m pytest tests/integration/ -v

# Specific test
python -m pytest tests/unit/test_event_service.py::TestEventServiceCreate -v

# Open HTML coverage report
open htmlcov/index.html
```

## CI Artifacts

After each pipeline run, download from GitHub Actions:
- `junit-test-report` → `junit.xml`
- `coverage-xml-report` → `coverage.xml`
- `coverage-html-report` → `htmlcov/index.html`
