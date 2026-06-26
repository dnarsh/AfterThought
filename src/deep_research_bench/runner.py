"""The benchmark runner — orchestrates (cases × engines × scorers + judge)."""

from __future__ import annotations

import time
import traceback
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

from deep_research_bench.case import BenchmarkCase
from deep_research_bench.engine import Engine, EngineAnswer
from deep_research_bench.judge import Judge, JudgeResult
from deep_research_bench.scorers.base import ScoreResult, Scorer


@dataclass
class CaseEngineResult:
    """All scoring outputs for one (case, engine) cell."""

    case_id: str
    engine_name: str
    answer: EngineAnswer
    scorer_results: Dict[str, ScoreResult] = field(default_factory=dict)
    judge_result: Optional[JudgeResult] = None
    error: Optional[str] = None
    latency_sec: float = 0.0

    @property
    def all_passed(self) -> bool:
        """True iff there was no engine error AND every scorer passed."""
        if self.error is not None:
            return False
        return all(r.passed for r in self.scorer_results.values())


@dataclass
class BenchmarkRun:
    """Full benchmark results — cases × engines + summary."""

    cases: List[BenchmarkCase]
    engines: List[str]
    scorers: List[str]
    judge_name: Optional[str]
    results: List[CaseEngineResult] = field(default_factory=list)
    started_at: float = 0.0
    finished_at: float = 0.0

    def by_engine(self, engine_name: str) -> List[CaseEngineResult]:
        return [r for r in self.results if r.engine_name == engine_name]

    def pass_rate(self, engine_name: str) -> float:
        cells = self.by_engine(engine_name)
        if not cells:
            return 0.0
        return sum(1 for c in cells if c.all_passed) / len(cells)

    def mean_judge_score(self, engine_name: str) -> Optional[float]:
        cells = [c for c in self.by_engine(engine_name) if c.judge_result is not None]
        if not cells:
            return None
        return sum(c.judge_result.score for c in cells) / len(cells)


def run_benchmark(
    cases: Sequence[BenchmarkCase],
    engines: Sequence[Engine],
    scorers: Sequence[Scorer],
    judge: Optional[Judge] = None,
) -> BenchmarkRun:
    """Run every (case, engine) pair through every scorer + the judge.

    Engine exceptions are CAUGHT and recorded as ``error`` on the
    CaseEngineResult — one engine crashing must not abort the whole
    benchmark. Scorer exceptions are NOT caught; a broken scorer is a
    bug in the scorer, not in the engine under test.
    """
    if not cases:
        raise ValueError("at least one case required")
    if not engines:
        raise ValueError("at least one engine required")

    run = BenchmarkRun(
        cases=list(cases),
        engines=[e.name for e in engines],
        scorers=[s.name for s in scorers],
        judge_name=judge.name if judge is not None else None,
        started_at=time.time(),
    )

    for case in cases:
        for engine in engines:
            cell = _run_one_cell(case, engine, scorers, judge)
            run.results.append(cell)

    run.finished_at = time.time()
    return run


def _run_one_cell(
    case: BenchmarkCase,
    engine: Engine,
    scorers: Sequence[Scorer],
    judge: Optional[Judge],
) -> CaseEngineResult:
    started = time.monotonic()
    try:
        answer = engine.run(case.query)
    except Exception as e:
        return CaseEngineResult(
            case_id=case.id,
            engine_name=engine.name,
            answer=EngineAnswer(text=""),
            error=f"{type(e).__name__}: {e}\n{traceback.format_exc(limit=4)}",
            latency_sec=time.monotonic() - started,
        )
    latency = time.monotonic() - started

    cell = CaseEngineResult(
        case_id=case.id,
        engine_name=engine.name,
        answer=answer,
        latency_sec=latency,
    )
    for scorer in scorers:
        cell.scorer_results[scorer.name] = scorer.score(case, answer)
    if judge is not None:
        try:
            cell.judge_result = judge.judge(case, answer)
        except Exception as e:
            cell.error = f"judge {judge.name} raised {type(e).__name__}: {e}"
    return cell
