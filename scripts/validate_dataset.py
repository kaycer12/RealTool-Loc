#!/usr/bin/env python3
"""Validate the released benchmark and attribution datasets."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from realtool_loc.schemas import load_jsonl, validate_attribution, validate_main  # noqa: E402


def main() -> None:
    payload = {
        "main": validate_main(load_jsonl(ROOT / "data" / "realtool_loc.jsonl")),
        "attribution": validate_attribution(load_jsonl(ROOT / "data" / "attribution.jsonl")),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
