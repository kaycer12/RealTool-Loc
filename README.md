# RealTool-Loc

RealTool-Loc is a diagnostic benchmark for the final answer produced after a tool has already executed successfully. It tests whether a multilingual assistant can express a curated static API-style record associated with a public tool or service while preserving identifiers, entities, semantic values, and localizable statuses.

This repository is a self-contained anonymous research artifact. It contains no model-provider credentials, private endpoints, author metadata, or live API dependencies.

## Contents

- `data/realtool_loc.jsonl`: 1,024 main tasks associated with 32 public tools and services.
- `data/attribution.jsonl`: 448 controlled-attribution tasks.
- `data/splits/`: fixed, record-disjoint development and test task IDs.
- `prompts/`: the four released realization strategies.
- `src/realtool_loc/evaluator.py`: strict and relaxed deterministic evaluation.
- `src/realtool_loc/protected_slots.py`: Protected-Slot substitution and restoration.
- `results/`: frozen aggregate tables used to check the reported arithmetic.
- `tests/`: offline regression, integrity, reproduction, and anonymity tests.

The main benchmark combines 32 sources, four curated static records per source, and eight language settings: Chinese, Japanese, Thai, Indonesian, Tibetan, Uyghur, traditional Mongolian, and Arabic-script Kazakh.

## Quick start

The offline artifact requires Python 3.10 or newer and has no runtime dependencies outside the standard library.

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 scripts/validate_dataset.py
PYTHONPATH=src python3 scripts/make_splits.py --check
PYTHONPATH=src python3 scripts/reproduce_results.py --check
PYTHONPATH=src python3 scripts/audit_release.py
```

Evaluate the included smoke predictions:

```bash
PYTHONPATH=src python3 scripts/evaluate_predictions.py \
  --predictions examples/predictions.jsonl \
  --output reports/example.strict.json \
  --evaluation-policy strict

PYTHONPATH=src python3 scripts/evaluate_predictions.py \
  --predictions examples/predictions.jsonl \
  --output reports/example.relaxed.json \
  --evaluation-policy relaxed
```

Render the exact provider-neutral messages for one strategy:

```bash
PYTHONPATH=src python3 scripts/render_prompt.py \
  --sample-id weather_zh_001 \
  --method protected_slot_realization
```

## Prediction format

Predictions are JSON Lines records with three required fields:

```json
{"id": "weather_zh_001", "method": "my_method", "answer": "..."}
```

The evaluator joins each prediction to the released task by `id`. Unknown task IDs are rejected.

## Evaluation

CorePass is the conjunction of seven operational checks:

1. target-language/script control;
2. required-field coverage;
3. immutable-value preservation;
4. entity fidelity;
5. semantic fidelity;
6. localization of fields marked as requiring localization;
7. absence of predefined unsupported claims.

The `strict` policy preserves the paper's exact-copy contract. The `relaxed` policy additionally accepts documented natural-language equivalents for selected metadata codes such as country, currency, and language codes. See `docs/EVALUATION.md` for the full boundary and known limitations.

## Released strategies

- `naive`: use the shared benchmark payload without an explicit field-policy system instruction.
- `field_constrained`: expose required fields and field roles.
- `extract_localize_verify`: instruct the model to extract evidence, realize it, and verify coverage within one call.
- `protected_slot_realization`: replace eligible evidence values with deterministic placeholders during generation, then restore the original values.

The repository renders messages but intentionally does not select a model provider. Users can send the returned two-message array to any compatible chat interface, then store the final answer in the prediction format above.

## Reproducing released numbers

`scripts/reproduce_results.py --check` recomputes the headline method-level values from `results/main_table.csv` and checks them against `results/reported_aggregates.json`. It reproduces the reported aggregate arithmetic without requiring paid model calls.

This release does not claim bitwise reproducibility of proprietary model generation or external LLM judgments. It provides the data contracts, prompts, deterministic evaluator, frozen aggregate result tables, and smoke predictions needed to audit the offline portion. See `docs/REPRODUCIBILITY.md`.

## Data and licensing

The benchmark uses curated, compact API-style records associated with public tools and services. Provider, documentation, and request URLs are retained as source context, but this release does not contain original HTTP responses or per-record response hashes. The legacy `retrieved_at` value is dataset-construction metadata, not a verified fetch time for each record. Benchmark-authored annotations and code have separate licenses; associated upstream material remains subject to its provider's terms. See `LICENSE-CODE`, `LICENSE-DATA`, and `THIRD_PARTY_NOTICES.md`.

Citation metadata is intentionally omitted during anonymous review.
