"""Built-in scorers — cheap, no-I/O grading."""

from __future__ import annotations

import re
from typing import List

from deep_research_bench.case import BenchmarkCase
from deep_research_bench.engine import EngineAnswer
from deep_research_bench.scorers.base import ScoreResult


class RegexScorer:
    """Pass iff every regex in ``case.must_contain_regex`` matches
    the answer text (case-insensitive by default).

    Partial-credit score = matched_count / total_count, so a partially-
    answered question gets a fractional score in reports even though
    ``passed`` is False.

    Cases that declare no patterns are auto-passed with score=1.0.
    """

    name = "regex"

    def __init__(self, case_insensitive: bool = True) -> None:
        self.flags = re.IGNORECASE if case_insensitive else 0

    def score(self, case: BenchmarkCase, answer: EngineAnswer) -> ScoreResult:
        patterns: List[str] = case.must_contain_regex
        if not patterns:
            return ScoreResult(passed=True, score=1.0, detail="no patterns declared")
        matched: List[str] = []
        missing: List[str] = []
        for p in patterns:
            try:
                compiled = re.compile(p, self.flags)
            except re.error as e:
                return ScoreResult(
                    passed=False, score=0.0, detail=f"invalid regex {p!r}: {e}"
                )
            if compiled.search(answer.text):
                matched.append(p)
            else:
                missing.append(p)
        score = len(matched) / len(patterns)
        passed = not missing
        detail = f"matched {len(matched)}/{len(patterns)} patterns" + (
            f"; missing: {missing}" if missing else ""
        )
        return ScoreResult(passed=passed, score=score, detail=detail)


class CitationCountScorer:
    """Pass iff len(answer.citations) >= case.min_citation_count.

    Cases that declare no min are auto-passed with score=1.0.
    """

    name = "citation_count"

    def score(self, case: BenchmarkCase, answer: EngineAnswer) -> ScoreResult:
        if case.min_citation_count is None:
            return ScoreResult(passed=True, score=1.0, detail="no min declared")
        have = len(answer.citations)
        need = case.min_citation_count
        passed = have >= need
        score = 1.0 if passed else (have / need if need > 0 else 1.0)
        score = min(1.0, max(0.0, score))
        return ScoreResult(
            passed=passed, score=score, detail=f"have {have} citations, need {need}"
        )


class WordCountScorer:
    """Pass iff answer word count >= case.min_word_count.

    Word counting is whitespace-split (deliberately simple). For prose
    answers in English this is close enough; for code-heavy answers it
    over-counts. If you need a tokenizer-based count, write your own
    scorer.

    Cases that declare no min are auto-passed with score=1.0.
    """

    name = "word_count"

    def score(self, case: BenchmarkCase, answer: EngineAnswer) -> ScoreResult:
        if case.min_word_count is None:
            return ScoreResult(passed=True, score=1.0, detail="no min declared")
        have = len(answer.text.split())
        need = case.min_word_count
        passed = have >= need
        score = 1.0 if passed else (have / need if need > 0 else 1.0)
        score = min(1.0, max(0.0, score))
        return ScoreResult(
            passed=passed, score=score, detail=f"have {have} words, need {need}"
        )
