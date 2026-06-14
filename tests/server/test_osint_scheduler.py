import pytest
from datetime import datetime, timedelta, timezone
from src.openjarvis.server.osint_store import OsintStore

class TestOsintScheduler:
    def setup_method(self):
        self.store = OsintStore()

    def test_create_and_list_schedule(self):
        job = self.store.create_schedule(
            user_id="u1",
            target="example.com",
            modules=["dns", "whois"],
            interval_minutes=60,
        )
        assert job.target == "example.com"
        assert job.modules == ["dns", "whois"]
        assert job.interval_minutes == 60
        assert job.enabled is True
        assert job.next_run is not None

        schedules = self.store.list_schedules("u1")
        assert len(schedules) == 1
        assert schedules[0]["target"] == "example.com"

    def test_delete_schedule(self):
        job = self.store.create_schedule("u1", "x.com", ["dns"], 30)
        removed = self.store.delete_schedule("u1", job.id)
        assert removed is True
        assert len(self.store.list_schedules("u1")) == 0

    def test_delete_unknown_returns_false(self):
        removed = self.store.delete_schedule("u1", "nonexistent")
        assert removed is False

    def test_toggle_schedule(self):
        job = self.store.create_schedule("u1", "x.com", ["dns"], 30)
        status = self.store.toggle_schedule("u1", job.id)
        assert status is False
        status = self.store.toggle_schedule("u1", job.id)
        assert status is True

    def test_schedule_user_scoped(self):
        self.store.create_schedule("alice", "a.com", ["dns"], 30)
        self.store.create_schedule("bob", "b.com", ["whois"], 60)
        assert len(self.store.list_schedules("alice")) == 1
        assert len(self.store.list_schedules("bob")) == 1

    def test_tick_skips_disabled(self):
        job = self.store.create_schedule("u1", "example.com", ["dns"], 30)
        self.store.toggle_schedule("u1", job.id)
        executed = self.store._tick()
        assert len(executed) == 0

    def test_tick_executes_due_job(self):
        job = self.store.create_schedule("u1", "example.com", ["dns"], 30)
        # Force next_run to the past so it fires immediately
        past = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
        job.next_run = past

        executed = self.store._tick()
        assert len(executed) == 1
        assert executed[0]["schedule_id"] == job.id
        assert executed[0]["success"] is True

        # next_run should be updated to the future
        assert job.last_run is not None
        next_run = datetime.fromisoformat(job.next_run)
        assert next_run > datetime.now(timezone.utc)

        # History should contain the auto-scan
        history = self.store.list_history("u1")
        assert len(history) == 1
        assert history[0]["type"] == "scan"
        assert history[0]["target"] == "example.com"
