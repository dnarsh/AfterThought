"""Scorer protocol + shared ScoreResult dataclass."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from deep_research_bench.case import BenchmarkCase
from deep_research_bench.engine import EngineAnswer


@dataclass(frozen=True)
class ScoreResult:
    """The output of a single scorer for a single (case, answer) pair.

    Attributes:
        passed: True if the scorer's contract was satisfied. The
            framework uses this for the aggregate pass/fail summary.
        score: Float in [0.0, 1.0]. Some scorers are binary (0 or 1);
            others (regex with partial-match counting) can be fractional.
        detail: Human-readable reason — included in reports so a reader
            understands WHY the answer scored as it did.
    """

    passed: bool
    score: float
    detail: str

    def __post_init__(self) -> None:
        if not (0.0 <= self.score <= 1.0):
            raise ValueError(f"score must be in [0, 1], got {self.score}")


class Scorer(Protocol):
    """A scorer protocol. Implementations are pure functions of
    (case, answer) — no I/O, no API calls. For LLM-as-judge scoring,
    use the Judge protocol instead."""

    name: str

    def score(self, case: BenchmarkCase, answer: EngineAnswer) -> ScoreResult: ...
