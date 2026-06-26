"""Benchmark case schema + JSON loader.

A case is a single query + a set of scoring contracts. Cases are loaded
from JSON files so you can author / version-control your own
benchmarks without touching code.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, List, Optional, Union


@dataclass(frozen=True)
class BenchmarkCase:
    """A single benchmark case.

    Required:
        id: stable identifier (used in reports)
        query: the question sent to engines under test

    Optional scoring contracts (a missing contract is simply not scored):
        category: free-text grouping label
        severity: free-text severity label (e.g. "P1", "P2")
        must_contain_regex: list of regex patterns that the answer text
            must match (case-insensitive). Used by RegexScorer.
        min_citation_count: floor for the citation count. Used by
            CitationCountScorer.
        min_word_count: floor for the answer word count. Used by
            WordCountScorer.
        judge_criteria: free-text instruction for an LLM-as-judge. Used
            by Judge implementations to build the rubric prompt.
    """

    id: str
    query: str
    category: str = ""
    severity: str = ""
    must_contain_regex: List[str] = field(default_factory=list)
    min_citation_count: Optional[int] = None
    min_word_count: Optional[int] = None
    judge_criteria: str = ""

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("BenchmarkCase.id is required")
        if not self.query:
            raise ValueError(f"BenchmarkCase {self.id!r}: query is required")
        if self.min_citation_count is not None and self.min_citation_count < 0:
            raise ValueError(
                f"BenchmarkCase {self.id!r}: min_citation_count must be >= 0"
            )
        if self.min_word_count is not None and self.min_word_count < 0:
            raise ValueError(f"BenchmarkCase {self.id!r}: min_word_count must be >= 0")


def _case_from_dict(d: dict) -> BenchmarkCase:
    """Build a BenchmarkCase from a JSON-dict entry. Accepts both
    snake_case (Python convention) and camelCase (common in JSON)."""

    def pick(*keys: str, default: Any = None) -> Any:
        for k in keys:
            if k in d:
                return d[k]
        return default

    return BenchmarkCase(
        id=pick("id", default=""),
        query=pick("query", "question", default=""),
        category=pick("category", default="") or "",
        severity=pick("severity", default="") or "",
        must_contain_regex=list(
            pick("must_contain_regex", "mustContainRegex", default=[]) or []
        ),
        min_citation_count=pick("min_citation_count", "minCitationCount"),
        min_word_count=pick("min_word_count", "minWordCount"),
        judge_criteria=pick("judge_criteria", "judgeCriteria", default="") or "",
    )


def load_cases(path: Union[str, os.PathLike]) -> List[BenchmarkCase]:
    """Load cases from a JSON file.

    The file may be either:
      * A list of case dicts: ``[{"id": ..., "query": ...}, ...]``
      * An object with a "cases" key: ``{"cases": [...], "version": ...}``
        (this matches the schema used by the original system this
        framework was extracted from)

    Raises FileNotFoundError if the file doesn't exist, json.JSONDecodeError
    on invalid JSON, ValueError on schema violations.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"cases file not found: {p}")
    with p.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "cases" in data:
        raw_cases = data["cases"]
    elif isinstance(data, list):
        raw_cases = data
    else:
        raise ValueError(
            f"{p}: top-level JSON must be a list or an object with 'cases' key"
        )
    if not isinstance(raw_cases, list):
        raise ValueError(f"{p}: 'cases' must be a list")
    out: List[BenchmarkCase] = []
    seen_ids = set()
    for i, entry in enumerate(raw_cases):
        if not isinstance(entry, dict):
            raise ValueError(f"{p}: case index {i} is not a dict")
        case = _case_from_dict(entry)
        if case.id in seen_ids:
            raise ValueError(f"{p}: duplicate case id {case.id!r}")
        seen_ids.add(case.id)
        out.append(case)
    return out
