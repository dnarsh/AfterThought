"""Report formatters — markdown table + structured JSON."""

from __future__ import annotations

import json
from typing import Any, Dict

from deep_research_bench.runner import BenchmarkRun


def to_markdown(run: BenchmarkRun) -> str:
    """Render a BenchmarkRun as a markdown report.

    Layout: per-engine summary table, then per-case detail tables, then
    failure-detail blocks for any cells with engine errors or scorer
    failures."""
    lines: list = []
    lines.append("# Benchmark report")
    lines.append("")
    lines.append(
        f"- Cases: **{len(run.cases)}**  · Engines: **{len(run.engines)}**  "
        f"· Scorers: **{len(run.scorers)}**  · Judge: **{run.judge_name or 'none'}**"
    )
    elapsed = run.finished_at - run.started_at
    lines.append(f"- Elapsed: {elapsed:.1f}s")
    lines.append("")

    # === Engine summary ===
    lines.append("## Engine summary")
    lines.append("")
    has_judge = run.judge_name is not None
    headers = ["Engine", "Pass rate", "Cases passed"]
    if has_judge:
        headers.append("Mean judge score")
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("|" + "|".join("---" for _ in headers) + "|")
    for engine_name in run.engines:
        cells = run.by_engine(engine_name)
        passed = sum(1 for c in cells if c.all_passed)
        rate = run.pass_rate(engine_name)
        row = [engine_name, f"{rate * 100:.0f}%", f"{passed}/{len(cells)}"]
        if has_judge:
            mean = run.mean_judge_score(engine_name)
            row.append(f"{mean:.2f}" if mean is not None else "-")
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")

    # === Per-case detail ===
    lines.append("## Per-case detail")
    for case in run.cases:
        lines.append(f"\n### `{case.id}`  _{case.category}_")
        lines.append(f"> {case.query}")
        lines.append("")
        case_cells = [r for r in run.results if r.case_id == case.id]
        det_headers = ["Engine", "Overall"] + run.scorers
        if has_judge:
            det_headers.append("Judge")
        det_headers.append("Latency")
        lines.append("| " + " | ".join(det_headers) + " |")
        lines.append("|" + "|".join("---" for _ in det_headers) + "|")
        for cell in case_cells:
            row = [cell.engine_name]
            if cell.error:
                row.append("ERROR")
                for _ in run.scorers:
                    row.append("-")
                if has_judge:
                    row.append("-")
                row.append(f"{cell.latency_sec:.2f}s")
                lines.append("| " + " | ".join(row) + " |")
                continue
            row.append("PASS" if cell.all_passed else "FAIL")
            for scorer_name in run.scorers:
                sr = cell.scorer_results.get(scorer_name)
                if sr is None:
                    row.append("-")
                else:
                    row.append(f"{'PASS' if sr.passed else 'FAIL'} ({sr.score:.2f})")
            if has_judge:
                jr = cell.judge_result
                row.append(str(jr.score) if jr is not None else "-")
            row.append(f"{cell.latency_sec:.2f}s")
            lines.append("| " + " | ".join(row) + " |")

    # === Failure details ===
    failing_cells = [r for r in run.results if r.error or not r.all_passed]
    if failing_cells:
        lines.append("\n## Failure details\n")
        for cell in failing_cells:
            lines.append(f"\n### `{cell.case_id}` × `{cell.engine_name}`")
            if cell.error:
                lines.append(f"\n**Engine error:**\n```\n{cell.error}\n```")
                continue
            for name, sr in cell.scorer_results.items():
                if not sr.passed:
                    lines.append(f"- `{name}` FAIL — {sr.detail}")
            if cell.judge_result is not None and cell.judge_result.score < 3:
                lines.append(
                    f"- judge `{cell.judge_result.judge_name}` "
                    f"score={cell.judge_result.score} — {cell.judge_result.reasoning}"
                )

    return "\n".join(lines) + "\n"


def to_json(run: BenchmarkRun) -> Dict[str, Any]:
    """Render a BenchmarkRun as a JSON-serializable dict. Useful for
    machine consumption or for diffing two runs."""
    return {
        "engines": run.engines,
        "scorers": run.scorers,
        "judge": run.judge_name,
        "started_at": run.started_at,
        "finished_at": run.finished_at,
        "summary": {
            engine: {
                "pass_rate": run.pass_rate(engine),
                "cases_passed": sum(1 for c in run.by_engine(engine) if c.all_passed),
                "cases_total": len(run.by_engine(engine)),
                "mean_judge_score": run.mean_judge_score(engine),
            }
            for engine in run.engines
        },
        "cells": [
            {
                "case_id": r.case_id,
                "engine": r.engine_name,
                "passed": r.all_passed,
                "error": r.error,
                "latency_sec": r.latency_sec,
                "answer_text": r.answer.text,
                "answer_citations": list(r.answer.citations),
                "answer_metadata": dict(r.answer.metadata),
                "scorers": {
                    name: {
                        "passed": sr.passed,
                        "score": sr.score,
                        "detail": sr.detail,
                    }
                    for name, sr in r.scorer_results.items()
                },
                "judge": (
                    {
                        "score": r.judge_result.score,
                        "reasoning": r.judge_result.reasoning,
                        "judge_name": r.judge_result.judge_name,
                    }
                    if r.judge_result is not None
                    else None
                ),
            }
            for r in run.results
        ],
    }


def write_report(run: BenchmarkRun, output_dir, name: str = "report") -> tuple:
    """Convenience: write both markdown and JSON to ``output_dir``.

    Returns the two paths written, as Path objects."""
    from pathlib import Path

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    md_path = out / f"{name}.md"
    json_path = out / f"{name}.json"
    md_path.write_text(to_markdown(run), encoding="utf-8")
    json_path.write_text(json.dumps(to_json(run), indent=2), encoding="utf-8")
    return md_path, json_path
