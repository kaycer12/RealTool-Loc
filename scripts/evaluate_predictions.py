#!/usr/bin/env python3
"""Evaluate a JSONL prediction file with the released RealTool-Loc rules."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from realtool_loc.evaluator import evaluate_predictions  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=ROOT / "data" / "realtool_loc.jsonl")
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--evaluation-policy", choices=["strict", "relaxed"], default="strict")
    args = parser.parse_args()

    report = evaluate_predictions(args.data, args.predictions, evaluation_policy=args.evaluation_policy)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    summary = {"n_predictions": report["n_predictions"], "overall": report["overall"]}
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
