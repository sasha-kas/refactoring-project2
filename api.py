"""
Простий HTTP API для дошки планування подій.
Запуск: python3 api.py
Дошка: http://localhost:8000/board
"""
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs

from src.models.enums import EventType, EventStatus, TaskPriority, TaskStatus, UserRole
from src.storage.repositories import (
    InMemoryUserRepository, InMemoryEventRepository,
    InMemoryTaskRepository, InMemoryNotificationRepository,
)
from src.services.event_service import EventService
from src.services.task_service import TaskService
from src.services.user_service import UserService, NotificationService
from src.utils.observer import EventBus, NotificationObserver

# ── Bootstrap ─────────────────────────────────────────────────────────────────
user_repo   = InMemoryUserRepository()
event_repo  = InMemoryEventRepository()
task_repo   = InMemoryTaskRepository()
notif_repo  = InMemoryNotificationRepository()
bus         = EventBus()
bus.subscribe_all(NotificationObserver(notif_repo))

user_svc    = UserService(user_repo)
event_svc   = EventService(event_repo, user_repo, bus)
task_svc    = TaskService(task_repo, event_repo, user_repo, bus)
notif_svc   = NotificationService(notif_repo)

# ── Seed data ─────────────────────────────────────────────────────────────────
def seed():
    alice  = user_svc.register("Аліса",   "alice@example.com",  UserRole.ORGANIZER)
    bob    = user_svc.register("Боб",     "bob@example.com")
    carol  = user_svc.register("Карол",   "carol@example.com")
    oleg   = user_svc.register("Олег",    "oleg@example.com",   UserRole.ORGANIZER)
    marina = user_svc.register("Марина",  "marina@example.com")
    mgr    = user_svc.register("Менеджер","mgr@example.com",    UserRole.ORGANIZER)
    iryna  = user_svc.register("Ірина",   "iryna@example.com")
    serhiy = user_svc.register("Сергій",  "serhiy@example.com")

    # Подія 1 — свято
    party = event_svc.create_event(
        "День народження Аліси", alice.id, EventType.HOLIDAY,
        location="Ресторан Panorama",
        start_date=datetime.now() + timedelta(days=14),
        end_date=datetime.now()   + timedelta(days=14, hours=4),
        total_budget=8500.0,
    )
    event_svc.add_budget_entry(party.id, "Торт",  1500.0)
    event_svc.add_budget_entry(party.id, "Зала",  5000.0)
    event_svc.add_budget_entry(party.id, "Декор", 2000.0)
    for u, rsvp in [(bob,"yes"),(carol,"maybe")]:
        event_svc.invite_participant(party.id, u.id)
        event_svc.set_rsvp(party.id, u.id, rsvp)
    event_svc.update_actual_cost(party.id, "Торт", 1400.0)
    event_svc.update_actual_cost(party.id, "Зала", 5200.0)
    event_svc.update_actual_cost(party.id, "Декор", 1800.0)
    event_svc.transition_status(party.id, EventStatus.PLANNED)
    event_svc.transition_status(party.id, EventStatus.IN_PROGRESS)

    t1 = task_svc.create_task("Замовити торт",       party.id, assignee_id=bob.id,   priority=TaskPriority.HIGH,     estimated_cost=1500.0, due_date=datetime.now()+timedelta(days=3))
    t2 = task_svc.create_task("Забронювати залу",     party.id, assignee_id=alice.id, priority=TaskPriority.CRITICAL, estimated_cost=5000.0, due_date=datetime.now()-timedelta(days=2))
    t3 = task_svc.create_task("Купити декор",         party.id, assignee_id=carol.id, priority=TaskPriority.MEDIUM,   estimated_cost=2000.0, due_date=datetime.now()+timedelta(days=5))
    t4 = task_svc.create_task("Надіслати запрошення", party.id, assignee_id=alice.id, priority=TaskPriority.HIGH,     estimated_cost=0.0)
    t5 = task_svc.create_task("Скласти меню",         party.id,                       priority=TaskPriority.MEDIUM,   estimated_cost=0.0)
    t6 = task_svc.create_task("Музичне оформлення",   party.id, assignee_id=bob.id,   priority=TaskPriority.LOW,      estimated_cost=800.0,  due_date=datetime.now()-timedelta(days=5))
    task_svc.complete_task(t2.id)
    task_svc.complete_task(t4.id)
    task_svc.check_and_mark_overdue()

    # Подія 2 — подорож
    trip = event_svc.create_event(
        "Подорож до Відня", oleg.id, EventType.TRAVEL,
        location="Відень, Австрія",
        start_date=datetime.now() + timedelta(days=60),
        end_date=datetime.now()   + timedelta(days=74),
        total_budget=38000.0,
    )
    event_svc.add_budget_entry(trip.id, "Авіаквитки", 12000.0)
    event_svc.add_budget_entry(trip.id, "Готель",     18000.0)
    event_svc.add_budget_entry(trip.id, "Харчування",  5000.0)
    event_svc.add_budget_entry(trip.id, "Екскурсії",   3000.0)
    event_svc.invite_participant(trip.id, marina.id)
    event_svc.set_rsvp(trip.id, marina.id, "yes")
    event_svc.update_actual_cost(trip.id, "Авіаквитки", 12500.0)
    event_svc.update_actual_cost(trip.id, "Готель",     17000.0)
    event_svc.update_actual_cost(trip.id, "Харчування",  2100.0)
    event_svc.transition_status(trip.id, EventStatus.PLANNED)

    ta = task_svc.create_task("Купити авіаквитки",  trip.id, assignee_id=oleg.id,   priority=TaskPriority.CRITICAL, estimated_cost=12000.0, due_date=datetime.now()-timedelta(days=10))
    tb = task_svc.create_task("Забронювати готель", trip.id, assignee_id=marina.id, priority=TaskPriority.HIGH,     estimated_cost=18000.0, due_date=datetime.now()+timedelta(days=5))
    tc = task_svc.create_task("Оформити страховку", trip.id, assignee_id=marina.id, priority=TaskPriority.HIGH,     estimated_cost=600.0,   due_date=datetime.now()+timedelta(days=10))
    td = task_svc.create_task("Скласти маршрут",   trip.id,                         priority=TaskPriority.MEDIUM,   estimated_cost=0.0,     due_date=datetime.now()+timedelta(days=15))
    task_svc.complete_task(ta.id)
    task_svc.complete_task(tb.id)

    # Подія 3 — корпоратив
    corp = event_svc.create_event(
        "Корпоратив компанії", mgr.id, EventType.CORPORATE,
        location="Конференц-зала, 4 поверх",
        start_date=datetime.now() + timedelta(days=30),
        total_budget=50000.0,
    )
    event_svc.add_budget_entry(corp.id, "Кейтеринг", 25000.0)
    event_svc.add_budget_entry(corp.id, "Розваги",   15000.0)
    event_svc.add_budget_entry(corp.id, "Нагороди",  10000.0)
    for u in [iryna, serhiy]:
        event_svc.invite_participant(corp.id, u.id)
        event_svc.set_rsvp(corp.id, u.id, "yes")
    event_svc.update_actual_cost(corp.id, "Розваги",  8000.0)
    event_svc.update_actual_cost(corp.id, "Нагороди", 9500.0)

    te = task_svc.create_task("Замовити кейтеринг",     corp.id, assignee_id=iryna.id,  priority=TaskPriority.HIGH,     estimated_cost=25000.0, due_date=datetime.now()+timedelta(days=20))
    tf = task_svc.create_task("Організувати конкурси",  corp.id, assignee_id=serhiy.id, priority=TaskPriority.MEDIUM,   estimated_cost=8000.0,  due_date=datetime.now()+timedelta(days=22))
    tg = task_svc.create_task("Підготувати нагороди",   corp.id, assignee_id=iryna.id,  priority=TaskPriority.HIGH,     estimated_cost=9500.0,  due_date=datetime.now()+timedelta(days=23))
    th = task_svc.create_task("Розіслати запрошення",   corp.id, assignee_id=mgr.id,    priority=TaskPriority.CRITICAL, estimated_cost=0.0,     due_date=datetime.now()-timedelta(days=5))
    task_svc.check_and_mark_overdue()

