import pytest
from src.models.notification import Notification
from src.models.enums import NotificationType
from src.storage.repositories import InMemoryNotificationRepository
from src.services.user_service import NotificationService


@pytest.fixture
def repo():
    return InMemoryNotificationRepository()


@pytest.fixture
def svc(repo):
    return NotificationService(repo)


def make_notification(user_id="u1", read=False):
    n = Notification(user_id, NotificationType.INVITATION, "You are invited")
    if read:
        n.mark_read()
    return n


class TestNotificationService:
    def test_get_notifications(self, svc, repo):
        n = make_notification("u1")
        repo.save(n)
        result = svc.get_notifications("u1")
        assert n in result

    def test_get_unread(self, svc, repo):
        n_unread = make_notification("u1")
        n_read = make_notification("u1", read=True)
        repo.save(n_unread)
        repo.save(n_read)
        unread = svc.get_unread("u1")
        assert n_unread in unread
        assert n_read not in unread

    def test_mark_read(self, svc, repo):
        n = make_notification("u1")
        repo.save(n)
        svc.mark_read(n.id)
        assert n.is_read is True

    def test_mark_read_unknown_raises(self, svc):
        with pytest.raises(KeyError):
            svc.mark_read("ghost")

    def test_mark_all_read(self, svc, repo):
        for _ in range(3):
            repo.save(make_notification("u1"))
        count = svc.mark_all_read("u1")
        assert count == 3
        assert len(svc.get_unread("u1")) == 0

    def test_mark_all_read_other_user_not_affected(self, svc, repo):
        repo.save(make_notification("u1"))
        repo.save(make_notification("u2"))
        svc.mark_all_read("u1")
        assert len(svc.get_unread("u2")) == 1

    def test_count_unread(self, svc, repo):
        repo.save(make_notification("u1"))
        repo.save(make_notification("u1"))
        repo.save(make_notification("u1", read=True))
        assert svc.count_unread("u1") == 2

    def test_delete_notification(self, svc, repo):
        n = make_notification("u1")
        repo.save(n)
        result = svc.delete_notification(n.id)
        assert result is True
        assert len(svc.get_notifications("u1")) == 0
