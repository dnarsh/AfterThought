"""Scorer tests — pure logic, no I/O."""

from __future__ import annotations

import pytest

from deep_research_bench import (
    BenchmarkCase,
    CitationCountScorer,
    EngineAnswer,
    RegexScorer,
    ScoreResult,
    WordCountScorer,
)


def _case(**kw):
    """Quick BenchmarkCase factory with sensible defaults."""
    kw.setdefault("id", "t")
    kw.setdefault("query", "q")
    return BenchmarkCase(**kw)


def _answer(text="", citations=None) -> EngineAnswer:
    return EngineAnswer(text=text, citations=list(citations or []))


def test_score_result_rejects_out_of_range() -> None:
    with pytest.raises(ValueError):
        ScoreResult(passed=True, score=1.5, detail="")
    with pytest.raises(ValueError):
        ScoreResult(passed=True, score=-0.1, detail="")


def test_regex_scorer_all_match() -> None:
    s = RegexScorer()
    r = s.score(_case(must_contain_regex=["foo", "bar"]), _answer("foo and BAR"))
    assert r.passed is True
    assert r.score == 1.0


def test_regex_scorer_partial_match() -> None:
    s = RegexScorer()
    r = s.score(
        _case(must_contain_regex=["foo", "bar", "baz"]),
        _answer("only foo here"),
    )
    assert r.passed is False
    assert r.score == pytest.approx(1 / 3)
    assert "bar" in r.detail
    assert "baz" in r.detail


def test_regex_scorer_no_patterns_auto_pass() -> None:
    s = RegexScorer()
    r = s.score(_case(must_contain_regex=[]), _answer(""))
    assert r.passed is True
    assert r.score == 1.0


def test_regex_scorer_invalid_pattern() -> None:
    s = RegexScorer()
    r = s.score(_case(must_contain_regex=["(unclosed"]), _answer("anything"))
    assert r.passed is False
    assert "invalid regex" in r.detail


def test_citation_count_scorer_pass_and_fail() -> None:
    s = CitationCountScorer()
    case = _case(min_citation_count=2)

    r_pass = s.score(case, _answer(citations=["a", "b", "c"]))
    assert r_pass.passed is True
    assert r_pass.score == 1.0

    r_fail = s.score(case, _answer(citations=["a"]))
    assert r_fail.passed is False
    assert r_fail.score == 0.5  # have 1 of 2


def test_citation_count_no_min_auto_pass() -> None:
    s = CitationCountScorer()
    r = s.score(_case(), _answer())
    assert r.passed is True


def test_word_count_scorer_pass_and_fail() -> None:
    s = WordCountScorer()
    case = _case(min_word_count=5)

    r_pass = s.score(case, _answer("one two three four five six"))
    assert r_pass.passed is True

    r_fail = s.score(case, _answer("only two"))
    assert r_fail.passed is False
    assert r_fail.score == pytest.approx(2 / 5)


def test_word_count_no_min_auto_pass() -> None:
    s = WordCountScorer()
    r = s.score(_case(), _answer("anything"))
    assert r.passed is True
