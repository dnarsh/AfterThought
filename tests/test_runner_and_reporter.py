"""Runner orchestration + reporter output tests."""

from __future__ import annotations

import json

import pytest

from deep_research_bench import (
    BenchmarkCase,
    CitationCountScorer,
    EngineAnswer,
    RegexScorer,
    StubJudge,
    WordCountScorer,
    run_benchmark,
    to_json,
    to_markdown,
)
from deep_research_bench.adapters.mock_engine import MockEngine


def _two_cases():
    return [
        BenchmarkCase(
            id="case-a",
            query="Q1",
            category="recency",
            must_contain_regex=["foo"],
            min_word_count=5,
            min_citation_count=1,
        ),
        BenchmarkCase(
            id="case-b",
            query="Q2",
            category="synthesis",
            must_contain_regex=["bar"],
            min_word_count=3,
        ),
    ]


def _scorers():
    return [RegexScorer(), CitationCountScorer(), WordCountScorer()]


def test_runner_runs_full_cross_product() -> None:
    cases = _two_cases()
    canned = {
        "Q1": EngineAnswer(text="foo word two three four five", citations=["u"]),
        "Q2": EngineAnswer(text="bar word three"),
    }
    mock = MockEngine(canned_answers=canned)
    run = run_benchmark(cases=cases, engines=[mock], scorers=_scorers())
    assert len(run.results) == 2
    assert all(r.engine_name == "mock" for r in run.results)
    assert all(r.all_passed for r in run.results)
    assert run.pass_rate("mock") == 1.0


def test_runner_records_engine_exception_as_cell_error() -> None:
    class BrokenEngine:
        name = "broken"

        def run(self, query: str):
            raise RuntimeError("intentional")

    cases = [BenchmarkCase(id="c", query="q")]
    run = run_benchmark(cases=cases, engines=[BrokenEngine()], scorers=[])
    assert len(run.results) == 1
    cell = run.results[0]
    assert cell.error is not None
    assert "RuntimeError" in cell.error
    assert "intentional" in cell.error
    assert not cell.all_passed
    assert run.pass_rate("broken") == 0.0


def test_runner_rejects_empty_inputs() -> None:
    with pytest.raises(ValueError):
        run_benchmark(cases=[], engines=[MockEngine()], scorers=[])
    with pytest.raises(ValueError):
        run_benchmark(cases=[BenchmarkCase(id="c", query="q")], engines=[], scorers=[])


def test_runner_includes_judge_when_given() -> None:
    cases = [BenchmarkCase(id="c", query="q")]
    mock = MockEngine()
    run = run_benchmark(
        cases=cases, engines=[mock], scorers=[], judge=StubJudge(fixed_score=4)
    )
    cell = run.results[0]
    assert cell.judge_result is not None
    assert cell.judge_result.score == 4
    assert run.mean_judge_score("mock") == 4.0


def test_reporter_markdown_has_expected_sections() -> None:
    cases = _two_cases()
    canned = {
        "Q1": EngineAnswer(text="foo " * 10, citations=["u"]),
        "Q2": EngineAnswer(text="not_matching " * 10),  # fails regex 'bar'
    }
    mock = MockEngine(canned_answers=canned)
    run = run_benchmark(cases=cases, engines=[mock], scorers=_scorers())
    md = to_markdown(run)
    assert "# Benchmark report" in md
    assert "## Engine summary" in md
    assert "## Per-case detail" in md
    assert "case-a" in md
    assert "case-b" in md
    assert "## Failure details" in md  # because case-b fails


def test_reporter_json_shape_is_serializable() -> None:
    cases = _two_cases()
    mock = MockEngine()
    run = run_benchmark(
        cases=cases, engines=[mock], scorers=_scorers(), judge=StubJudge()
    )
    data = to_json(run)
    # Must round-trip through json.dumps without errors
    serialized = json.dumps(data)
    parsed = json.loads(serialized)
    assert parsed["engines"] == ["mock"]
    assert "case-a" in [c["case_id"] for c in parsed["cells"]]
    assert parsed["summary"]["mock"]["cases_total"] == 2
    assert parsed["summary"]["mock"]["mean_judge_score"] == 3.0
    assert parsed["judge"] == "stub"


def test_write_report_creates_both_files(tmp_path) -> None:
    from deep_research_bench.reporter import write_report

    cases = [BenchmarkCase(id="c", query="q")]
    mock = MockEngine()
    run = run_benchmark(cases=cases, engines=[mock], scorers=_scorers())
    md_path, json_path = write_report(run, tmp_path / "out")
    assert md_path.exists()
    assert json_path.exists()
    assert "Benchmark report" in md_path.read_text(encoding="utf-8")
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert "engines" in data
