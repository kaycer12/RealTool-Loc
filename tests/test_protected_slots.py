from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from realtool_loc.messages import build_messages  # noqa: E402
from realtool_loc.protected_slots import (  # noqa: E402
    protect_sample,
    protected_slot_map,
    restore_answer,
)
from realtool_loc.schemas import load_jsonl  # noqa: E402


class ProtectedSlotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        rows = load_jsonl(ROOT / "data" / "realtool_loc.jsonl")
        cls.sample = next(row for row in rows if row["id"] == "weather_zh_001")

    def test_slot_map_protects_evidence_but_not_localizable_status(self) -> None:
        slots = protected_slot_map(self.sample)
        self.assertIn("location_name", slots)
        self.assertIn("date", slots)
        self.assertIn("weather_code", slots)
        self.assertNotIn("weather_condition", slots)
        self.assertEqual(slots["location_name"], "[[FIELD_location_name]]")

    def test_protect_sample_is_non_mutating_and_updates_contract_values(self) -> None:
        original_result = dict(self.sample["tool_result"])
        protected = protect_sample(self.sample)
        self.assertEqual(self.sample["tool_result"], original_result)
        self.assertEqual(protected["tool_result"]["location_name"], "[[FIELD_location_name]]")
        spec = next(item for item in protected["field_specs"] if item["path"] == "location_name")
        self.assertEqual(spec["value"], "[[FIELD_location_name]]")
        self.assertEqual(spec["accepted_values"], ["[[FIELD_location_name]]"])

    def test_restoration_round_trips_exact_values(self) -> None:
        answer = "[[FIELD_location_name]]：[[FIELD_date]]，代码[[FIELD_weather_code]]。"
        restored = restore_answer(self.sample, answer)
        self.assertEqual(restored, "Tokyo：2025-07-01，代码53。")

    def test_restoration_does_not_invent_omitted_values(self) -> None:
        answer = "这里没有占位符。"
        self.assertEqual(restore_answer(self.sample, answer), answer)

    def test_all_four_methods_render_provider_neutral_messages(self) -> None:
        for method in ["naive", "field_constrained", "extract_localize_verify", "protected_slot_realization"]:
            with self.subTest(method=method):
                messages = build_messages(self.sample, method, ROOT / "prompts")
                self.assertEqual([item["role"] for item in messages], ["system", "user"])
                self.assertTrue(messages[0]["content"].strip())
                prefix, payload_text = messages[1]["content"].split("\n", 1)
                self.assertEqual(prefix, "Generate the final user-facing answer for this post-tool stage. Return only the answer.")
                payload = json.loads(payload_text)
                self.assertEqual(payload["id"], self.sample["id"])
                if method == "protected_slot_realization":
                    self.assertEqual(payload["tool_result"]["location_name"], "[[FIELD_location_name]]")
                else:
                    self.assertEqual(payload["tool_result"]["location_name"], "Tokyo")


if __name__ == "__main__":
    unittest.main()
