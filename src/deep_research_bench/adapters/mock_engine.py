"""Deterministic mock engine — for tests, dry runs, and CLI demos."""

from __future__ import annotations

import hashlib
from typing import Dict, Optional

from deep_research_bench.engine import EngineAnswer


class MockEngine:
    """Returns canned answers from a per-query dict, or a deterministic
    pseudo-answer derived from the query hash if the query isn't mapped.

    Pseudo-answers are NOT meant to score well — they're just
    deterministic placeholders so reports look realistic in demos.
    """

    def __init__(
        self,
        name: str = "mock",
        canned_answers: Optional[Dict[str, EngineAnswer]] = None,
        pseudo_word_count: int = 80,
        pseudo_citation_count: int = 2,
        latency_sec: float = 0.0,
    ) -> None:
        self.name = name
        self.canned = dict(canned_answers or {})
        self.pseudo_word_count = max(0, pseudo_word_count)
        self.pseudo_citation_count = max(0, pseudo_citation_count)
        self.latency_sec = max(0.0, latency_sec)

    def run(self, query: str) -> EngineAnswer:
        if self.latency_sec > 0:
            import time

            time.sleep(self.latency_sec)
        if query in self.canned:
            return self.canned[query]
        return self._pseudo(query)

    def _pseudo(self, query: str) -> EngineAnswer:
        h = hashlib.sha256(query.encode("utf-8")).hexdigest()
        # Build a deterministic pseudo-text by repeating hash chunks.
        chunk_size = max(1, len(h) // self.pseudo_word_count)
        words = [h[i : i + chunk_size] for i in range(0, len(h), chunk_size)]
        text = " ".join(words[: self.pseudo_word_count])
        citations = [
            f"https://example.invalid/mock/{h[:8]}/{i}"
            for i in range(self.pseudo_citation_count)
        ]
        return EngineAnswer(
            text=text,
            citations=citations,
            metadata={"engine": self.name, "query_hash": h[:16]},
        )
