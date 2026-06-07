"""
Integration tests — end-to-end scenarios:
1. Організація свята
2. Планування подорожі
3. Розподіл обов'язків на корпоратив
"""
import pytest
from datetime import datetime, timedelta
from src.models.enums import EventType, EventStatus, TaskPriority, TaskStatus, UserRole


class TestHolidayPlanningScenario:
    """Scenario: Alice organizes a birthday party."""

    def test_full_holiday_flow(self, shared_context):
        user_service = shared_context["user_service"]
        event_service = shared_context["event_service"]
        task_service = shared_context["task_service"]
        notification_service = shared_context["notification_service"]

        alice = user_service.register("Alice", "alice@x.com", UserRole.ORGANIZER)
        bob = user_service.register("Bob", "bob@x.com")
        carol = user_service.register("Carol", "carol@x.com")

        party = event_service.create_event(
            "Alice Birthday Party",
            alice.id,
            EventType.HOLIDAY,
            total_budget=2000.0,
            start_date=datetime.now() + timedelta(days=14),
        )
        assert party.status == EventStatus.DRAFT

        event_service.add_budget_entry(party.id, "cake", 100.0)
        event_service.add_budget_entry(party.id, "venue", 500.0)
        event_service.add_budget_entry(party.id, "decorations", 200.0)
        assert party.total_planned_budget() == pytest.approx(800.0)

        event_service.invite_participant(party.id, bob.id)
        event_service.invite_participant(party.id, carol.id)
        assert party.participant_count() == 2

        event_service.set_rsvp(party.id, bob.id, "yes")
        event_service.set_rsvp(party.id, carol.id, "maybe")

        t_cake = task_service.create_task("Order cake", party.id, assignee_id=bob.id, estimated_cost=100.0)
        t_venue = task_service.create_task("Book venue", party.id, assignee_id=carol.id, estimated_cost=500.0)
        t_dec = task_service.create_task("Buy decorations", party.id, estimated_cost=200.0)

        assert t_cake.status == TaskStatus.IN_PROGRESS
        assert t_dec.status == TaskStatus.PENDING

        event_service.transition_status(party.id, EventStatus.PLANNED)
        assert party.status == EventStatus.PLANNED

        task_service.update_task_cost(t_cake.id, 95.0)
        task_service.complete_task(t_cake.id)
        task_service.update_task_cost(t_venue.id, 480.0)
        task_service.complete_task(t_venue.id)

        progress = task_service.get_event_progress(party.id)
        assert progress["done"] == 2
        assert progress["pending"] == 1

        bob_notifs = notification_service.get_notifications(bob.id)
        bob_types = [n.notification_type.value for n in bob_notifs]
        assert "invitation" in bob_types
        assert "task_assigned" in bob_types

        event_service.transition_status(party.id, EventStatus.IN_PROGRESS)
        task_service.complete_task(t_dec.id)
        event_service.transition_status(party.id, EventStatus.COMPLETED)
        assert party.status == EventStatus.COMPLETED

    def test_holiday_notification_count(self, shared_context):
        us = shared_context["user_service"]
        es = shared_context["event_service"]
        ts = shared_context["task_service"]
        ns = shared_context["notification_service"]

        org = us.register("Org", "org@x.com", UserRole.ORGANIZER)
        p1 = us.register("P1", "p1@x.com")
        p2 = us.register("P2", "p2@x.com")

        event = es.create_event("Test Event", org.id, EventType.HOLIDAY)
        es.invite_participant(event.id, p1.id)
        es.invite_participant(event.id, p2.id)

        ts.create_task("T1", event.id, assignee_id=p1.id)
        ts.create_task("T2", event.id, assignee_id=p2.id)

        assert ns.count_unread(p1.id) >= 2  # invitation + task_assigned
        assert ns.count_unread(p2.id) >= 2

    def test_rsvp_tracking(self, shared_context):
        us = shared_context["user_service"]
        es = shared_context["event_service"]

        org = us.register("Org", "org2@x.com", UserRole.ORGANIZER)
        p1 = us.register("P1", "pp1@x.com")
        p2 = us.register("P2", "pp2@x.com")
        p3 = us.register("P3", "pp3@x.com")

        event = es.create_event("RSVP Event", org.id)
        es.invite_participant(event.id, p1.id)
        es.invite_participant(event.id, p2.id)
        es.invite_participant(event.id, p3.id)

        es.set_rsvp(event.id, p1.id, "yes")
        es.set_rsvp(event.id, p2.id, "no")
        es.set_rsvp(event.id, p3.id, "maybe")

        rsvp_map = {p.user_id: p.rsvp for p in event.participants}
        assert rsvp_map[p1.id] == "yes"
        assert rsvp_map[p2.id] == "no"
        assert rsvp_map[p3.id] == "maybe"


