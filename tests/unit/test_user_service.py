import pytest
from src.models.enums import UserRole
from src.storage.repositories import InMemoryUserRepository
from src.services.user_service import UserService


@pytest.fixture
def repo():
    return InMemoryUserRepository()


@pytest.fixture
def svc(repo):
    return UserService(repo)


class TestUserServiceRegister:
    def test_register_basic(self, svc):
        u = svc.register("Alice", "alice@test.com")
        assert u.name == "Alice"
        assert u.email == "alice@test.com"

    def test_register_with_role(self, svc):
        u = svc.register("Alice", "alice@test.com", UserRole.ORGANIZER)
        assert u.role == UserRole.ORGANIZER

    def test_register_empty_name_raises(self, svc):
        with pytest.raises(ValueError):
            svc.register("", "a@b.com")

    def test_register_whitespace_name_raises(self, svc):
        with pytest.raises(ValueError):
            svc.register("   ", "a@b.com")

    def test_register_invalid_email_raises(self, svc):
        with pytest.raises(ValueError):
            svc.register("Alice", "not-an-email")

    def test_register_duplicate_email_raises(self, svc):
        svc.register("Alice", "alice@test.com")
        with pytest.raises(ValueError):
            svc.register("Bob", "alice@test.com")

    def test_register_strips_whitespace(self, svc):
        u = svc.register("  Alice  ", "alice@test.com")
        assert u.name == "Alice"

    def test_register_persists_to_repo(self, svc, repo):
        u = svc.register("Alice", "alice@test.com")
        assert repo.find_by_id(u.id) is not None


class TestUserServiceOperations:
    def test_get_user(self, svc):
        u = svc.register("Alice", "alice@test.com")
        found = svc.get_user(u.id)
        assert found == u

    def test_get_user_not_found_raises(self, svc):
        with pytest.raises(KeyError):
            svc.get_user("nonexistent")

    def test_deactivate_user(self, svc):
        u = svc.register("Alice", "alice@test.com")
        svc.deactivate(u.id)
        assert u.is_active is False

    def test_activate_user(self, svc):
        u = svc.register("Alice", "alice@test.com")
        svc.deactivate(u.id)
        svc.activate(u.id)
        assert u.is_active is True

    def test_promote_to_organizer(self, svc):
        u = svc.register("Alice", "alice@test.com")
        assert u.role == UserRole.PARTICIPANT
        svc.promote_to_organizer(u.id)
        assert u.role == UserRole.ORGANIZER

    def test_get_all_users(self, svc):
        svc.register("Alice", "alice@test.com")
        svc.register("Bob", "bob@test.com")
        all_users = svc.get_all_users()
        assert len(all_users) == 2

    def test_get_active_users(self, svc):
        u1 = svc.register("Alice", "alice@test.com")
        u2 = svc.register("Bob", "bob@test.com")
        svc.deactivate(u2.id)
        active = svc.get_active_users()
        assert u1 in active
        assert u2 not in active

    def test_delete_user(self, svc, repo):
        u = svc.register("Alice", "alice@test.com")
        result = svc.delete_user(u.id)
        assert result is True
        assert repo.find_by_id(u.id) is None

    def test_get_by_email(self, svc):
        u = svc.register("Alice", "alice@test.com")
        found = svc.get_by_email("alice@test.com")
        assert found == u

    def test_get_by_email_missing(self, svc):
        assert svc.get_by_email("missing@test.com") is None

    def test_register_with_phone(self, svc):
        u = svc.register("Alice", "alice@test.com", phone="+38099")
        assert u.phone == "+38099"
