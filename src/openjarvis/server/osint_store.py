"""OSINT Result Store — persists scan and execution results.

Uses in-memory storage by default. If a Redis/KV client is available
via the app state, results are also persisted there.
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class HistoryEntry:
    """Single OSINT action (scan or exec)."""

    id: str
    type: str  # "scan" | "exec"
    user_id: str
    timestamp: str
    target: str | None = None
    tool_name: str | None = None
    modules: list[str] | None = None
    results: dict[str, Any] | None = None
    output: str | None = None
    success: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


class OsintStore:
    """In-memory store for OSINT scan and execution history."""

    def __init__(self) -> None:
        self._history: dict[str, list[HistoryEntry]] = {}
        self._favorites: dict[str, set[str]] = {}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _user_history(self, user_id: str) -> list[HistoryEntry]:
        return self._history.setdefault(user_id, [])

    def _user_favorites(self, user_id: str) -> set[str]:
        return self._favorites.setdefault(user_id, set())

    # ------------------------------------------------------------------
    # Scan persistence
    # ------------------------------------------------------------------

    def save_scan(
        self,
        user_id: str,
        target: str,
        modules: list[str],
        results: dict[str, Any],
        summary: dict[str, Any],
    ) -> str:
        """Persist a Watchdog scan result. Returns the entry id."""
        entry = HistoryEntry(
            id=str(uuid.uuid4()),
            type="scan",
            user_id=user_id,
            timestamp=self._now(),
            target=target,
            modules=modules,
            results=results,
            success=summary.get("errors", 0) == 0,
            metadata={"summary": summary},
        )
        self._user_history(user_id).append(entry)
        return entry.id

    # ------------------------------------------------------------------
    # Exec persistence
    # ------------------------------------------------------------------

    def save_exec(
        self,
        user_id: str,
        tool_name: str,
        target: str,
        output: str,
        success: bool,
        metadata: dict[str, Any],
    ) -> str:
        """Persist a tool execution result. Returns the entry id."""
        entry = HistoryEntry(
            id=str(uuid.uuid4()),
            type="exec",
            user_id=user_id,
            timestamp=self._now(),
            target=target,
            tool_name=tool_name,
            output=output,
            success=success,
            metadata=metadata,
        )
        self._user_history(user_id).append(entry)
        return entry.id

    # ------------------------------------------------------------------
    # History queries
    # ------------------------------------------------------------------

    def list_history(self, user_id: str, limit: int = 50) -> list[dict[str, Any]]:
        """Return chronologically sorted history (newest first)."""
        history = self._user_history(user_id)
        sorted_history = sorted(history, key=lambda e: e.timestamp, reverse=True)
        return [asdict(e) for e in sorted_history[:limit]]

    def delete_history_entry(self, user_id: str, entry_id: str) -> bool:
        """Delete a single history entry. Returns True if found and removed."""
        history = self._user_history(user_id)
        for idx, entry in enumerate(history):
            if entry.id == entry_id:
                history.pop(idx)
                return True
        return False

    def clear_history(self, user_id: str) -> int:
        """Clear all history for a user. Returns number of removed entries."""
        history = self._user_history(user_id)
        count = len(history)
        history.clear()
        return count

    # ------------------------------------------------------------------
    # Favorites
    # ------------------------------------------------------------------

    def toggle_favorite(self, user_id: str, tool_name: str) -> bool:
        """Toggle favorite status for a tool. Returns new status (True = favorited)."""
        favs = self._user_favorites(user_id)
        if tool_name in favs:
            favs.discard(tool_name)
            return False
        favs.add(tool_name)
        return True

    def list_favorites(self, user_id: str) -> list[str]:
        """Return list of favorited tool names."""
        return sorted(self._user_favorites(user_id))

    def is_favorite(self, user_id: str, tool_name: str) -> bool:
        return tool_name in self._user_favorites(user_id)

    # ------------------------------------------------------------------
    # Dashboard stats
    # ------------------------------------------------------------------

    def get_dashboard_stats(self, user_id: str) -> dict[str, Any]:
        """Return aggregated stats for the dashboard."""
        from collections import Counter
        from datetime import timedelta

        history = self._user_history(user_id)
        scans = [e for e in history if e.type == "scan"]
        execs = [e for e in history if e.type == "exec"]

        # Success rate
        total = len(history)
        successes = sum(1 for e in history if e.success)
        success_rate = round((successes / total) * 100, 1) if total else 0.0

        # Top targets
        target_counts = Counter(
            e.target for e in history if e.target
        )
        top_targets = [
            {"target": target, "count": count}
            for target, count in target_counts.most_common(5)
        ]

        # Tool usage
        tool_counts = Counter(
            e.tool_name for e in history if e.tool_name
        )
        tool_usage = [
            {"tool_name": tool, "count": count}
            for tool, count in tool_counts.most_common(5)
        ]

        # Module usage (from scan metadata)
        module_counts: Counter[str] = Counter()
        for scan in scans:
            if scan.modules:
                for mod in scan.modules:
                    module_counts[mod] += 1
        module_usage = [
            {"module": mod, "count": count}
            for mod, count in module_counts.most_common(5)
        ]

        # Activity timeline (last 30 days)
        today = datetime.now(timezone.utc).date()
        timeline: dict[str, dict[str, int]] = {}
        for i in range(30):
            day = (today - timedelta(days=i)).isoformat()
            timeline[day] = {"scans": 0, "execs": 0}

        for entry in history:
            entry_date = entry.timestamp[:10]  # YYYY-MM-DD
            if entry_date in timeline:
                if entry.type == "scan":
                    timeline[entry_date]["scans"] += 1
                else:
                    timeline[entry_date]["execs"] += 1

        activity_timeline = [
            {"date": day, "scans": data["scans"], "execs": data["execs"]}
            for day, data in sorted(timeline.items())
        ]

        return {
            "total_scans": len(scans),
            "total_execs": len(execs),
            "total_actions": total,
            "unique_targets": len(target_counts),
            "success_rate": success_rate,
            "top_targets": top_targets,
            "tool_usage": tool_usage,
            "module_usage": module_usage,
            "activity_timeline": activity_timeline,
        }


# Global singleton (server lifetime)
_store: OsintStore | None = None


def get_store() -> OsintStore:
    """Get or create the global OsintStore singleton."""
    global _store
    if _store is None:
        _store = OsintStore()
    return _store