class TestTravelPlanningScenario:
    """Scenario: Planning a group travel."""

    def test_travel_with_budget_warning(self, shared_context):
        user_service = shared_context["user_service"]
        event_service = shared_context["event_service"]
        task_service = shared_context["task_service"]
        notification_service = shared_context["notification_service"]

        organizer = user_service.register("Organizer", "org@x.com", UserRole.ORGANIZER)
        traveler = user_service.register("Traveler", "trav@x.com")

        trip = event_service.create_event(
            "European Trip",
            organizer.id,
            EventType.TRAVEL,
            start_date=datetime.now() + timedelta(days=60),
            end_date=datetime.now() + timedelta(days=74),
        )
        event_service.add_budget_entry(trip.id, "flights", 1500.0)
        event_service.invite_participant(trip.id, traveler.id)

        t_flights = task_service.create_task(
            "Book flights", trip.id, assignee_id=traveler.id, estimated_cost=1500.0,
            priority=TaskPriority.CRITICAL
        )
        t_hotels = task_service.create_task(
            "Book hotels", trip.id, assignee_id=traveler.id, estimated_cost=2000.0
        )

        # Overspend on flights — 1700/1500 = 113% > 80% threshold → budget warning
        event_service.update_actual_cost(trip.id, "flights", 1700.0)
        traveler_notifs = notification_service.get_notifications(traveler.id)
        notif_types = [n.notification_type.value for n in traveler_notifs]
        assert "budget_exceeded" in notif_types

        assert trip.duration_days() == 14

        from src.utils.strategies import PriorityEnumStrategy
        task_service.set_priority_strategy(PriorityEnumStrategy())
        sorted_tasks = task_service.get_sorted_by_priority(trip.id)
        assert sorted_tasks[0].id == t_flights.id

    def test_travel_full_lifecycle(self, shared_context):
        us = shared_context["user_service"]
        es = shared_context["event_service"]
        ts = shared_context["task_service"]

        org = us.register("TravelOrg", "torg@x.com", UserRole.ORGANIZER)
        trip = es.create_event("Japan Trip", org.id, EventType.TRAVEL,
                               start_date=datetime.now() + timedelta(days=90),
                               end_date=datetime.now() + timedelta(days=100))
        es.add_budget_entry(trip.id, "flights", 2000.0)
        es.add_budget_entry(trip.id, "hotels", 3000.0)
        es.add_budget_entry(trip.id, "food", 500.0)

        t1 = ts.create_task("Book flights", trip.id, priority=TaskPriority.CRITICAL, estimated_cost=2000.0)
        t2 = ts.create_task("Book hotels", trip.id, priority=TaskPriority.HIGH, estimated_cost=3000.0)
        t3 = ts.create_task("Plan itinerary", trip.id, priority=TaskPriority.MEDIUM)

        es.transition_status(trip.id, EventStatus.PLANNED)
        ts.complete_task(t1.id)
        ts.complete_task(t2.id)
        ts.complete_task(t3.id)

        progress = ts.get_event_progress(trip.id)
        assert progress["percent"] == pytest.approx(100.0)

        es.transition_status(trip.id, EventStatus.IN_PROGRESS)
        es.transition_status(trip.id, EventStatus.COMPLETED)
        assert trip.status == EventStatus.COMPLETED

    def test_travel_budget_multiple_categories(self, shared_context):
        us = shared_context["user_service"]
        es = shared_context["event_service"]

        org = us.register("Org3", "o3@x.com", UserRole.ORGANIZER)
        trip = es.create_event("Budget Trip", org.id, EventType.TRAVEL)
        es.add_budget_entry(trip.id, "transport", 500.0)
        es.add_budget_entry(trip.id, "accommodation", 800.0)
        es.add_budget_entry(trip.id, "food", 300.0)

        assert trip.total_planned_budget() == pytest.approx(1600.0)

        es.update_actual_cost(trip.id, "transport", 490.0)
        es.update_actual_cost(trip.id, "accommodation", 820.0)
        es.update_actual_cost(trip.id, "food", 280.0)

        assert trip.total_actual_budget() == pytest.approx(1590.0)
        assert trip.is_over_budget() is False


