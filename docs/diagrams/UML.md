# UML Diagrams — Event Planning Board

## 1. Use Case Diagram

```
                    ┌─────────────────────────────────────────────────┐
                    │            Event Planning Board System           │
                    │                                                   │
  ┌──────────┐      │  ○ Create Event                                  │
  │          │──────│──○ Invite Participant                            │
  │Organizer │      │  ○ Add Budget Entry / Update Actual Cost         │
  │          │──────│──○ Assign Task to Participant                    │
  └──────────┘      │  ○ Transition Event Status                       │
       │            │  ○ Send Reminders                                │
       │            │  ○ Set Budget Warning Strategy                   │
       │            │                                                   │
  ┌────▼─────┐      │  ○ View Own Tasks                                │
  │          │──────│──○ Complete Task                                 │
  │Participant│     │  ○ RSVP to Event                                 │
  │          │──────│──○ Add Comment to Task                           │
  └──────────┘      │  ○ View Notifications                            │
                    │  ○ Mark Notifications Read                       │
                    │                                                   │
  ┌──────────┐      │  ○ Check Overdue Tasks (scheduled)               │
  │  System  │──────│──○ Publish EventBus notifications                │
  │(Scheduler)      │                                                   │
  └──────────┘      └─────────────────────────────────────────────────┘
```

---

## 2. Domain Model

```
┌──────────────┐         ┌──────────────────┐        ┌───────────────┐
│     User     │         │      Event        │        │     Task      │
│──────────────│         │──────────────────│        │───────────────│
│ id: str      │  1    * │ id: str          │  1   * │ id: str       │
│ name: str    │◄────────│ organizer_id: str│───────►│ event_id: str │
│ email: str   │         │ title: str        │        │ title: str    │
│ role: UserRole│        │ event_type: Enum  │        │ assignee_id   │
│ is_active    │         │ status: Enum      │        │ status: Enum  │
└──────┬───────┘         │ start_date        │        │ priority:Enum │
       │                 │ end_date          │        │ due_date      │
       │ participates    │ budget_entries[]  │        │ estimated_cost│
       │                 │ participants[]    │        │ actual_cost   │
       │         ┌───────┤ task_ids[]        │        │ tags[]        │
       │         │       └──────────────────┘        │ comments[]    │
       │         │                                    └───────────────┘
       │         │
       │  ┌──────▼──────────┐     ┌──────────────────┐
       │  │ EventParticipant│     │   BudgetEntry    │
       │  │─────────────────│     │──────────────────│
       │  │ user_id: str    │     │ category: str    │
       │  │ role: str       │     │ planned: float   │
       │  │ rsvp: str       │     │ actual: float    │
       │  └─────────────────┘     │ note: str        │
       │                          └──────────────────┘
       │
  ┌────▼──────────┐
  │ Notification  │
  │───────────────│
  │ id: str       │
  │ recipient_id  │
  │ type: Enum    │
  │ message: str  │
  │ is_read: bool │
  └───────────────┘
```

---

## 3. Class Diagram (Architecture)

```
«interface»                      «interface»
IRepository[T]                   IEventObserver
───────────────                  ───────────────
+save(T): T                      +on_event(type, payload)
+find_by_id(id): T?                     ▲
+find_all(): [T]                ┌───────┴────────┐
+delete(id): bool       NotificationObserver  LoggingObserver
+exists(id): bool
        ▲
┌───────┴──────────────┐
│InMemoryUserRepository│
│InMemoryEventRepository
│InMemoryTaskRepository│
│InMemoryNotif...Repo  │
└──────────────────────┘

«interface»                          EventBus
ITaskPriorityStrategy           ─────────────────
──────────────────              +subscribe(type, obs)
+compute_score(Task): float     +subscribe_all(obs)
+get_name(): str                +publish(type, payload)
        ▲                       +unsubscribe(...)
┌───────┴──────────┐
│DeadlineBased...  │
│CostBased...      │
│PriorityEnum...   │
│Composite...      │

«interface»
IBudgetWarningStrategy          Services
──────────────────────     ──────────────────
+is_warning(Event): bool   EventService
+warning_message(): str    TaskService
        ▲                  UserService
┌───────┴──────┐           NotificationService
│Percentage... │
│Absolute...   │
```

---

## 4. Event Status State Machine

```
  ┌────────┐   transition_to(PLANNED)    ┌─────────┐
  │ DRAFT  │──────────────────────────►  │ PLANNED │
  └────┬───┘                             └────┬────┘
       │                                      │ transition_to(IN_PROGRESS)
       │ transition_to                        ▼
       │    (CANCELLED)             ┌─────────────────┐
       │                            │   IN_PROGRESS   │
       ▼                            └────────┬────────┘
  ┌───────────┐ ◄──────────────────────────  │
  │ CANCELLED │   transition_to(CANCELLED)   │ transition_to(COMPLETED)
  └───────────┘                              ▼
                                     ┌───────────────┐
                                     │   COMPLETED   │
                                     └───────────────┘
```
