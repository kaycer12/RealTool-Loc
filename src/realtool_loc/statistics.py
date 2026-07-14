"""Small offline aggregations used to verify the released result tables."""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path


def _weighted_mean(rows: list[dict[str, str]], value_key: str, count_key: str) -> tuple[float, int]:
    total = sum(int(row[count_key]) for row in rows)
    if total == 0:
        raise ValueError(f"Cannot aggregate {value_key}: total {count_key} is zero")
    weighted = sum(float(row[value_key]) * int(row[count_key]) for row in rows)
    return weighted / total, total


def summarize_main_table(path: Path) -> dict[str, dict[str, float | int]]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError(f"Result table is empty: {path}")

    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[row["method"]].append(row)

    summary: dict[str, dict[str, float | int]] = {}
    for method, method_rows in sorted(groups.items()):
        core, core_n = _weighted_mean(method_rows, "core_pass", "core_n")
        hybrid, hybrid_n = _weighted_mean(method_rows, "hybrid_faithfulness", "gemini_n")
        naturalness, naturalness_n = _weighted_mean(method_rows, "naturalness", "naturalness_n")
        summary[method] = {
            "corepass": core,
            "core_n": core_n,
            "hybrid": hybrid,
            "hybrid_n": hybrid_n,
            "naturalness": naturalness,
            "naturalness_n": naturalness_n,
        }
    return summary


def headline_differences(summary: dict[str, dict[str, float | int]]) -> dict[str, float]:
    elv = summary["extract_localize_verify"]
    protected = summary["protected_slot_realization"]
    return {
        "corepass_elv": float(elv["corepass"]),
        "corepass_protected": float(protected["corepass"]),
        "corepass_delta_pp": 100.0 * (float(protected["corepass"]) - float(elv["corepass"])),
        "hybrid_elv": float(elv["hybrid"]),
        "hybrid_protected": float(protected["hybrid"]),
        "hybrid_delta_pp": 100.0 * (float(protected["hybrid"]) - float(elv["hybrid"])),
        "naturalness_elv": float(elv["naturalness"]),
        "naturalness_protected": float(protected["naturalness"]),
        "naturalness_delta": float(protected["naturalness"]) - float(elv["naturalness"]),
    }