class TestResponsibilityDistributionScenario:
    """Scenario: Corporate event with responsibility distribution."""

    def test_corporate_responsibility_distribution(self, shared_context):
        user_service = shared_context["user_service"]
        event_service = shared_context["event_service"]
        task_service = shared_context["task_service"]
        notification_service = shared_context["notification_service"]

        manager = user_service.register("Manager", "mgr@corp.com", UserRole.ORGANIZER)
        emp1 = user_service.register("Employee1", "e1@corp.com")
        emp2 = user_service.register("Employee2", "e2@corp.com")
        emp3 = user_service.register("Employee3", "e3@corp.com")

        corp = event_service.create_event(
            "Corporate New Year Party", manager.id, EventType.CORPORATE, max_participants=50,
        )
        for emp in [emp1, emp2, emp3]:
            event_service.invite_participant(corp.id, emp.id)
        assert corp.participant_count() == 3

        tasks_data = [
            ("Catering arrangements", emp1.id, TaskPriority.HIGH, 3000.0),
            ("AV equipment setup", emp2.id, TaskPriority.HIGH, 1500.0),
            ("Venue decoration", emp3.id, TaskPriority.MEDIUM, 800.0),
            ("Guest invitations", emp1.id, TaskPriority.MEDIUM, 0.0),
            ("Entertainment booking", emp2.id, TaskPriority.CRITICAL, 2000.0),
        ]
        created_tasks = []
        for title, assignee, priority, cost in tasks_data:
            t = task_service.create_task(title, corp.id, assignee_id=assignee, priority=priority, estimated_cost=cost)
            created_tasks.append(t)

        assert len(task_service.get_tasks_by_assignee(emp1.id)) == 2
        assert len(task_service.get_tasks_by_assignee(emp2.id)) == 2
        assert len(task_service.get_tasks_by_assignee(emp3.id)) == 1

        task_service.complete_task(created_tasks[3].id)
        progress = task_service.get_event_progress(corp.id)
        assert progress["done"] == 1
        assert progress["total"] == 5

        created_tasks[0].due_date = datetime.now() - timedelta(hours=1)
        overdue_list = task_service.check_and_mark_overdue()
        assert len(overdue_list) >= 1

        emp1_notifs = notification_service.get_notifications(emp1.id)
        notif_types = [n.notification_type.value for n in emp1_notifs]
        assert "task_overdue" in notif_types

        count = notification_service.mark_all_read(emp1.id)
        assert count > 0
        assert notification_service.count_unread(emp1.id) == 0

    def test_unassigned_tasks_tracking(self, shared_context):
        us = shared_context["user_service"]
        es = shared_context["event_service"]
        ts = shared_context["task_service"]

        org = us.register("Org4", "o4@x.com", UserRole.ORGANIZER)
        event = es.create_event("Corp Event", org.id, EventType.CORPORATE)
        emp = us.register("Emp", "emp@x.com")
        es.invite_participant(event.id, emp.id)

        t1 = ts.create_task("Unassigned task", event.id)
        t2 = ts.create_task("Assigned task", event.id, assignee_id=emp.id)

        unassigned = ts.get_unassigned_tasks()
        assert t1 in unassigned
        assert t2 not in unassigned

    def test_task_comments_and_tags(self, shared_context):
        us = shared_context["user_service"]
        es = shared_context["event_service"]
        ts = shared_context["task_service"]

        org = us.register("Org5", "o5@x.com")
        event = es.create_event("Event5", org.id)
        task = ts.create_task("Tagged Task", event.id, tags=["important", "external"])

        ts.add_comment(task.id, "Confirmed with vendor")
        ts.add_comment(task.id, "Waiting for invoice")

        assert len(task.comments) == 2
        assert "important" in task.tags
        assert "external" in task.tags


class TestEventCancellationScenario:
    def test_cancel_event_and_verify_terminal(self, shared_context):
        us = shared_context["user_service"]
        es = shared_context["event_service"]

        user = us.register("Alice", "alice@x.com")
        event = es.create_event("Cancelled Party", user.id)
        es.transition_status(event.id, EventStatus.PLANNED)
        es.transition_status(event.id, EventStatus.CANCELLED)
        assert event.status == EventStatus.CANCELLED

        with pytest.raises(ValueError):
            es.transition_status(event.id, EventStatus.IN_PROGRESS)

    def test_update_event_notifies_participants(self, shared_context):
        us = shared_context["user_service"]
        es = shared_context["event_service"]
        ns = shared_context["notification_service"]

        org = us.register("Org6", "o6@x.com", UserRole.ORGANIZER)
        p = us.register("Guest", "guest@x.com")
        event = es.create_event("Event to update", org.id)
        es.invite_participant(event.id, p.id)

        es.update_event(event.id, title="Updated Event Title")
        notifs = ns.get_notifications(p.id)
        types = [n.notification_type.value for n in notifs]
        assert "event_updated" in types

    def test_send_reminders_to_all_participants(self, shared_context):
        us = shared_context["user_service"]
        es = shared_context["event_service"]
        ns = shared_context["notification_service"]

        org = us.register("Org7", "o7@x.com", UserRole.ORGANIZER)
        p1 = us.register("G1", "g1@x.com")
        p2 = us.register("G2", "g2@x.com")
        p3 = us.register("G3", "g3@x.com")
        event = es.create_event("Reminder Test", org.id)
        for p in [p1, p2, p3]:
            es.invite_participant(event.id, p.id)

        count = es.send_reminders(event.id)
        assert count == 3
        for p in [p1, p2, p3]:
            notifs = ns.get_notifications(p.id)
            types = [n.notification_type.value for n in notifs]
            assert "event_reminder" in types


