from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from realtool_loc.statistics import headline_differences, summarize_main_table  # noqa: E402


class ResultReproductionTests(unittest.TestCase):
    def test_headline_values_reproduce_released_results(self) -> None:
        summary = summarize_main_table(ROOT / "results" / "main_table.csv")
        headline = headline_differences(summary)
        expected = {
            "corepass_elv": 0.52490234375,
            "corepass_protected": 0.761474609375,
            "corepass_delta_pp": 23.6572265625,
            "hybrid_elv": 0.44642857142857145,
            "hybrid_protected": 0.6420454545454546,
            "hybrid_delta_pp": 19.561688311688316,
            "naturalness_elv": 3.8380681818181817,
            "naturalness_protected": 3.4752435064935066,
            "naturalness_delta": -0.3628246753246751,
        }
        self.assertEqual(set(headline), set(expected))
        for key, value in expected.items():
            with self.subTest(key=key):
                self.assertAlmostEqual(headline[key], value, places=12)

    def test_summary_uses_metric_specific_observation_counts(self) -> None:
        summary = summarize_main_table(ROOT / "results" / "main_table.csv")
        elv = summary["extract_localize_verify"]
        self.assertEqual(elv["core_n"], 4096)
        self.assertEqual(elv["hybrid_n"], 1232)
        self.assertEqual(elv["naturalness_n"], 1232)


if __name__ == "__main__":
    unittest.main()
