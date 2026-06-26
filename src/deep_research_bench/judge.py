"""Judge protocol + StubJudge + prompt helper.

A judge produces a 1-5 quality score from a (case, answer) pair using
some LLM-as-judge process. The framework treats judges as a separate
protocol from scorers because:
  * Judges have side effects (API calls). Scorers don't.
  * Judges cost money. Tests must be able to bypass them.
  * Judges can disagree. The framework supports running zero or one
    judge per benchmark; running multiple judges and aggregating is
    left to the caller.

This module ships the protocol, a deterministic ``StubJudge`` for
tests / offline runs, and a prompt-builder helper that real adapters
(Anthropic / OpenAI / ...) can use to keep their rubric consistent.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from deep_research_bench.case import BenchmarkCase
from deep_research_bench.engine import EngineAnswer


@dataclass(frozen=True)
class JudgeResult:
    """An LLM-as-judge score.

    Attributes:
        score: Integer 1-5. 1 = totally wrong / hallucinated, 5 =
            complete + accurate + well-cited.
        reasoning: The judge's free-text justification. Surface in
            reports so a human can spot-check the judge's calibration.
        judge_name: Name of the judge that produced this result.
    """

    score: int
    reasoning: str
    judge_name: str

    def __post_init__(self) -> None:
        if not (1 <= self.score <= 5):
            raise ValueError(f"judge score must be in 1..5, got {self.score}")


class Judge(Protocol):
    name: str

    def judge(self, case: BenchmarkCase, answer: EngineAnswer) -> JudgeResult: ...


class StubJudge:
    """Deterministic judge — always returns the same score. Useful for
    tests, dry-runs, and CI where you don't want to hit a real API.

    The stub returns a mid-range score (3) by default. Override
    ``fixed_score`` to test report formatting against high/low scores.
    """

    name = "stub"

    def __init__(self, fixed_score: int = 3) -> None:
        if not (1 <= fixed_score <= 5):
            raise ValueError("fixed_score must be in 1..5")
        self.fixed_score = fixed_score

    def judge(self, case: BenchmarkCase, answer: EngineAnswer) -> JudgeResult:
        return JudgeResult(
            score=self.fixed_score,
            reasoning=f"stub judge (always returns {self.fixed_score})",
            judge_name=self.name,
        )


JUDGE_RUBRIC = """\
You are evaluating an answer to a research question. Score the answer
1-5 on a single integer scale:

  1 = Wrong, hallucinated, or off-topic. Would mislead a reader.
  2 = Partially right but missing major requested elements.
  3 = Adequate. Covers the question but lacks depth, citations, or
      specificity.
  4 = Good. Covers the question with appropriate depth and at least
      some verifiable specifics.
  5 = Excellent. Comprehensive, accurate, well-cited, and directly
      addresses every part of the question.

Reply with exactly two lines:

  SCORE: <integer 1-5>
  REASONING: <one sentence>

Do not include any other text.
"""


def build_judge_prompt(case: BenchmarkCase, answer: EngineAnswer) -> str:
    """Build a standard rubric prompt that real-LLM judge adapters can
    use. Returns a string the adapter passes to its LLM."""
    extra_criteria = ""
    if case.judge_criteria:
        extra_criteria = (
            f"\n\nADDITIONAL CRITERIA FOR THIS QUESTION:\n{case.judge_criteria}"
        )

    citations_block = ""
    if answer.citations:
        cite_lines = "\n".join(f"  - {c}" for c in answer.citations)
        citations_block = f"\n\nCITATIONS PROVIDED:\n{cite_lines}"

    return (
        f"{JUDGE_RUBRIC}\n"
        f"QUESTION:\n{case.query}{extra_criteria}\n\n"
        f"ANSWER:\n{answer.text}{citations_block}"
    )


def parse_judge_response(text: str) -> tuple:
    """Parse a judge LLM's reply into (score, reasoning).

    Looks for ``SCORE: N`` and ``REASONING: ...`` lines (case-insensitive).
    Tolerant of extra surrounding whitespace and minor format drift.

    Returns (score, reasoning) on success. Raises ValueError if the
    score line is missing or out of range — adapters should catch this
    and surface a meaningful error to the user.
    """
    import re

    score_m = re.search(r"SCORE\s*[:=]\s*(\d+)", text, re.IGNORECASE)
    if not score_m:
        raise ValueError(f"could not find 'SCORE: N' in response: {text[:200]!r}")
    score = int(score_m.group(1))
    if not (1 <= score <= 5):
        raise ValueError(f"judge returned out-of-range score {score}")

    reason_m = re.search(
        r"REASONING\s*[:=]\s*(.+?)(?:\n\n|\Z)", text, re.IGNORECASE | re.DOTALL
    )
    reasoning = reason_m.group(1).strip() if reason_m else ""
    return score, reasoning
