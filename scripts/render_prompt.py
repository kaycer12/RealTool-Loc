#!/usr/bin/env python3
"""Render provider-neutral chat messages for one benchmark task."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from realtool_loc.messages import METHODS, build_messages  # noqa: E402
from realtool_loc.schemas import load_jsonl  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample-id", required=True)
    parser.add_argument("--method", choices=sorted(METHODS), required=True)
    args = parser.parse_args()

    samples = {row["id"]: row for row in load_jsonl(ROOT / "data" / "realtool_loc.jsonl")}
    if args.sample_id not in samples:
        raise SystemExit(f"Unknown sample ID: {args.sample_id}")
    messages = build_messages(samples[args.sample_id], args.method, ROOT / "prompts")
    print(json.dumps(messages, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
