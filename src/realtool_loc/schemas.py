"""Dataset loading, validation, and deterministic split construction."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


FIELD_ROLES = {"immutable", "entity", "semantic", "status"}
EXPECTED_LANGUAGES = {"zh", "ja", "th", "id", "bo", "ug", "mn-Mong", "kk-Arab"}
REQUIRED_TASK_KEYS = {
    "id",
    "domain",
    "source_record_id",
    "user_language",
    "expected_answer_language",
    "user_query",
    "tool_name",
    "tool_result",
    "field_specs",
    "required_fields",
    "forbidden_hallucinations",
}


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON in {path} at line {line_number}: {exc}") from exc
            if not isinstance(value, dict):
                raise ValueError(f"Expected an object in {path} at line {line_number}")
            rows.append(value)
    return rows


def _validate_tasks(rows: list[dict], *, expected_rows: int | None) -> dict:
    if expected_rows is not None and len(rows) != expected_rows:
        raise ValueError(f"Expected {expected_rows} rows, found {len(rows)}")
    if not rows:
        raise ValueError("Dataset is empty")

    ids: set[str] = set()
    domains: set[str] = set()
    languages: set[str] = set()
    for index, row in enumerate(rows, start=1):
        missing_keys = sorted(REQUIRED_TASK_KEYS - row.keys())
        if missing_keys:
            raise ValueError(f"Row {index} is missing required keys: {', '.join(missing_keys)}")

        sample_id = row["id"]
        if not isinstance(sample_id, str) or not sample_id:
            raise ValueError(f"Row {index} has an invalid id")
        if sample_id in ids:
            raise ValueError(f"Duplicate task id: {sample_id}")
        ids.add(sample_id)

        specs = row["field_specs"]
        if not isinstance(specs, list):
            raise ValueError(f"Task {sample_id} field_specs must be a list")
        spec_paths: set[str] = set()
        for spec in specs:
            if not isinstance(spec, dict) or not spec.get("path"):
                raise ValueError(f"Task {sample_id} has a field specification without a path")
            role = spec.get("role")
            if role not in FIELD_ROLES:
                raise ValueError(f"Task {sample_id} has unsupported field role: {role}")
            spec_paths.add(spec["path"])

        uncovered = sorted(set(row["required_fields"]) - spec_paths)
        if uncovered:
            raise ValueError(f"Task {sample_id} has required fields without specs: {', '.join(uncovered)}")

        domains.add(str(row["domain"]))
        languages.add(str(row["user_language"]))

    return {
        "rows": len(rows),
        "unique_ids": len(ids),
        "domains": len(domains),
        "languages": sorted(languages),
    }


def validate_main(rows: list[dict], *, expected_rows: int | None = 1024) -> dict:
    summary = _validate_tasks(rows, expected_rows=expected_rows)
    languages = set(summary["languages"])
    if expected_rows == 1024 and languages != EXPECTED_LANGUAGES:
        raise ValueError(f"Unexpected main-dataset languages: {sorted(languages)}")
    if expected_rows == 1024 and summary["domains"] != 32:
        raise ValueError(f"Expected 32 domains, found {summary['domains']}")
    return summary


def validate_attribution(rows: list[dict], *, expected_rows: int | None = 448) -> dict:
    summary = _validate_tasks(rows, expected_rows=expected_rows)
    condition_counts = Counter(row.get("attribution_condition") for row in rows)
    if None in condition_counts:
        raise ValueError("Attribution row is missing attribution_condition")
    if expected_rows == 448 and (len(condition_counts) != 7 or set(condition_counts.values()) != {64}):
        raise ValueError(f"Unexpected attribution condition balance: {dict(condition_counts)}")
    summary["conditions"] = len(condition_counts)
    summary["condition_counts"] = dict(sorted(condition_counts.items()))
    return summary


def split_ids(rows: list[dict]) -> tuple[list[str], list[str]]:
    dev_ids: list[str] = []
    test_ids: list[str] = []
    record_split: dict[str, str] = {}
    for row in rows:
        record_id = str(row["source_record_id"])
        task_id = str(row["id"])
        suffix = task_id.rsplit("_", 1)[-1]
        if suffix in {"001", "003"}:
            split = "dev"
            dev_ids.append(row["id"])
        elif suffix in {"002", "004"}:
            split = "test"
            test_ids.append(row["id"])
        else:
            raise ValueError(f"Unsupported task-id suffix in {task_id}")
        previous = record_split.setdefault(record_id, split)
        if previous != split:
            raise ValueError(f"Source record appears in both splits: {record_id}")

    if len(dev_ids) + len(test_ids) != len(rows):
        raise ValueError("Split does not cover every task")
    if set(dev_ids) & set(test_ids):
        raise ValueError("Development and test task IDs overlap")
    return sorted(dev_ids), sorted(test_ids)
