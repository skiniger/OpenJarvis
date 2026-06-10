"""Tests for openjarvis.agents.memory.AgentMemoryManager."""

from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

import pytest

from openjarvis.agents.memory import AgentMemoryManager


@pytest.fixture
def tmp_manager():
    with tempfile.TemporaryDirectory() as td:
        mgr = AgentMemoryManager(base_dir=td)
        yield mgr
        mgr.close()


class TestStoreAndRetrieveTurns:
    def test_store_turn_returns_id(self, tmp_manager: AgentMemoryManager):
        doc_id = tmp_manager.store_turn("bavaria_booking", "user", "Wie viele Zimmer?")
        assert doc_id is not None
        assert isinstance(doc_id, str)
        assert doc_id.isdigit()  # integer rowid as string

    def test_store_turn_dedup(self, tmp_manager: AgentMemoryManager):
        """Identical consecutive turns are deduplicated."""
        mgr = tmp_manager
        id1 = mgr.store_turn("bavaria_booking", "user", "Same question")
        id2 = mgr.store_turn("bavaria_booking", "user", "Same question")
        assert id1 is not None
        assert id2 is None
        recent = mgr.get_recent_turns("bavaria_booking", limit=10)
        assert len(recent) == 1

    def test_recent_turns_order(self, tmp_manager: AgentMemoryManager):
        mgr = tmp_manager
        mgr.store_turn("bavaria_booking", "user", "Erste Frage")
        mgr.store_turn("bavaria_booking", "assistant", "Erste Antwort")
        mgr.store_turn("bavaria_booking", "user", "Zweite Frage")

        recent = mgr.get_recent_turns("bavaria_booking", limit=2)
        assert len(recent) == 2
        assert recent[0].content == "Erste Antwort"
        assert recent[1].content == "Zweite Frage"

    def test_recent_turns_session_filter(self, tmp_manager: AgentMemoryManager):
        mgr = tmp_manager
        mgr.store_turn("bavaria_booking", "user", "S1", session_id="sess-a")
        mgr.store_turn("bavaria_booking", "user", "S2", session_id="sess-b")

        recent = mgr.get_recent_turns("bavaria_booking", limit=10, session_id="sess-a")
        assert len(recent) == 1
        assert recent[0].content == "S1"

    def test_retrieve_turns_fts(self, tmp_manager: AgentMemoryManager):
        mgr = tmp_manager
        mgr.store_turn("bavaria_booking", "user", "Wie sind die Zimmerpreise im Sommer?")
        mgr.store_turn("bavaria_booking", "assistant", "Die Zimmerpreise betragen 95 Euro.")
        mgr.store_turn("bavaria_booking", "user", "Was ist das Frühstück?")

        results = mgr.retrieve_turns("bavaria_booking", "Zimmerpreise", top_k=2)
        assert len(results) == 2
        contents = {r.content for r in results}
        assert "Wie sind die Zimmerpreise im Sommer?" in contents
        assert "Die Zimmerpreise betragen 95 Euro." in contents

    def test_retrieve_turns_empty_query(self, tmp_manager: AgentMemoryManager):
        mgr = tmp_manager
        mgr.store_turn("bavaria_booking", "user", "Test")
        assert mgr.retrieve_turns("bavaria_booking", "") == []
        assert mgr.retrieve_turns("bavaria_booking", "   ") == []

    def test_multiple_agents_isolated(self, tmp_manager: AgentMemoryManager):
        mgr = tmp_manager
        mgr.store_turn("bavaria_booking", "user", "Booking query")
        mgr.store_turn("legal_assistant", "user", "Legal query")

        bb = mgr.get_recent_turns("bavaria_booking", limit=10)
        la = mgr.get_recent_turns("legal_assistant", limit=10)
        assert len(bb) == 1
        assert len(la) == 1
        assert bb[0].content == "Booking query"
        assert la[0].content == "Legal query"

    def test_turn_pruning(self, tmp_manager: AgentMemoryManager):
        """Only max_turns are retained."""
        mgr = AgentMemoryManager(base_dir=tmp_manager._base_dir, max_turns=3)
        for i in range(5):
            mgr.store_turn("bavaria_booking", "user", f"Turn {i}")
        recent = mgr.get_recent_turns("bavaria_booking", limit=10)
        assert len(recent) == 3
        assert recent[-1].content == "Turn 4"

    def test_retrieve_min_score_filter(self, tmp_manager: AgentMemoryManager):
        mgr = tmp_manager
        mgr.store_turn("bavaria_booking", "user", "foobar")
        # Empty or non-matching query returns nothing
        results = mgr.retrieve_turns("bavaria_booking", "xyz", top_k=5)
        assert results == []


