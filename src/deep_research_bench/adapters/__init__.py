"""Example engine adapters.

Currently shipped:
    MockEngine — deterministic canned answers, for tests and CLI demos.

Real adapters (Anthropic, OpenAI, Perplexity, your own private system)
are intentionally NOT shipped. They require API keys, billing setup,
and per-provider error handling that's better written for your exact
use case than guessed at by this framework. The ``judge`` module ships
a prompt builder + response parser to make writing your own adapter
short.
"""

from deep_research_bench.adapters.mock_engine import MockEngine

__all__ = ["MockEngine"]
