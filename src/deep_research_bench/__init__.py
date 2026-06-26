"""deep-research-bench — evaluation framework for deep-research engines.

Public API:
    BenchmarkCase, load_cases    — case schema + loader
    Engine, EngineAnswer         — engine protocol
    Scorer, ScoreResult          — scorer protocol
    RegexScorer, CitationCountScorer, WordCountScorer  — built-in scorers
    Judge, JudgeResult, StubJudge, build_judge_prompt  — judge protocol + helpers
    run_benchmark, BenchmarkRun  — runner + results
    to_markdown, to_json         — report formatters
"""

from deep_research_bench.case import BenchmarkCase, load_cases
from deep_research_bench.engine import Engine, EngineAnswer
from deep_research_bench.judge import (
    Judge,
    JudgeResult,
    StubJudge,
    build_judge_prompt,
)
from deep_research_bench.reporter import to_json, to_markdown
from deep_research_bench.runner import BenchmarkRun, CaseEngineResult, run_benchmark
from deep_research_bench.scorers import (
    CitationCountScorer,
    RegexScorer,
    ScoreResult,
    Scorer,
    WordCountScorer,
)

__all__ = [
    "BenchmarkCase",
    "BenchmarkRun",
    "CaseEngineResult",
    "CitationCountScorer",
    "Engine",
    "EngineAnswer",
    "Judge",
    "JudgeResult",
    "RegexScorer",
    "ScoreResult",
    "Scorer",
    "StubJudge",
    "WordCountScorer",
    "build_judge_prompt",
    "load_cases",
    "run_benchmark",
    "to_json",
    "to_markdown",
]
__version__ = "0.1.0"
