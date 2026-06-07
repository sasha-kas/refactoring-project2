from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid

from src.models.enums import NotificationType


@dataclass
class Notification:
    recipient_id: str
    notification_type: NotificationType
    message: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    related_event_id: Optional[str] = None
    related_task_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    is_read: bool = False

    def mark_read(self):
        self.is_read = True

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "recipient_id": self.recipient_id,
            "type": self.notification_type.value,
            "message": self.message,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat(),
            "related_event_id": self.related_event_id,
            "related_task_id": self.related_task_id,
        }