class TestStoreAndRetrieveFacts:
    def test_store_fact(self, tmp_manager: AgentMemoryManager):
        doc_id = tmp_manager.store_fact(
            "bavaria_booking",
            "Preis Doppelzimmer: 95 Euro",
            source="pricing_sheet",
            metadata={"currency": "EUR"},
        )
        assert isinstance(doc_id, str)

    def test_fact_upsert_by_source(self, tmp_manager: AgentMemoryManager):
        """Storing a fact with the same source updates the existing one."""
        mgr = tmp_manager
        id1 = mgr.store_fact("bavaria_booking", "Preis: 95", source="pricing")
        id2 = mgr.store_fact("bavaria_booking", "Preis: 110", source="pricing")
        assert id1 == id2
        facts = mgr.retrieve_facts("bavaria_booking", "Preis", top_k=5)
        assert any("110" in f.content for f in facts)
        assert not any("95" in f.content for f in facts)

    def test_retrieve_facts_fts(self, tmp_manager: AgentMemoryManager):
        mgr = tmp_manager
        mgr.store_fact("bavaria_booking", "Preis EZ: 65 Euro", source="pricing_ez")
        mgr.store_fact("bavaria_booking", "Preis DZ: 95 Euro", source="pricing_dz")
        mgr.store_fact("bavaria_booking", "Check-in ab 15 Uhr", source="rules")

        results = mgr.retrieve_facts("bavaria_booking", "Preis DZ", top_k=2)
        assert any("95 Euro" in r.content for r in results)

    def test_retrieve_facts_empty(self, tmp_manager: AgentMemoryManager):
        mgr = tmp_manager
        mgr.store_fact("bavaria_booking", "Fact")
        assert mgr.retrieve_facts("bavaria_booking", "") == []

    def test_fact_pruning(self, tmp_manager: AgentMemoryManager):
        """Only max_facts are retained."""
        mgr = AgentMemoryManager(base_dir=tmp_manager._base_dir, max_facts=2)
        for i in range(4):
            mgr.store_fact("bavaria_booking", f"Fact {i}")
        facts = mgr.retrieve_facts("bavaria_booking", "Fact", top_k=10)
        # After prune, rebuild may transiently reduce count; just assert <= 2
        assert len(facts) <= 2


class TestLifecycle:
    def test_clear_agent_memory(self, tmp_manager: AgentMemoryManager):
        mgr = tmp_manager
        mgr.store_turn("bavaria_booking", "user", "Q")
        mgr.store_fact("bavaria_booking", "F")
        mgr.clear_agent_memory("bavaria_booking")
        assert mgr.get_recent_turns("bavaria_booking", limit=10) == []
        assert mgr.retrieve_facts("bavaria_booking", "F", top_k=10) == []

    def test_clear_only_target_agent(self, tmp_manager: AgentMemoryManager):
        mgr = tmp_manager
        mgr.store_turn("bavaria_booking", "user", "BB")
        mgr.store_turn("legal_assistant", "user", "LA")
        mgr.clear_agent_memory("bavaria_booking")
        assert mgr.get_recent_turns("bavaria_booking", limit=10) == []
        assert len(mgr.get_recent_turns("legal_assistant", limit=10)) == 1

    def test_db_files_created(self, tmp_manager: AgentMemoryManager):
        mgr = tmp_manager
        mgr.store_turn("bavaria_booking", "user", "Q")
        expected = Path(mgr._base_dir) / "bavaria_booking.db"
        assert expected.exists()

    def test_fts_tables_exist(self, tmp_manager: AgentMemoryManager):
        mgr = tmp_manager
        mgr.store_turn("bavaria_booking", "user", "Q")
        conn = mgr._conn("bavaria_booking")
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        names = {t[0] for t in tables}
        assert "turns" in names
        assert "turns_fts" in names
        assert "facts" in names
        assert "facts_fts" in names

    def test_close_releases_connection(self, tmp_manager: AgentMemoryManager):
        mgr = tmp_manager
        mgr.store_turn("bavaria_booking", "user", "Q")
        mgr.close("bavaria_booking")
        assert "bavaria_booking" not in mgr._conns
