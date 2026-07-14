#!/usr/bin/env python3
"""Create or check the deterministic RealTool-Loc development/test splits."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from realtool_loc.schemas import load_jsonl, split_ids, validate_main  # noqa: E402


def read_ids(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_ids(path: Path, values: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(f"{value}\n" for value in values), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Compare regenerated IDs with committed split files.")
    args = parser.parse_args()

    rows = load_jsonl(ROOT / "data" / "realtool_loc.jsonl")
    validate_main(rows)
    dev_ids, test_ids = split_ids(rows)
    split_dir = ROOT / "data" / "splits"
    paths = {"dev": split_dir / "dev_ids.txt", "test": split_dir / "test_ids.txt"}

    if args.check:
        if read_ids(paths["dev"]) != dev_ids or read_ids(paths["test"]) != test_ids:
            raise SystemExit("Committed split files do not match deterministic reconstruction")
        print(f"Split files match: dev={len(dev_ids)} test={len(test_ids)}")
        return

    write_ids(paths["dev"], dev_ids)
    write_ids(paths["test"], test_ids)
    print(f"Wrote split files: dev={len(dev_ids)} test={len(test_ids)}")


if __name__ == "__main__":
    main()
