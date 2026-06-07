from enum import Enum, auto


class EventType(Enum):
    HOLIDAY = "holiday"
    TRAVEL = "travel"
    MEETING = "meeting"
    BIRTHDAY = "birthday"
    CORPORATE = "corporate"
    OTHER = "other"


class EventStatus(Enum):
    DRAFT = "draft"
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    OVERDUE = "overdue"


class TaskPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class UserRole(Enum):
    ORGANIZER = "organizer"
    PARTICIPANT = "participant"
    VIEWER = "viewer"


class NotificationType(Enum):
    TASK_ASSIGNED = "task_assigned"
    TASK_OVERDUE = "task_overdue"
    EVENT_REMINDER = "event_reminder"
    EVENT_UPDATED = "event_updated"
    BUDGET_EXCEEDED = "budget_exceeded"
    INVITATION = "invitation"
