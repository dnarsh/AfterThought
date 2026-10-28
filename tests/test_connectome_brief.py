"""Source-count consistency and meaningful failures through the actual scorers."""

import unittest
from unittest.mock import patch

from deep_research_bench import EngineAnswer
from deep_research_bench.connectome import ConnectomeError, SOURCE_URL
from deep_research_bench.connectome_brief import build_connectome_brief, evaluate_connectome_answer


def snapshot(total=10, gaba=3):
    return {
        "dataset": "FlyWire FAFB v783", "source_url": SOURCE_URL, "snapshot": True,
        "total_neurons": total, "matching_neurons": gaba,
        "neurotransmitters": [{"name": "GABA", "count": gaba}, {"name": "ACH", "count": total - gaba}],
        "retrieved_at": "2026-10-28T04:02:28+00:00", "neurons": [],
    }


class ConnectomeBriefTests(unittest.TestCase):
    def test_actual_query_filters_and_counts_feed_case_and_brief(self):
        with patch("deep_research_bench.connectome_brief.query_neurons", return_value=snapshot()) as query:
            brief = build_connectome_brief()
        query.assert_called_once_with(transmitter="GABA", limit=1)
        self.assertEqual(brief["case"]["id"], "flywire-gaba-evidence")
        self.assertEqual(brief["facts"]["total_neurons"], 10)
        self.assertEqual(brief["facts"]["gaba_neurons"], 3)
        self.assertEqual(brief["facts"]["percentage"], 30.0)
        self.assertEqual(brief["facts"]["version"], 783)
        self.assertEqual(brief["answer"]["citations"], [SOURCE_URL])
        self.assertIn("30.00%", brief["answer"]["text"])
        self.assertTrue(110 <= len(brief["answer"]["text"].split()) <= 160)
        self.assertEqual(brief["generated_by"], "deterministic-dataset-template")

    def test_source_numbers_are_not_hardcoded(self):
        with patch("deep_research_bench.connectome_brief.query_neurons", return_value=snapshot(2000, 777)):
            brief = build_connectome_brief()
        self.assertEqual(brief["facts"]["percentage"], 38.85)
        self.assertIn("2,000 neurons", brief["answer"]["text"])
        self.assertIn("777 have GABA", brief["answer"]["text"])
        self.assertIn("38.85%", brief["answer"]["text"])

    def test_source_consistency_fails_closed(self):
        variants = []
        bad = snapshot(); bad["total_neurons"] = 11; variants.append(bad)
        bad = snapshot(); bad["matching_neurons"] = 2; variants.append(bad)
        bad = snapshot(); bad["source_url"] = "https://attacker.invalid/archive"; variants.append(bad)
        bad = snapshot(); bad["snapshot"] = False; variants.append(bad)
        bad = snapshot(); bad["neurotransmitters"].append({"name": "GABA", "count": 0}); variants.append(bad)
        bad = snapshot(); bad["neurotransmitters"][0]["count"] = True; variants.append(bad)
        for value in variants:
            with self.subTest(value=value), patch("deep_research_bench.connectome_brief.query_neurons", return_value=value):
                with self.assertRaises(ConnectomeError):
                    build_connectome_brief()

    def test_real_runner_scores_complete_brief_and_meaningful_mutations(self):
        with patch("deep_research_bench.connectome_brief.query_neurons", return_value=snapshot()):
            brief = build_connectome_brief()
            good = brief["answer"]
            result = evaluate_connectome_answer(EngineAnswer(**good))
            self.assertTrue(result["run"]["cells"][0]["passed"])
            self.assertEqual(result["run"]["engines"], ["flywire-evidence-review"])
            self.assertIsNone(result["run"]["judge"])
            self.assertEqual(result["mode"], "evidence")
            self.assertEqual(result["run"]["cells"][0]["answer_metadata"]["source"], "user-submitted")
            mutations = [
                (good["text"].replace("3 have GABA", "4 have GABA"), good["citations"], "regex"),
                (good["text"].replace("30.00%", "99.00%"), good["citations"], "regex"),
                (good["text"].replace("not a live neural simulation", "a live neural simulation"), good["citations"], "regex"),
                (good["text"], [], "citation_count"),
                ("GABA", good["citations"], "word_count"),
            ]
            for text, citations, scorer in mutations:
                with self.subTest(scorer=scorer, text=text[:30]):
                    cell = evaluate_connectome_answer(EngineAnswer(text=text, citations=citations))["run"]["cells"][0]
                    self.assertFalse(cell["passed"])
                    self.assertFalse(cell["scorers"][scorer]["passed"])

    def test_network_failure_does_not_invent_a_brief(self):
        with patch("deep_research_bench.connectome_brief.query_neurons", side_effect=ConnectomeError("unavailable")):
            with self.assertRaises(ConnectomeError):
                build_connectome_brief()


if __name__ == "__main__":
    unittest.main()
