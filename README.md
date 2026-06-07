# Event Planning Board

System for planning events: holidays, travel, responsibility distribution.

[![CI Pipeline](https://github.com/your-username/event-planning-board/actions/workflows/ci-pipeline.yml/badge.svg)](https://github.com/your-username/event-planning-board/actions/workflows/ci-pipeline.yml)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=event-planning-board&metric=alert_status)](https://sonarcloud.io/project/overview?id=event-planning-board)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=event-planning-board&metric=coverage)](https://sonarcloud.io/project/overview?id=event-planning-board)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)

---

## Repository structure

```
event-planning-board/
├── src/
│   ├── models/           # User, Event, Task, Notification, Enums
│   ├── services/         # EventService, TaskService, UserService, NotificationService
│   ├── storage/          # IRepository interface + InMemory implementations
│   └── utils/            # Strategy pattern, Observer / EventBus
├── tests/
│   ├── conftest.py       # Shared fixtures (shared_context, sample_user, ...)
│   ├── unit/             # 220+ unit tests
│   └── integration/      # 45+ integration tests (end-to-end scenarios)
├── docs/diagrams/
│   └── UML.md            # Use Case, Domain Model, Class, State diagrams
├── .cursor/rules/
│   ├── architecture.md   # AI architecture rules
│   └── testing.md        # AI test generation rules
├── .github/workflows/
│   └── ci-pipeline.yml   # GitHub Actions: build, test, coverage, SonarCloud
├── .cursorrules          # Global rules for AI agents
├── api.py                # HTTP server — serves board.html and REST API
├── board.html            # Kanban board UI (connects to api.py)
├── sonar-project.properties
├── Dockerfile
├── setup.cfg             # pytest + coverage configuration
└── requirements-dev.txt
```

---

## Running the project

### Requirements

- Python 3.12+
- pip

### Setup (once)

```bash
cd event-planning-board
python3 -m pip install -r requirements-dev.txt
```

### Run the board

```bash
python3 api.py
```

Open in browser: http://localhost:8000/board

The server loads all services, seeds demo data (3 events with tasks and participants),
and serves the Kanban board. Stop with Ctrl+C.

### Run tests

```bash
# All tests with coverage report
python3 -m pytest tests/ -v

# Unit tests only
python3 -m pytest tests/unit/ -v

# Integration scenarios only
python3 -m pytest tests/integration/ -v
```

### View HTML coverage report

```bash
python3 -m pytest tests/ -q
open htmlcov/index.html
```

### Docker

```bash
docker build -t epb .
docker run --rm epb
```

---

## Domain

**Actors:**
- `Organizer` — creates events, invites participants, assigns tasks, manages budget
- `Participant` — receives tasks, RSVPs, completes tasks

**Key use cases:**
1. Holiday planning — create event, invite guests, distribute tasks, track budget
2. Travel planning — book flights and hotels, manage budget by category, send reminders
3. Corporate event — distribute responsibilities across a team, track deadlines
4. Overdue detection — automatic check and notification for overdue tasks
5. Budget management — planned vs actual spending, threshold warnings

---

## Architecture

Layered In-Memory Architecture — no external databases or APIs.
All data lives in Python dicts during the process lifetime.

```
Services Layer  ->  IRepository (ABC)  ->  InMemory collections
                         |
                    EventBus (Observer)
                         |
               IEventObserver implementations
```

### Design patterns

| Pattern | Where applied |
|---------|---------------|
| Strategy | `ITaskPriorityStrategy` — 4 task sorting algorithms |
| Strategy | `IBudgetWarningStrategy` — 2 budget warning algorithms |
| Observer | `EventBus` + `IEventObserver` — notifications for all changes |

### SOLID

- **S** — each service is responsible for one entity
- **O** — new algorithms are added as new Strategy classes, existing code untouched
- **L** — all repositories are substitutable via `IRepository[T]`
- **I** — small focused interfaces: `IRepository`, `ITaskPriorityStrategy`, `IBudgetWarningStrategy`, `IEventObserver`
- **D** — services receive dependencies through constructor injection

---

## Testing

**Results:** 265 tests, 0 failures, 97% coverage (threshold: 70%)

Generated reports:
- `junit.xml` — for SonarQube / CI integration
- `coverage.xml` — for SonarCloud
- `htmlcov/index.html` — visual line-by-line coverage report

---

## CI/CD Pipeline

GitHub Actions (`.github/workflows/ci-pipeline.yml`):

```
push / PR  ->  build  ->  test & coverage  ->  upload artifacts  ->  SonarCloud scan
```

Artifacts saved after each run:
- `junit-test-report` — `junit.xml`
- `coverage-xml-report` — `coverage.xml`
- `coverage-html-report` — `htmlcov/index.html`

Branch protection: pull requests cannot be merged if the pipeline fails
or the SonarCloud Quality Gate is not passed (coverage below 70%).

### SonarCloud setup

1. Go to sonarcloud.io and create a project
2. Add `SONAR_TOKEN` to GitHub Secrets
3. Update `sonar-project.properties` with your `sonar.projectKey` and `sonar.organization`

---

## AI rules

`.cursorrules` and `.cursor/rules/` contain rules for Cursor, Claude, and Copilot:
- No external databases or APIs allowed
- Interfaces required before implementation
- TDD — tests written alongside code
- SOLID and GoF patterns enforced
- Details in `.cursor/rules/architecture.md` and `.cursor/rules/testing.md`

---

## UML diagrams

Full diagrams in `docs/diagrams/UML.md`:
- Use Case Diagram
- Domain Model
- Class Diagram (architecture)
- Event Status State Machine
