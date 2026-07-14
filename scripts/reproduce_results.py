#!/usr/bin/env python3
"""Recompute the released headline aggregates from the frozen result table."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from realtool_loc.statistics import headline_differences, summarize_main_table  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail when recomputed values differ from the frozen snapshot.")
    args = parser.parse_args()

    computed = headline_differences(summarize_main_table(ROOT / "results" / "main_table.csv"))
    expected = json.loads((ROOT / "results" / "reported_aggregates.json").read_text(encoding="utf-8"))
    print(json.dumps(computed, indent=2, sort_keys=True))

    mismatches = {
        key: {"expected": expected[key], "computed": computed.get(key)}
        for key in expected
        if key not in computed or not math.isclose(float(expected[key]), float(computed[key]), rel_tol=0.0, abs_tol=1e-12)
    }
    if args.check and mismatches:
        raise SystemExit("Aggregate mismatch:\n" + json.dumps(mismatches, indent=2, sort_keys=True))
    if not mismatches:
        print("All frozen aggregates match.")


if __name__ == "__main__":
    main()