class TestEdgeCases:
    def test_max_participants_enforced(self, shared_context):
        us = shared_context["user_service"]
        es = shared_context["event_service"]

        organizer = us.register("Org", "org@x.com")
        event = es.create_event("Small Party", organizer.id, max_participants=2)
        u1 = us.register("U1", "u1@x.com")
        u2 = us.register("U2", "u2@x.com")
        u3 = us.register("U3", "u3@x.com")
        es.invite_participant(event.id, u1.id)
        es.invite_participant(event.id, u2.id)
        result = es.invite_participant(event.id, u3.id)
        assert result is False
        assert event.participant_count() == 2

    def test_task_sorted_by_deadline(self, shared_context):
        us = shared_context["user_service"]
        es = shared_context["event_service"]
        ts = shared_context["task_service"]

        user = us.register("Alice", "alice@x.com")
        event = es.create_event("Event", user.id)
        t_near = ts.create_task("Near task", event.id, due_date=datetime.now() + timedelta(hours=2))
        t_far = ts.create_task("Far task", event.id, due_date=datetime.now() + timedelta(days=30))

        from src.utils.strategies import DeadlineBasedPriorityStrategy
        ts.set_priority_strategy(DeadlineBasedPriorityStrategy())
        sorted_tasks = ts.get_sorted_by_priority(event.id)
        assert sorted_tasks[0].id == t_near.id

    def test_zero_budget_utilization(self, shared_context):
        us = shared_context["user_service"]
        es = shared_context["event_service"]

        user = us.register("Alice", "alice@x.com")
        event = es.create_event("Event", user.id)
        assert event.budget_utilization_percent() == pytest.approx(0.0)

    def test_composite_priority_strategy(self, shared_context):
        us = shared_context["user_service"]
        es = shared_context["event_service"]
        ts = shared_context["task_service"]

        from src.utils.strategies import CompositePriorityStrategy, CostBasedPriorityStrategy, PriorityEnumStrategy
        user = us.register("Alice2", "alice2@x.com")
        event = es.create_event("Composite Test", user.id)

        t1 = ts.create_task("Costly", event.id, estimated_cost=5000.0, priority=TaskPriority.LOW)
        t2 = ts.create_task("Critical", event.id, estimated_cost=10.0, priority=TaskPriority.CRITICAL)

        composite = CompositePriorityStrategy([
            (CostBasedPriorityStrategy(), 1.0),
            (PriorityEnumStrategy(), 1.0),
        ])
        ts.set_priority_strategy(composite)
        sorted_tasks = ts.get_sorted_by_priority(event.id)
        # t1: (5000+1)/2=2500.5, t2: (10+4)/2=7 → t1 wins on cost
        assert sorted_tasks[0].id == t1.id

    def test_absolute_budget_strategy(self, shared_context):
        us = shared_context["user_service"]
        es = shared_context["event_service"]
        from src.utils.strategies import AbsoluteBudgetWarningStrategy

        org = us.register("AbsOrg", "abs@x.com", UserRole.ORGANIZER)
        event = es.create_event("AbsEvent", org.id)
        es.add_budget_entry(event.id, "misc", 1000.0)

        strat = AbsoluteBudgetWarningStrategy(max_overspend=100.0)
        es.set_budget_warning_strategy(strat)

        es.update_actual_cost(event.id, "misc", 1050.0)  # 50 over — no warning
        assert not strat.is_warning(event)

        es.update_actual_cost(event.id, "misc", 1200.0)  # 200 over — warning
        assert strat.is_warning(event)

    def test_delete_task_removes_from_event(self, shared_context):
        us = shared_context["user_service"]
        es = shared_context["event_service"]
        ts = shared_context["task_service"]

        user = us.register("Del", "del@x.com")
        event = es.create_event("DelEvent", user.id)
        task = ts.create_task("To delete", event.id)
        assert task.id in event.task_ids
        ts.delete_task(task.id)
        assert task.id not in event.task_ids
