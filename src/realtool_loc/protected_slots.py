"""Deterministic value protection used by Protected-Slot Realization."""

from __future__ import annotations

import json


PROTECTED_ROLES = {"immutable", "semantic", "entity"}


def protected_slot_map(sample: dict) -> dict[str, str]:
    slots: dict[str, str] = {}
    localizable = set(sample.get("localizable_fields", []))
    for spec in sample.get("field_specs", []):
        path = spec.get("path")
        value = spec.get("value")
        role = spec.get("role")
        if not path or path in localizable or role not in PROTECTED_ROLES or value in ("", None):
            continue
        slots[path] = f"[[FIELD_{path}]]"
    return slots


def protect_sample(sample: dict) -> dict:
    slots = protected_slot_map(sample)
    if not slots:
        return json.loads(json.dumps(sample, ensure_ascii=False))

    protected = json.loads(json.dumps(sample, ensure_ascii=False))
    for path, placeholder in slots.items():
        if path in protected.get("tool_result", {}):
            protected["tool_result"][path] = placeholder
        for spec in protected.get("field_specs", []):
            if spec.get("path") == path:
                spec["value"] = placeholder
                spec["accepted_values"] = [placeholder]
        if path in protected.get("evaluation_values", {}):
            protected["evaluation_values"][path] = [placeholder]

    protected["protected_slots"] = [
        {
            "path": path,
            "placeholder": placeholder,
            "role": next(
                (spec.get("role") for spec in sample.get("field_specs", []) if spec.get("path") == path),
                None,
            ),
        }
        for path, placeholder in slots.items()
    ]
    return protected


def restore_answer(sample: dict, answer: str) -> str:
    restored = answer
    values = sample.get("tool_result", {})
    for path, placeholder in protected_slot_map(sample).items():
        restored = restored.replace(placeholder, str(values.get(path, "")))
    return restored
