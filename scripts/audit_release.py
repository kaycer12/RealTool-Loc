#!/usr/bin/env python3
"""Audit the artifact for anonymity, credential, path, and size leaks."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from realtool_loc.release_audit import audit_tree  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--include-git", action="store_true")
    args = parser.parse_args()
    violations = audit_tree(ROOT, include_git=args.include_git)
    print(json.dumps({"violations": violations, "count": len(violations)}, ensure_ascii=False, indent=2))
    if violations:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
