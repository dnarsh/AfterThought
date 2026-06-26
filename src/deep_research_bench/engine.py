"""Engine protocol — the contract for anything that can answer a query.

An engine is anything that takes a query string and returns an
``EngineAnswer``. That's it. This is deliberately minimal: real
engines wrap external services (Perplexity, OpenAI Deep Research,
Anthropic search-tool calls, your own private system); mock engines
return canned answers for tests.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Protocol


@dataclass(frozen=True)
class EngineAnswer:
    """An engine's response to a query.

    Attributes:
        text: The answer text. Must be a string (may be empty).
        citations: List of citation URLs/identifiers. Empty list if
            the engine doesn't produce citations.
        metadata: Anything the engine wants to attach for reporting:
            latency, token count, model name, retry count, etc. Should
            be JSON-serializable so reports can persist it.
    """

    text: str
    citations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class Engine(Protocol):
    """An engine under test.

    Implementations must set ``name`` (used in reports) and implement
    ``run(query)``. Engines are expected to handle their own retries,
    timeouts, and rate-limiting — the framework treats engine failures
    as test failures (the engine returns an empty / error-marked answer).
    """

    name: str

    def run(self, query: str) -> EngineAnswer: ...
