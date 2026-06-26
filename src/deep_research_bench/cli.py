"""Minimal CLI — run a benchmark with the built-in mock engine and
print a markdown report.

Real-engine adapters are NOT shipped with this CLI on purpose: they
need API keys and provider-specific config. To use a real adapter,
import the framework in Python and call ``run_benchmark`` yourself.
The mock engine is wired up here so anyone can see the framework's
output shape end-to-end without setting up credentials.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional, Sequence

from deep_research_bench import (
    CitationCountScorer,
    RegexScorer,
    StubJudge,
    WordCountScorer,
    load_cases,
    run_benchmark,
    to_markdown,
)
from deep_research_bench.adapters.mock_engine import MockEngine
from deep_research_bench.reporter import write_report


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="deep-research-bench",
        description="Run a deep-research benchmark with the mock engine "
        "(plug in your own engines via the Python API).",
    )
    p.add_argument("--cases", required=True, help="Path to cases JSON file")
    p.add_argument(
        "--output",
        default=None,
        help="Output directory for report.md / report.json (omit to print "
        "markdown to stdout only)",
    )
    p.add_argument(
        "--judge",
        action="store_true",
        help="Include StubJudge in the run (deterministic mid-score). "
        "For real LLM judges, use the Python API.",
    )
    p.add_argument(
        "--mock-name",
        default="mock",
        help="Name reported for the mock engine (default: 'mock')",
    )
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_parser().parse_args(argv)

    try:
        cases = load_cases(args.cases)
    except (FileNotFoundError, ValueError) as e:
        print(f"error loading cases: {e}", file=sys.stderr)
        return 2

    engine = MockEngine(name=args.mock_name)
    scorers = [RegexScorer(), CitationCountScorer(), WordCountScorer()]
    judge = StubJudge() if args.judge else None

    run = run_benchmark(cases=cases, engines=[engine], scorers=scorers, judge=judge)
    md = to_markdown(run)
    print(md)

    if args.output:
        md_path, json_path = write_report(run, Path(args.output))
        print(f"\nWrote {md_path} and {json_path}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
