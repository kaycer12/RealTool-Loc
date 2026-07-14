"""Provider-neutral prompt rendering for the four released strategies."""

from __future__ import annotations

import json
from pathlib import Path

from .protected_slots import protect_sample


METHODS = {"naive", "field_constrained", "extract_localize_verify", "protected_slot_realization"}


def build_messages(sample: dict, method: str, prompt_dir: Path) -> list[dict[str, str]]:
    if method not in METHODS:
        raise ValueError(f"Unsupported method: {method}")
    rendered_sample = protect_sample(sample) if method == "protected_slot_realization" else sample
    prompt_path = prompt_dir / f"{method}.md"
    system_prompt = prompt_path.read_text(encoding="utf-8")

    field_policy = [
        {
            "path": spec.get("path"),
            "role": spec.get("role"),
            "required": spec.get("required", True),
            "description": spec.get("description"),
            "requires_localization": spec.get("requires_localization", False),
        }
        for spec in rendered_sample.get("field_specs", [])
    ]
    user_payload = {
        "id": rendered_sample["id"],
        "user_language": rendered_sample["user_language"],
        "expected_answer_language": rendered_sample["expected_answer_language"],
        "user_query": rendered_sample["user_query"],
        "tool_name": rendered_sample["tool_name"],
        "tool_result": rendered_sample["tool_result"],
        "required_fields": rendered_sample["required_fields"],
        "preserve_exact_fields": rendered_sample["preserve_exact_fields"],
        "localizable_fields": rendered_sample["localizable_fields"],
        "forbidden_hallucinations": rendered_sample["forbidden_hallucinations"],
    }
    for optional_key in [
        "immutable_fields",
        "entity_fields",
        "semantic_fields",
        "field_descriptions",
        "tool_source",
        "protected_slots",
    ]:
        if optional_key in rendered_sample:
            user_payload[optional_key] = rendered_sample[optional_key]
    if field_policy:
        user_payload["field_policy"] = field_policy

    return [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": "Generate the final user-facing answer for this post-tool stage. Return only the answer.\n"
            + json.dumps(user_payload, ensure_ascii=False, indent=2),
        },
    ]
