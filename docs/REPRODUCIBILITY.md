# Reproducibility guide

## Tier 1: exact offline checks

The following operations require only the released files and Python standard library:

```bash
PYTHONPATH=src python3 scripts/validate_dataset.py
PYTHONPATH=src python3 scripts/make_splits.py --check
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 scripts/reproduce_results.py --check
PYTHONPATH=src python3 scripts/audit_release.py
```

These commands verify dataset shape, unique IDs, field contracts, split isolation, evaluator regression behavior, Protected-Slot round trips, frozen aggregate arithmetic, and release anonymity.

They reproduce the offline benchmark object and reported arithmetic, not the provenance of a verbatim HTTP response. The release retains source-context URLs but does not include original response bodies or per-record response hashes.

## Tier 2: evaluate new model outputs

Use `scripts/render_prompt.py` to obtain the exact two-message input for any released strategy. Send those messages to a model using a provider chosen by the evaluator, store only the final visible answer, and write one JSON object per line:

```json
{"id": "task_id", "method": "strategy_name", "answer": "final answer"}
```

Then run `scripts/evaluate_predictions.py`. No provider SDK is required by this repository.

For Protected-Slot, call `protect_sample` before generation and `restore_answer` on the returned visible answer. `build_messages` performs the protection step automatically when rendering the protected strategy.

## Tier 3: external judgments

Recreating semantic-faithfulness or naturalness judgments requires an independently configured model provider. Exact agreement is not guaranteed because hosted models and serving stacks change. The operational definitions and sampling boundary are documented in `docs/EVALUATION.md`; the released aggregate tables preserve the values used for paper analysis.

## Frozen results

`results/main_table.csv` contains one row per model and strategy. `results/method_summary.csv` contains pooled method-level values. Additional files report significance and language-level analyses. `results/reported_aggregates.json` stores the unrounded headline values checked by `scripts/reproduce_results.py`.

The repository does not include private request logs, hidden reasoning, retry caches, credentials, or billing metadata. Those files are neither necessary for offline evaluation nor appropriate for an anonymous public artifact.
