"""BenchmarkCase + loader tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from deep_research_bench import BenchmarkCase, load_cases


def test_minimal_case_is_valid() -> None:
    c = BenchmarkCase(id="x", query="hello?")
    assert c.id == "x"
    assert c.query == "hello?"
    assert c.must_contain_regex == []


def test_rejects_missing_id() -> None:
    with pytest.raises(ValueError):
        BenchmarkCase(id="", query="hi")


def test_rejects_missing_query() -> None:
    with pytest.raises(ValueError):
        BenchmarkCase(id="x", query="")


def test_rejects_negative_min_counts() -> None:
    with pytest.raises(ValueError):
        BenchmarkCase(id="x", query="q", min_citation_count=-1)
    with pytest.raises(ValueError):
        BenchmarkCase(id="x", query="q", min_word_count=-1)


def test_load_cases_list_format(tmp_path: Path) -> None:
    f = tmp_path / "cases.json"
    f.write_text(
        json.dumps(
            [
                {"id": "a", "query": "qa", "must_contain_regex": ["foo"]},
                {"id": "b", "query": "qb", "min_word_count": 10},
            ]
        )
    )
    cases = load_cases(f)
    assert len(cases) == 2
    assert cases[0].id == "a"
    assert cases[0].must_contain_regex == ["foo"]
    assert cases[1].min_word_count == 10


def test_load_cases_object_format(tmp_path: Path) -> None:
    """The 'cases' key wrapper format (snake_case AND camelCase keys)."""
    f = tmp_path / "cases.json"
    f.write_text(
        json.dumps(
            {
                "version": "v1",
                "cases": [
                    {
                        "id": "a",
                        "question": "qa",
                        "mustContainRegex": ["foo"],
                        "minCitationCount": 3,
                    },
                ],
            }
        )
    )
    cases = load_cases(f)
    assert len(cases) == 1
    assert cases[0].id == "a"
    assert cases[0].query == "qa"  # question -> query alias
    assert cases[0].must_contain_regex == ["foo"]  # camelCase accepted
    assert cases[0].min_citation_count == 3


def test_load_cases_rejects_duplicate_ids(tmp_path: Path) -> None:
    f = tmp_path / "dup.json"
    f.write_text(
        json.dumps(
            [
                {"id": "x", "query": "q1"},
                {"id": "x", "query": "q2"},
            ]
        )
    )
    with pytest.raises(ValueError, match="duplicate"):
        load_cases(f)


def test_load_cases_rejects_bad_top_level(tmp_path: Path) -> None:
    f = tmp_path / "bad.json"
    f.write_text(json.dumps({"not_cases_key": []}))
    with pytest.raises(ValueError):
        load_cases(f)


def test_load_cases_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_cases(tmp_path / "nonexistent.json")


def test_load_public_10_actually_loads() -> None:
    """Smoke test: the cases/public-10.json shipped with this package
    parses with the loader (no schema drift)."""
    public = Path(__file__).parent.parent / "cases" / "public-10.json"
    cases = load_cases(public)
    assert len(cases) == 10
    ids = [c.id for c in cases]
    assert len(set(ids)) == 10
    for c in cases:
        assert c.query
        assert c.category
        assert c.judge_criteria
