"""Per-agent persistent memory layer.

Wraps lightweight sqlite3 tables so each domain agent can store and
retrieve conversation turns and facts across ``jarvis ask`` sessions.

Optimisations (v2):
* Turn deduplication — identical consecutive turns are skipped.
* Turn pruning — only the most recent *max_turns* are retained.
* Fact upsert — updating an existing fact by source avoids duplicates.
* Relevance threshold — retrieval filters out scores below *min_score*.
* Content hashing — fast exact-match dedup without schema changes.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from openjarvis.tools.storage._stubs import RetrievalResult


# ---------------------------------------------------------------------------
# Tunable defaults
# ---------------------------------------------------------------------------

DEFAULT_MAX_TURNS: int = 200
DEFAULT_MAX_FACTS: int = 500
DEFAULT_MIN_SCORE: float = 0.15


class AgentMemoryManager:
    """Manages namespaced persistent memory for every agent.

    Each agent gets its own SQLite database under *base_dir* so isolation
    is trivial and there is no risk of one agent leaking context into
    another.
    """

    def __init__(
        self,
        base_dir: str | Path = "",
        *,
        max_turns: int = DEFAULT_MAX_TURNS,
        max_facts: int = DEFAULT_MAX_FACTS,
        min_score: float = DEFAULT_MIN_SCORE,
    ) -> None:
        if not base_dir:
            from openjarvis.core.config import DEFAULT_CONFIG_DIR

            base_dir = DEFAULT_CONFIG_DIR / "agent_memory"
        self._base_dir = Path(base_dir)
        self._base_dir.mkdir(parents=True, exist_ok=True)
        self._conns: Dict[str, sqlite3.Connection] = {}
        self._max_turns = max_turns
        self._max_facts = max_facts
        self._min_score = min_score

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _conn(self, agent_id: str) -> sqlite3.Connection:
        """Return a cached connection for *agent_id*, creating tables if needed."""
        if agent_id not in self._conns:
            db_path = self._base_dir / f"{agent_id}.db"
            conn = sqlite3.connect(str(db_path), check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS turns (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id  TEXT NOT NULL DEFAULT '',
                    role        TEXT NOT NULL,
                    content     TEXT NOT NULL,
                    content_hash TEXT NOT NULL DEFAULT '',
                    metadata    TEXT NOT NULL DEFAULT '{}',
                    created_at  REAL NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_turns_session
                    ON turns(session_id, created_at);
                CREATE INDEX IF NOT EXISTS idx_turns_agent_time
                    ON turns(created_at);
                CREATE INDEX IF NOT EXISTS idx_turns_hash
                    ON turns(content_hash);

                CREATE VIRTUAL TABLE IF NOT EXISTS turns_fts USING fts5(
                    content,
                    tokenize='porter unicode61'
                );

                CREATE TABLE IF NOT EXISTS facts (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    content     TEXT NOT NULL,
                    content_hash TEXT NOT NULL DEFAULT '',
                    source      TEXT NOT NULL DEFAULT '',
                    metadata    TEXT NOT NULL DEFAULT '{}',
                    created_at  REAL NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_facts_source
                    ON facts(source);
                CREATE INDEX IF NOT EXISTS idx_facts_hash
                    ON facts(content_hash);
                CREATE VIRTUAL TABLE IF NOT EXISTS facts_fts USING fts5(
                    content,
                    source,
                    tokenize='porter unicode61'
                );
                """
            )
            # Best-effort migration: add content_hash if missing (pre-v2 dbs)
            try:
                conn.execute("SELECT content_hash FROM turns LIMIT 1")
            except sqlite3.OperationalError:
                conn.execute(
                    "ALTER TABLE turns ADD COLUMN content_hash TEXT NOT NULL DEFAULT ''"
                )
                conn.execute("CREATE INDEX idx_turns_hash ON turns(content_hash)")
            try:
                conn.execute("SELECT content_hash FROM facts LIMIT 1")
            except sqlite3.OperationalError:
                conn.execute(
                    "ALTER TABLE facts ADD COLUMN content_hash TEXT NOT NULL DEFAULT ''"
                )
                conn.execute("CREATE INDEX idx_facts_hash ON facts(content_hash)")
            conn.commit()
            self._conns[agent_id] = conn
        return self._conns[agent_id]

    @staticmethod
    def _now() -> float:
        return time.time()

    @staticmethod
    def _hash(content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]

    def _prune_turns(self, conn: sqlite3.Connection) -> None:
        """Keep only the most recent *max_turns* rows."""
        conn.execute(
            "DELETE FROM turns WHERE id NOT IN ("
            " SELECT id FROM turns ORDER BY created_at DESC LIMIT ?"
            ")",
            (self._max_turns,),
        )
        # Rebuild FTS to stay in sync
        conn.execute("INSERT INTO turns_fts(turns_fts) VALUES('rebuild')")

    def _prune_facts(self, conn: sqlite3.Connection) -> None:
        """Keep only the most recent *max_facts* rows."""
        conn.execute(
            "DELETE FROM facts WHERE id NOT IN ("
            " SELECT id FROM facts ORDER BY created_at DESC LIMIT ?"
            ")",
            (self._max_facts,),
        )
        conn.execute("INSERT INTO facts_fts(facts_fts) VALUES('rebuild')")

    # ------------------------------------------------------------------
    # Turns (conversation history)
    # ------------------------------------------------------------------

    def store_turn(
        self,
        agent_id: str,
        role: str,
        content: str,
        *,
        session_id: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """Persist a single conversation turn and return its document id.

        Returns ``None`` when the exact same turn already exists as the
        most recent entry (deduplication).
        """
        conn = self._conn(agent_id)
        meta_json = json.dumps(metadata) if metadata else "{}"
        now = self._now()
        content_hash = self._hash(content)

        # Deduplication: skip if identical to last turn
        last = conn.execute(
            "SELECT content_hash FROM turns ORDER BY created_at DESC LIMIT 1"
        ).fetchone()
        if last and last["content_hash"] == content_hash:
            return None

        cursor = conn.execute(
            "INSERT INTO turns (session_id, role, content, content_hash, metadata, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (session_id, role, content, content_hash, meta_json, now),
        )
        doc_id = str(cursor.lastrowid)
        conn.execute(
            "INSERT INTO turns_fts (rowid, content) VALUES (?, ?)",
            (doc_id, content),
        )
        conn.commit()

        # Prune asynchronously cheap — runs every store, but only deletes when over limit
        self._prune_turns(conn)
        conn.commit()
        return doc_id

    def get_recent_turns(
        self,
        agent_id: str,
        *,
        limit: int = 10,
        session_id: Optional[str] = None,
    ) -> List[RetrievalResult]:
        """Return the most recent turns for an agent (oldest → newest)."""
        conn = self._conn(agent_id)
        if session_id:
            rows = conn.execute(
                "SELECT id, role, content, metadata, created_at FROM turns"
                " WHERE session_id = ? ORDER BY created_at DESC LIMIT ?",
                (session_id, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, role, content, metadata, created_at FROM turns"
                " ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()

        results: List[RetrievalResult] = []
        for row in rows:
            meta = json.loads(row["metadata"]) if row["metadata"] else {}
            meta["role"] = row["role"]
            meta["created_at"] = row["created_at"]
            results.append(
                RetrievalResult(
                    content=row["content"],
                    score=0.0,
                    source=row["role"],
                    metadata=meta,
                )
            )
        return list(reversed(results))

    def retrieve_turns(
        self,
        agent_id: str,
        query: str,
        *,
        top_k: int = 5,
        min_score: Optional[float] = None,
    ) -> List[RetrievalResult]:
        """FTS5 relevance-ranked search over an agent's conversation history.

        Results with a score below *min_score* (defaults to the manager's
        configured threshold) are dropped.
        """
        conn = self._conn(agent_id)
        if not query.strip():
            return []

        threshold = self._min_score if min_score is None else min_score
        rows = conn.execute(
            "SELECT t.id, t.role, t.content, t.metadata, t.created_at,"
            " rank FROM turns_fts"
            " JOIN turns t ON turns_fts.rowid = t.id"
            " WHERE turns_fts MATCH ?"
            " ORDER BY rank LIMIT ?",
            (query, top_k * 2),  # fetch extra for filtering
        ).fetchall()

        results: List[RetrievalResult] = []
        for row in rows:
            meta = json.loads(row["metadata"]) if row["metadata"] else {}
            meta["role"] = row["role"]
            meta["created_at"] = row["created_at"]
            # BM25 rank is lower-is-better; invert loosely for a 0-1 score
            rank = row["rank"] or 0.0
            score = max(0.0, 1.0 / (1.0 + abs(rank)))
            if score < threshold:
                continue
            results.append(
                RetrievalResult(
                    content=row["content"],
                    score=score,
                    source=row["role"],
                    metadata=meta,
                )
            )
            if len(results) >= top_k:
                break
        return results

    # ------------------------------------------------------------------
    # Facts (long-term knowledge)
    # ------------------------------------------------------------------

    def store_fact(
        self,
        agent_id: str,
        content: str,
        *,
        source: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Persist a fact / knowledge snippet for an agent.

        When *source* is provided and a fact with the same source already
        exists, the old fact is updated (upsert) instead of creating a
        duplicate.
        """
        conn = self._conn(agent_id)
        meta_json = json.dumps(metadata) if metadata else "{}"
        now = self._now()
        content_hash = self._hash(content)

        # Upsert by source
        if source:
            existing = conn.execute(
                "SELECT id FROM facts WHERE source = ? LIMIT 1", (source,)
            ).fetchone()
            if existing:
                doc_id = existing["id"]
                conn.execute(
                    "UPDATE facts SET content = ?, content_hash = ?,"
                    " metadata = ?, created_at = ? WHERE id = ?",
                    (content, content_hash, meta_json, now, doc_id),
                )
                conn.execute(
                    "UPDATE facts_fts SET content = ? WHERE rowid = ?",
                    (content, doc_id),
                )
                conn.commit()
                self._prune_facts(conn)
                conn.commit()
                return str(doc_id)

        cursor = conn.execute(
            "INSERT INTO facts (content, content_hash, source, metadata, created_at)"
            " VALUES (?, ?, ?, ?, ?)",
            (content, content_hash, source, meta_json, now),
        )
        doc_id = str(cursor.lastrowid)
        conn.execute(
            "INSERT INTO facts_fts (rowid, content, source) VALUES (?, ?, ?)",
            (doc_id, content, source),
        )
        conn.commit()
        self._prune_facts(conn)
        conn.commit()
        return doc_id

    def retrieve_facts(
        self,
        agent_id: str,
        query: str,
        *,
        top_k: int = 5,
        min_score: Optional[float] = None,
    ) -> List[RetrievalResult]:
        """FTS5 relevance-ranked search over an agent's fact store.

        Results with a score below *min_score* are dropped.
        """
        conn = self._conn(agent_id)
        if not query.strip():
            return []

        threshold = self._min_score if min_score is None else min_score
        rows = conn.execute(
            "SELECT f.id, f.content, f.source, f.metadata, f.created_at,"
            " rank FROM facts_fts"
            " JOIN facts f ON facts_fts.rowid = f.id"
            " WHERE facts_fts MATCH ?"
            " ORDER BY rank LIMIT ?",
            (query, top_k * 2),
        ).fetchall()

        results: List[RetrievalResult] = []
        for row in rows:
            meta = json.loads(row["metadata"]) if row["metadata"] else {}
            meta["created_at"] = row["created_at"]
            rank = row["rank"] or 0.0
            score = max(0.0, 1.0 / (1.0 + abs(rank)))
            if score < threshold:
                continue
            results.append(
                RetrievalResult(
                    content=row["content"],
                    score=score,
                    source=row["source"],
                    metadata=meta,
                )
            )
            if len(results) >= top_k:
                break
        return results

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def clear_agent_memory(self, agent_id: str) -> None:
        """Delete every turn and fact for *agent_id*."""
        conn = self._conn(agent_id)
        conn.execute("DELETE FROM turns")
        conn.execute("DELETE FROM turns_fts")
        conn.execute("DELETE FROM facts")
        conn.execute("DELETE FROM facts_fts")
        conn.commit()

    def close(self, agent_id: Optional[str] = None) -> None:
        """Close one or all cached connections."""
        if agent_id:
            conn = self._conns.pop(agent_id, None)
            if conn:
                conn.close()
        else:
            for conn in self._conns.values():
                conn.close()
            self._conns.clear()

    def __del__(self) -> None:
        self.close()


__all__ = ["AgentMemoryManager"]
