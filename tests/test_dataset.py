from __future__ import annotations

import copy
import sys
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from realtool_loc.schemas import (  # noqa: E402
    load_jsonl,
    split_ids,
    validate_attribution,
    validate_main,
)


class DatasetIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.main_rows = load_jsonl(ROOT / "data" / "realtool_loc.jsonl")
        cls.attribution_rows = load_jsonl(ROOT / "data" / "attribution.jsonl")

    def test_main_dataset_has_expected_balanced_shape(self) -> None:
        summary = validate_main(self.main_rows)
        self.assertEqual(summary["rows"], 1024)
        self.assertEqual(summary["unique_ids"], 1024)
        self.assertEqual(summary["domains"], 32)
        self.assertEqual(
            summary["languages"],
            ["bo", "id", "ja", "kk-Arab", "mn-Mong", "th", "ug", "zh"],
        )
        counts = Counter(row["user_language"] for row in self.main_rows)
        self.assertEqual(set(counts.values()), {128})

    def test_attribution_dataset_has_seven_balanced_conditions(self) -> None:
        summary = validate_attribution(self.attribution_rows)
        self.assertEqual(summary["rows"], 448)
        self.assertEqual(summary["unique_ids"], 448)
        self.assertEqual(summary["conditions"], 7)
        counts = Counter(row["attribution_condition"] for row in self.attribution_rows)
        self.assertEqual(set(counts.values()), {64})

    def test_split_is_exhaustive_balanced_and_record_disjoint(self) -> None:
        dev_ids, test_ids = split_ids(self.main_rows)
        self.assertEqual(len(dev_ids), 512)
        self.assertEqual(len(test_ids), 512)
        self.assertFalse(set(dev_ids) & set(test_ids))
        self.assertEqual(set(dev_ids) | set(test_ids), {row["id"] for row in self.main_rows})

        split_by_record: dict[str, set[str]] = {}
        for row in self.main_rows:
            split = "dev" if row["id"] in dev_ids else "test"
            split_by_record.setdefault(row["source_record_id"], set()).add(split)
        self.assertTrue(all(len(splits) == 1 for splits in split_by_record.values()))

    def test_missing_required_task_key_is_rejected(self) -> None:
        broken = copy.deepcopy(self.main_rows[:1])
        del broken[0]["field_specs"]
        with self.assertRaisesRegex(ValueError, "field_specs"):
            validate_main(broken, expected_rows=None)


if __name__ == "__main__":
    unittest.main()
