"""Scorers — pluggable per-case grading functions.

Built-in scorers:
    RegexScorer          — checks must_contain_regex patterns
    CitationCountScorer  — checks citation count >= min_citation_count
    WordCountScorer      — checks word count >= min_word_count

Custom scorers: anything with ``name: str`` and
``score(case, answer) -> ScoreResult`` works.
"""

from deep_research_bench.scorers.base import ScoreResult, Scorer
from deep_research_bench.scorers.builtins import (
    CitationCountScorer,
    RegexScorer,
    WordCountScorer,
)

__all__ = [
    "CitationCountScorer",
    "RegexScorer",
    "ScoreResult",
    "Scorer",
    "WordCountScorer",
]
