import pytest
from src.models.user import User
from src.models.enums import UserRole


class TestUserCreation:
    def test_user_has_id(self):
        u = User("Alice", "a@b.com")
        assert u.id is not None
        assert len(u.id) > 0

    def test_user_unique_ids(self):
        u1 = User("Alice", "a@b.com")
        u2 = User("Bob", "b@b.com")
        assert u1.id != u2.id

    def test_user_default_role(self):
        u = User("Alice", "a@b.com")
        assert u.role == UserRole.PARTICIPANT

    def test_user_is_active_by_default(self):
        u = User("Alice", "a@b.com")
        assert u.is_active is True

    def test_user_with_phone(self):
        u = User("Alice", "a@b.com", phone="+380991234567")
        assert u.phone == "+380991234567"

    def test_user_organizer_role(self):
        u = User("Alice", "a@b.com", role=UserRole.ORGANIZER)
        assert u.role == UserRole.ORGANIZER

    def test_user_created_at_set(self):
        from datetime import datetime
        u = User("Alice", "a@b.com")
        assert isinstance(u.created_at, datetime)


class TestUserBehavior:
    def test_deactivate_user(self):
        u = User("Alice", "a@b.com")
        u.deactivate()
        assert u.is_active is False

    def test_activate_user(self):
        u = User("Alice", "a@b.com")
        u.deactivate()
        u.activate()
        assert u.is_active is True

    def test_promote_to_organizer(self):
        u = User("Alice", "a@b.com")
        assert u.role == UserRole.PARTICIPANT
        u.promote_to_organizer()
        assert u.role == UserRole.ORGANIZER

    def test_equality_same_id(self):
        u = User("Alice", "a@b.com")
        u2 = User.__new__(User)
        u2.__dict__.update(u.__dict__)
        assert u == u2

    def test_inequality_different_users(self):
        u1 = User("Alice", "a@b.com")
        u2 = User("Bob", "b@b.com")
        assert u1 != u2

    def test_hash_consistency(self):
        u = User("Alice", "a@b.com")
        assert hash(u) == hash(u)

    def test_repr_contains_name(self):
        u = User("Alice", "a@b.com")
        assert "Alice" in repr(u)

    def test_to_dict_keys(self):
        u = User("Alice", "a@b.com")
        d = u.to_dict()
        for key in ("id", "name", "email", "role", "is_active"):
            assert key in d

    def test_to_dict_role_is_string(self):
        u = User("Alice", "a@b.com", role=UserRole.ORGANIZER)
        d = u.to_dict()
        assert d["role"] == "organizer"

    def test_user_not_equal_to_non_user(self):
        u = User("Alice", "a@b.com")
        assert u != "not a user"
        assert u != 42
        assert u != None