seed()

# ── Serializers ───────────────────────────────────────────────────────────────
def serialize_task(t):
    return {
        "id": t.id,
        "title": t.title,
        "status": t.status.value,
        "priority": t.priority.value,
        "assignee_id": t.assignee_id,
        "assignee_name": user_repo.find_by_id(t.assignee_id).name if t.assignee_id else None,
        "estimated_cost": t.estimated_cost,
        "actual_cost": t.actual_cost,
        "due_date": t.due_date.strftime("%Y-%m-%d") if t.due_date else None,
        "tags": t.tags,
        "comments": t.comments,
    }

def serialize_event(e):
    tasks = task_repo.find_by_event(e.id)
    participants = []
    for p in e.participants:
        u = user_repo.find_by_id(p.user_id)
        if u:
            participants.append({
                "user_id": u.id,
                "name": u.name,
                "initials": "".join(w[0].upper() for w in u.name.split()[:2]),
                "rsvp": p.rsvp,
            })
    return {
        "id": e.id,
        "title": e.title,
        "type": e.event_type.value,
        "status": e.status.value,
        "location": e.location,
        "start_date": e.start_date.strftime("%Y-%m-%d") if e.start_date else None,
        "end_date":   e.end_date.strftime("%Y-%m-%d")   if e.end_date   else None,
        "total_budget": e.total_budget,
        "total_planned": e.total_planned_budget(),
        "total_actual":  e.total_actual_budget(),
        "budget_entries": [
            {"cat": b.category, "planned": b.planned, "actual": b.actual}
            for b in e.budget_entries
        ],
        "participants": participants,
        "tasks": [serialize_task(t) for t in tasks],
        "progress": task_svc.get_event_progress(e.id),
    }

