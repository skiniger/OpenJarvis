from src.openjarvis.server.osint_store import OsintStore, get_store

class TestOsintStore:
    def setup_method(self):
        self.store = OsintStore()

    def test_save_and_list_scan(self):
        entry_id = self.store.save_scan(
            user_id="u1",
            target="example.com",
            modules=["dns", "whois"],
            results={"ip": "1.2.3.4"},
            summary={"errors": 0, "modules": 2},
        )
        assert isinstance(entry_id, str)

        history = self.store.list_history("u1")
        assert len(history) == 1
        entry = history[0]
        assert entry["type"] == "scan"
        assert entry["target"] == "example.com"
        assert entry["user_id"] == "u1"
        assert entry["results"] == {"ip": "1.2.3.4"}
        assert entry["success"] is True

    def test_save_and_list_exec(self):
        entry_id = self.store.save_exec(
            user_id="u1",
            tool_name="nmap",
            target="scanme.nmap.org",
            output="scan results",
            success=True,
            metadata={},
        )
        assert isinstance(entry_id, str)

        history = self.store.list_history("u1")
        assert len(history) == 1
        entry = history[0]
        assert entry["type"] == "exec"
        assert entry["tool_name"] == "nmap"
        assert entry["output"] == "scan results"

    def test_history_is_user_scoped(self):
        self.store.save_scan(user_id="alice", target="a.com", modules=[], results={}, summary={})
        self.store.save_scan(user_id="bob", target="b.com", modules=[], results={}, summary={})
        assert len(self.store.list_history("alice")) == 1
        assert len(self.store.list_history("bob")) == 1
        assert self.store.list_history("alice")[0]["target"] == "a.com"

    def test_delete_history(self):
        entry_id = self.store.save_scan(user_id="u1", target="x.com", modules=[], results={}, summary={})
        removed = self.store.delete_history_entry("u1", entry_id)
        assert removed is True
        assert len(self.store.list_history("u1")) == 0

    def test_delete_unknown_returns_false(self):
        removed = self.store.delete_history_entry("u1", "nonexistent")
        assert removed is False

    def test_toggle_favorite_adds(self):
        active = self.store.toggle_favorite("u1", "nmap")
        assert active is True
        assert self.store.list_favorites("u1") == ["nmap"]

    def test_toggle_favorite_removes(self):
        self.store.toggle_favorite("u1", "nmap")
        active = self.store.toggle_favorite("u1", "nmap")
        assert active is False
        assert self.store.list_favorites("u1") == []

    def test_favorites_are_user_scoped(self):
        self.store.toggle_favorite("alice", "nmap")
        self.store.toggle_favorite("bob", "amass")
        assert self.store.list_favorites("alice") == ["nmap"]
        assert self.store.list_favorites("bob") == ["amass"]

    def test_history_limit(self):
        for i in range(150):
            self.store.save_scan(user_id="u1", target=f"t{i}.com", modules=[], results={}, summary={})
        history = self.store.list_history("u1", limit=50)
        assert len(history) == 50

    def test_history_order_newest_first(self):
        for i in range(5):
            self.store.save_scan(user_id="u1", target=f"t{i}.com", modules=[], results={}, summary={})
        history = self.store.list_history("u1")
        assert len(history) == 5
        assert history[0]["target"] == "t4.com"
        assert history[-1]["target"] == "t0.com"

    def test_singleton_get_store(self):
        s1 = get_store()
        s2 = get_store()
        assert s1 is s2

    def test_clear_history(self):
        for i in range(3):
            self.store.save_scan(user_id="u1", target=f"t{i}.com", modules=[], results={}, summary={})
        removed = self.store.clear_history("u1")
        assert removed == 3
        assert len(self.store.list_history("u1")) == 0

    def test_dashboard_stats_empty(self):
        stats = self.store.get_dashboard_stats("u1")
        assert stats["total_scans"] == 0
        assert stats["total_execs"] == 0
        assert stats["total_actions"] == 0
        assert stats["unique_targets"] == 0
        assert stats["success_rate"] == 0.0
        assert len(stats["activity_timeline"]) == 30
        assert stats["activity_timeline"][0]["scans"] == 0

    def test_dashboard_stats_with_data(self):
        self.store.save_scan(
            user_id="u1",
            target="example.com",
            modules=["dns", "whois"],
            results={},
            summary={"errors": 0, "modules": 2},
        )
        self.store.save_scan(
            user_id="u1",
            target="example.com",
            modules=["dns"],
            results={},
            summary={"errors": 1, "modules": 1},
        )
        self.store.save_exec(
            user_id="u1",
            tool_name="nmap",
            target="example.com",
            output="ok",
            success=True,
            metadata={},
        )

        stats = self.store.get_dashboard_stats("u1")
        assert stats["total_scans"] == 2
        assert stats["total_execs"] == 1
        assert stats["total_actions"] == 3
        assert stats["unique_targets"] == 1
        assert stats["success_rate"] == 66.7
        assert len(stats["top_targets"]) == 1
        assert stats["top_targets"][0]["target"] == "example.com"
        assert stats["top_targets"][0]["count"] == 3
        assert len(stats["tool_usage"]) == 1
        assert stats["tool_usage"][0]["tool_name"] == "nmap"
        assert len(stats["module_usage"]) == 2

    def test_dashboard_stats_user_scoped(self):
        self.store.save_scan(user_id="alice", target="a.com", modules=[], results={}, summary={})
        self.store.save_scan(user_id="bob", target="b.com", modules=[], results={}, summary={})
        assert self.store.get_dashboard_stats("alice")["total_scans"] == 1
        assert self.store.get_dashboard_stats("bob")["total_scans"] == 1


class TestOsintStorePersistence:
    def test_save_and_reload(self, tmp_path):
        path = str(tmp_path / "osint.json")
        store = OsintStore(persist_path=path)
        store.save_scan("u1", "x.com", ["dns"], {"ip": "1.2.3.4"}, {"errors": 0})
        store.toggle_favorite("u1", "nmap")
        job = store.create_schedule("u1", "y.com", ["http"], 60)

        # Reload from disk
        store2 = OsintStore(persist_path=path)
        history = store2.list_history("u1")
        assert len(history) == 1
        assert history[0]["target"] == "x.com"
        assert store2.list_favorites("u1") == ["nmap"]
        schedules = store2.list_schedules("u1")
        assert len(schedules) == 1
        assert schedules[0]["target"] == "y.com"
        assert schedules[0]["id"] == job.id

    def test_delete_persists(self, tmp_path):
        path = str(tmp_path / "osint.json")
        store = OsintStore(persist_path=path)
        store.save_scan("u1", "x.com", ["dns"], {"ip": "1.2.3.4"}, {"errors": 0})
        entry_id = store.list_history("u1")[0]["id"]
        store.delete_history_entry("u1", entry_id)

        store2 = OsintStore(persist_path=path)
        assert len(store2.list_history("u1")) == 0

    def test_corrupt_file_ignored(self, tmp_path):
        path = tmp_path / "osint.json"
        path.write_text("not json")
        store = OsintStore(persist_path=str(path))
        assert len(store.list_history("u1")) == 0
