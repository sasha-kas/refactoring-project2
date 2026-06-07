from typing import List, Optional
from src.models.user import User
from src.models.notification import Notification
from src.models.enums import UserRole
from src.storage.repositories import InMemoryUserRepository, InMemoryNotificationRepository


class UserService:
    def __init__(self, user_repo: InMemoryUserRepository):
        self._repo = user_repo

    def register(self, name: str, email: str, role: UserRole = UserRole.PARTICIPANT, phone: Optional[str] = None) -> User:
        if not name or not name.strip():
            raise ValueError("Name cannot be empty")
        if not email or "@" not in email:
            raise ValueError("Invalid email address")
        if self._repo.find_by_email(email):
            raise ValueError(f"Email {email} is already registered")

        user = User(name=name.strip(), email=email.strip(), role=role, phone=phone)
        self._repo.save(user)
        return user

    def get_user(self, user_id: str) -> User:
        user = self._repo.find_by_id(user_id)
        if not user:
            raise KeyError(f"User {user_id} not found")
        return user

    def get_by_email(self, email: str) -> Optional[User]:
        return self._repo.find_by_email(email)

    def deactivate(self, user_id: str) -> User:
        user = self.get_user(user_id)
        user.deactivate()
        self._repo.save(user)
        return user

    def activate(self, user_id: str) -> User:
        user = self.get_user(user_id)
        user.activate()
        self._repo.save(user)
        return user

    def promote_to_organizer(self, user_id: str) -> User:
        user = self.get_user(user_id)
        user.promote_to_organizer()
        self._repo.save(user)
        return user

    def get_all_users(self) -> List[User]:
        return self._repo.find_all()

    def get_active_users(self) -> List[User]:
        return self._repo.find_active()

    def delete_user(self, user_id: str) -> bool:
        return self._repo.delete(user_id)


class NotificationService:
    def __init__(self, notification_repo: InMemoryNotificationRepository):
        self._repo = notification_repo

    def get_notifications(self, user_id: str) -> List[Notification]:
        return self._repo.find_by_recipient(user_id)

    def get_unread(self, user_id: str) -> List[Notification]:
        return self._repo.find_unread(user_id)

    def mark_read(self, notification_id: str) -> Notification:
        n = self._repo.find_by_id(notification_id)
        if not n:
            raise KeyError(f"Notification {notification_id} not found")
        n.mark_read()
        self._repo.save(n)
        return n

    def mark_all_read(self, user_id: str) -> int:
        unread = self._repo.find_unread(user_id)
        for n in unread:
            n.mark_read()
            self._repo.save(n)
        return len(unread)

    def delete_notification(self, notification_id: str) -> bool:
        return self._repo.delete(notification_id)

    def count_unread(self, user_id: str) -> int:
        return len(self._repo.find_unread(user_id))
