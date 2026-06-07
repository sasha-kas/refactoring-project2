from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid

from src.models.enums import UserRole


@dataclass
class User:
    name: str
    email: str
    role: UserRole = UserRole.PARTICIPANT
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    phone: Optional[str] = None

    def __eq__(self, other):
        if not isinstance(other, User):
            return False
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

    def __repr__(self):
        return f"User(id={self.id[:8]}, name={self.name}, role={self.role.value})"

    def deactivate(self):
        self.is_active = False

    def activate(self):
        self.is_active = True

    def promote_to_organizer(self):
        self.role = UserRole.ORGANIZER

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role.value,
            "is_active": self.is_active,
            "phone": self.phone,
            "created_at": self.created_at.isoformat(),
        }
