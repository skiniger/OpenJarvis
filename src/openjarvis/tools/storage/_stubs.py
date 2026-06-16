"""ABC for memory / retrieval backends.

Phase 2 will provide concrete implementations (SQLite/FTS5, FAISS,
ColBERTv2, BM25, Hybrid).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(slots=True)
class RetrievalResult:
    """A single result returned by a memory backend query."""

    content: str
    score: float = 0.0
    source: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class MemoryBackend(ABC):
    """Base class for all memory / retrieval backends.

    Subclasses must be registered via
    ``@MemoryRegistry.register("name")`` to become discoverable.
    """

    backend_id: str

    @abstractmethod
    def store(
        self,
        content: str,
        *,
        source: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Persist *content* and return a unique document id."""

    @abstractmethod
    def retrieve(
        self,
        query: str,
        *,
        top_k: int = 5,
        **kwargs: Any,
    ) -> List[RetrievalResult]:
        """Search for *query* and return the top-k results."""

    @abstractmethod
    def delete(self, doc_id: str) -> bool:
        """Delete a document by id. Return ``True`` if it existed."""

    @abstractmethod
    def clear(self) -> None:
        """Remove all stored documents."""


class SimpleMemory(MemoryBackend):
    """Zero-dependency in-memory backend — used as fallback when compiled
    extensions or heavy dependencies are unavailable.
    """

    backend_id = "simple"

    def __init__(self) -> None:
        self._docs: list[RetrievalResult] = []
        self._counter = 0

    def store(
        self,
        content: str,
        *,
        source: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        doc_id = f"sm-{self._counter}"
        self._counter += 1
        self._docs.append(
            RetrievalResult(
                content=content,
                source=source,
                metadata=metadata or {},
            )
        )
        return doc_id

    def retrieve(
        self,
        query: str,
        *,
        top_k: int = 5,
        **kwargs: Any,
    ) -> List[RetrievalResult]:
        q = query.lower()
        scored = [
            (idx, r) for idx, r in enumerate(self._docs)
            if q in r.content.lower() or q in r.source.lower()
        ]
        # Simple ranking: more keyword matches = higher score
        def _score(item):
            _, r = item
            content_lower = r.content.lower()
            hits = content_lower.count(q)
            return hits * 0.1 + (1.0 if q in r.source.lower() else 0.0)

        scored.sort(key=lambda x: _score(x), reverse=True)
        return [r for _, r in scored[:top_k]]

    def delete(self, doc_id: str) -> bool:
        # SimpleMemory ids are sm-N; try to pop by index
        try:
            idx = int(doc_id.split("-")[1])
            if 0 <= idx < len(self._docs):
                self._docs.pop(idx)
                return True
        except (IndexError, ValueError):
            pass
        return False

    def clear(self) -> None:
        self._docs.clear()
        self._counter = 0

    def count(self) -> int:
        return len(self._docs)


__all__ = ["MemoryBackend", "RetrievalResult", "SimpleMemory"]