# ── Request handler ───────────────────────────────────────────────────────────
class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"  {self.address_string()} {fmt % args}")

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False, indent=2).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def send_html(self, path):
        try:
            with open(path, "rb") as f:
                body = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", len(body))
            self.end_headers()
            self.wfile.write(body)
        except FileNotFoundError:
            self.send_error(404, "Not Found")

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path in ("", "/board"):
            self.send_html("board.html")
        elif path == "/api/events":
            self.send_json([serialize_event(e) for e in event_repo.find_all()])
        elif path.startswith("/api/events/"):
            eid = path.split("/")[-1]
            e = event_repo.find_by_id(eid)
            self.send_json(serialize_event(e) if e else {"error": "not found"}, 200 if e else 404)
        elif path == "/api/users":
            self.send_json([u.to_dict() for u in user_repo.find_all()])
        elif path == "/api/notifications":
            qs = parse_qs(parsed.query)
            uid = qs.get("user_id", [None])[0]
            notifs = notif_repo.find_by_recipient(uid) if uid else notif_repo.find_all()
            self.send_json([n.to_dict() for n in notifs])
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        try:
            if path == "/api/tasks/complete":
                t = task_svc.complete_task(body["task_id"])
                self.send_json(serialize_task(t))

            elif path == "/api/tasks/assign":
                t = task_svc.assign_task(body["task_id"], body["user_id"])
                self.send_json(serialize_task(t))

            elif path == "/api/tasks":
                ev_obj = event_repo.find_by_id(body["event_id"])
                if not ev_obj:
                    self.send_json({"error": "event not found"}, 404); return
                t = task_svc.create_task(
                    title=body["title"],
                    event_id=body["event_id"],
                    priority=TaskPriority[body.get("priority", "MEDIUM").upper()],
                    estimated_cost=float(body.get("estimated_cost", 0)),
                )
                self.send_json(serialize_task(t))

            elif path == "/api/tasks/comment":
                t = task_svc.add_comment(body["task_id"], body["comment"])
                self.send_json(serialize_task(t))

            elif path == "/api/events/invite":
                result = event_svc.invite_participant(body["event_id"], body["user_id"])
                self.send_json({"added": result})

            elif path == "/api/events/rsvp":
                result = event_svc.set_rsvp(body["event_id"], body["user_id"], body["rsvp"])
                self.send_json({"ok": result})

            elif path == "/api/check-overdue":
                overdue = task_svc.check_and_mark_overdue()
                self.send_json({"marked": len(overdue), "tasks": [t.id for t in overdue]})

            else:
                self.send_error(404, "Not Found")

        except (KeyError, ValueError) as e:
            self.send_json({"error": str(e)}, 400)


if __name__ == "__main__":
    HOST, PORT = "localhost", 8000
    print(f"\n🚀  Event Planning Board API")
    print(f"   Дошка:  http://{HOST}:{PORT}/board")
    print(f"   Events: http://{HOST}:{PORT}/api/events")
    print(f"   Users:  http://{HOST}:{PORT}/api/users\n")
    HTTPServer((HOST, PORT), Handler).serve_forever()
