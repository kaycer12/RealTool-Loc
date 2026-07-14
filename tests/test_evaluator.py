from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from realtool_loc.evaluator import evaluate_answer  # noqa: E402
from realtool_loc.schemas import load_jsonl  # noqa: E402


class EvaluatorRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        rows = load_jsonl(ROOT / "data" / "realtool_loc.jsonl")
        cls.samples = {row["id"]: row for row in rows}

    def test_reference_answer_passes_all_seven_core_checks(self) -> None:
        sample = self.samples["weather_zh_001"]
        result = evaluate_answer(sample, sample["optional_reference_answer"], "reference")
        metrics = [
            "language_accuracy",
            "field_coverage",
            "immutable_preservation",
            "entity_fidelity",
            "semantic_fidelity",
            "localization_quality",
            "hallucination_free",
        ]
        self.assertTrue(result["core_pass"])
        self.assertTrue(all(result[name] == 1.0 for name in metrics))

    def test_immutable_corruption_fails_corepass(self) -> None:
        sample = self.samples["scholarly_zh_001"]
        answer = sample["optional_reference_answer"].replace("10.1038/nature14539", "10.1038/wrong")
        result = evaluate_answer(sample, answer, "corrupt")
        self.assertIn("doi", result["immutable_corruptions"])
        self.assertFalse(result["core_pass"])

    def test_localized_entity_and_date_are_accepted(self) -> None:
        sample = self.samples["weather_zh_001"]
        answer = "东京在2025年7月1日最高33.9°C，最低25.8°C，降水1.0毫米，天气代码53，状况为中等毛毛雨。"
        result = evaluate_answer(sample, answer, "localized")
        self.assertEqual(result["entity_fidelity"], 1.0)
        self.assertEqual(result["semantic_fidelity"], 1.0)
        self.assertTrue(result["core_pass"])

    def test_decimal_and_integer_boundaries_are_not_loosened(self) -> None:
        sample = self.samples["weather_zh_001"]
        answer = "东京在2025年7月1日最高339°C，最低25.8°C，降水1.0毫米，天气代码1530，状况为中等毛毛雨。"
        result = evaluate_answer(sample, answer, "bad_numbers")
        self.assertIn("temperature_2m_max", result["semantic_mismatches"])
        self.assertIn("weather_code", result["semantic_mismatches"])
        self.assertFalse(result["core_pass"])

    def test_underlocalized_status_is_reported(self) -> None:
        sample = self.samples["food_zh_001"]
        answer = "Open Food Facts product found。条码3017620422003，商品名Nutella，品牌Nutella、Ferrero、Yum yum，Nutri-Score等级E。"
        result = evaluate_answer(sample, answer, "raw_status")
        self.assertIn("status_verbose", result["underlocalized_fields"])
        self.assertEqual(result["localization_quality"], 0.0)
        self.assertFalse(result["core_pass"])

    def test_wrong_script_is_rejected(self) -> None:
        sample = self.samples["weather_mn-Mong_001"]
        answer = sample["optional_reference_answer"] + " Энэ өгүүлбэр кирилл монгол бичгээр байна."
        result = evaluate_answer(sample, answer, "wrong_script")
        self.assertEqual(result["target_script_present"], 1.0)
        self.assertEqual(result["wrong_script_free"], 0.0)
        self.assertEqual(result["language_accuracy"], 0.0)

    def test_relaxed_policy_accepts_localized_currency_code(self) -> None:
        sample = self.samples["crypto_market_zh_001"]
        answer = sample["optional_reference_answer"].replace("currency: usd", "currency: 美元")
        strict = evaluate_answer(sample, answer, "localized_code", evaluation_policy="strict")
        relaxed = evaluate_answer(sample, answer, "localized_code", evaluation_policy="relaxed")
        self.assertIn("currency", strict["immutable_corruptions"])
        self.assertFalse(strict["core_pass"])
        self.assertNotIn("currency", relaxed["immutable_corruptions"])
        self.assertTrue(relaxed["core_pass"])

    def test_empty_answer_fails_without_crashing(self) -> None:
        sample = self.samples["weather_zh_001"]
        result = evaluate_answer(sample, "", "empty")
        self.assertEqual(result["language_accuracy"], 0.0)
        self.assertEqual(result["field_coverage"], 0.0)
        self.assertFalse(result["core_pass"])


if __name__ == "__main__":
    unittest.main()
