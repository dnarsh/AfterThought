"""A source-derived FlyWire evidence case, separate from the public-10 suite.

This is a deterministic metadata summary and structural answer evaluation,
not an LLM answer, a factual-certification judge, or a neural simulation.
"""

from dataclasses import asdict
import re

from deep_research_bench import (
    BenchmarkCase, CitationCountScorer, EngineAnswer, RegexScorer,
    WordCountScorer, run_benchmark, to_json, to_markdown,
)
from deep_research_bench.connectome import ConnectomeError, SOURCE_URL, query_neurons


def _count_pattern(value: int) -> str:
    return r"(?<![\d,])(?:" + re.escape(format(value, ",")) + "|" + str(value) + r")(?![\d,])"


def build_connectome_brief() -> dict:
    """Calculate facts from the complete cached snapshot, never a visible sample."""
    snapshot = query_neurons(transmitter="GABA", limit=1)
    try:
        total = snapshot["total_neurons"]
        matching = snapshot["matching_neurons"]
        if (
            snapshot["dataset"] != "FlyWire FAFB v783"
            or snapshot["source_url"] != SOURCE_URL
            or snapshot["snapshot"] is not True
            or type(total) is not int or not 0 < total <= 200_000
            or type(matching) is not int or not 0 <= matching <= total
        ):
            raise ValueError("invalid snapshot")
        counts = {}
        entries = snapshot["neurotransmitters"]
        if not isinstance(entries, list) or not entries:
            raise ValueError("missing counts")
        for entry in entries:
            name, count = entry["name"], entry["count"]
            if (
                not isinstance(name, str) or not name or name in counts
                or type(count) is not int or not 0 <= count <= total
            ):
                raise ValueError("invalid counts")
            counts[name] = count
        gaba = counts["GABA"]
        if sum(counts.values()) != total or gaba != matching:
            raise ValueError("inconsistent counts")
        retrieved = snapshot["retrieved_at"]
        if not isinstance(retrieved, str) or not retrieved:
            raise ValueError("missing source timestamp")
    except (KeyError, TypeError, ValueError):
        raise ConnectomeError("The FlyWire evidence snapshot is inconsistent. Retry later.") from None

    percentage = round(gaba * 100 / total, 2)
    facts = {
        "total_neurons": total,
        "gaba_neurons": gaba,
        "percentage": percentage,
        "dataset": snapshot["dataset"],
        "source_url": SOURCE_URL,
        "retrieved_at": retrieved,
        "version": 783,
    }
    text = (
        "FlyWire FAFB v783's published neuron metadata contains {total:,} neurons. "
        "Of these, {gaba:,} have GABA as their predicted neurotransmitter, representing "
        "{percentage:.2f}% of the snapshot total. The fraction is calculated from the "
        "GABA prediction count divided by all neuron records, multiplied by one hundred; "
        "it is not estimated from the limited rows shown in the explorer. "
        "These are neurotransmitter predictions attached to reconstructed neurons, not "
        "direct measurements of firing or behavior. The source is the version 783 "
        "metadata archive cited below. This brief describes a fixed snapshot, not a "
        "live neural simulation, and the connector does not load synaptic edges or run "
        "an AI model. Counts should be interpreted within this dataset and its "
        "annotation limits rather than generalized to every fly brain. This text is a "
        "deterministic dataset summary, not an LLM-generated research conclusion."
    ).format(total=total, gaba=gaba, percentage=percentage)
    case = BenchmarkCase(
        id="flywire-gaba-evidence",
        category="dataset-evidence",
        severity="P1",
        query=(
            "Using the FlyWire FAFB v783 neuron metadata snapshot, how many neurons "
            "have GABA as their predicted neurotransmitter, and what percentage of all "
            "neuron records is that (to two decimal places)? Give the total, cite the "
            "source, and explain that predictions and snapshot metadata do not constitute "
            "a live neural simulation."
        ),
        must_contain_regex=[
            r"\bGABA\b", _count_pattern(total), _count_pattern(gaba),
            r"(?<![\d.])" + re.escape(format(percentage, ".2f")) + r"\s*%",
            r"\b(?:v\s*)?783\b", r"\b(?:predicted|prediction|predictions)\b",
            r"\bmetadata\b", r"\bsnapshot\b",
            r"\b(?:not\s+(?:a\s+)?(?:live\s+)?(?:neural|brain)\s+simulation|no\s+(?:neural|brain)\s+simulation)\b",
        ],
        min_citation_count=1,
        min_word_count=110,
        judge_criteria=(
            "Structural checks only: expected source-derived counts, percentage, "
            "version, prediction/snapshot limits, citation count, and word count. "
            "No LLM judge runs; passing does not establish factual correctness or verify citation URLs."
        ),
    )
    return {
        "case": asdict(case),
        "answer": {"text": text, "citations": [SOURCE_URL]},
        "facts": facts,
        "generated_by": "deterministic-dataset-template",
    }


class _EvidenceEngine:
    name = "flywire-evidence-review"

    def __init__(self, answer: EngineAnswer) -> None:
        self.answer = answer

    def run(self, query: str) -> EngineAnswer:
        return self.answer


def evaluate_connectome_answer(answer: EngineAnswer) -> dict:
    """Score supplied text against fresh server-owned snapshot facts."""
    brief = build_connectome_brief()
    case = BenchmarkCase(**brief["case"])
    submitted = EngineAnswer(
        text=answer.text,
        citations=list(answer.citations),
        metadata={"source": "user-submitted", "generated_by_app": False, "dataset_version": 783},
    )
    run = run_benchmark(
        [case], [_EvidenceEngine(submitted)],
        [RegexScorer(), CitationCountScorer(), WordCountScorer()], judge=None,
    )
    return {
        "run": to_json(run), "markdown": to_markdown(run), "mode": "evidence",
        "case": brief["case"], "facts": brief["facts"],
    }
