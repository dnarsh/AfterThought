"""Judge protocol + StubJudge + prompt helpers."""

from __future__ import annotations

import pytest

from deep_research_bench import (
    BenchmarkCase,
    EngineAnswer,
    JudgeResult,
    StubJudge,
    build_judge_prompt,
)
from deep_research_bench.judge import JUDGE_RUBRIC, parse_judge_response


def test_judge_result_validates_range() -> None:
    JudgeResult(score=1, reasoning="ok", judge_name="t")
    JudgeResult(score=5, reasoning="ok", judge_name="t")
    with pytest.raises(ValueError):
        JudgeResult(score=0, reasoning="", judge_name="t")
    with pytest.raises(ValueError):
        JudgeResult(score=6, reasoning="", judge_name="t")


def test_stub_judge_returns_fixed_score() -> None:
    j = StubJudge(fixed_score=4)
    case = BenchmarkCase(id="x", query="q")
    answer = EngineAnswer(text="a")
    r = j.judge(case, answer)
    assert r.score == 4
    assert r.judge_name == "stub"
    assert "stub" in r.reasoning.lower()


def test_stub_judge_rejects_invalid_fixed_score() -> None:
    with pytest.raises(ValueError):
        StubJudge(fixed_score=0)
    with pytest.raises(ValueError):
        StubJudge(fixed_score=6)


def test_build_judge_prompt_includes_query_and_answer() -> None:
    case = BenchmarkCase(
        id="x",
        query="What is X?",
        judge_criteria="Bonus for mentioning Y.",
    )
    answer = EngineAnswer(text="X is a thing.", citations=["https://x.example/1"])
    prompt = build_judge_prompt(case, answer)
    assert JUDGE_RUBRIC in prompt
    assert "What is X?" in prompt
    assert "X is a thing." in prompt
    assert "Bonus for mentioning Y." in prompt
    assert "https://x.example/1" in prompt


def test_parse_judge_response_happy_path() -> None:
    score, reason = parse_judge_response("SCORE: 4\nREASONING: covers main facts.")
    assert score == 4
    assert reason == "covers main facts."


def test_parse_judge_response_lenient_whitespace() -> None:
    score, reason = parse_judge_response(
        "Some preamble.\n\n  SCORE = 5\n  REASONING:    excellent answer\n\n  trailing."
    )
    assert score == 5
    assert "excellent" in reason


def test_parse_judge_response_missing_score_raises() -> None:
    with pytest.raises(ValueError, match="SCORE"):
        parse_judge_response("REASONING: I forgot the score.")


def test_parse_judge_response_out_of_range_raises() -> None:
    with pytest.raises(ValueError, match="out-of-range"):
        parse_judge_response("SCORE: 7\nREASONING: too high.")
