# Released result tables

The CSV files in this directory are frozen analysis outputs used by the paper:

- `main_table.csv`: model-by-strategy CorePass, auxiliary faithfulness, Hybrid Faithfulness, and naturalness.
- `method_summary.csv`: pooled strategy-level results.
- `significance.csv`: released pairwise statistical comparisons.
- `language_results.csv`: language-level metrics.
- `language_tradeoff.csv`: Protected-Slot minus baseline changes by language.
- `model_level_significance.csv`: model-level direction and significance summaries.
- `reported_aggregates.json`: unrounded headline values used by the offline check.

Run:

```bash
PYTHONPATH=src python3 scripts/reproduce_results.py --check
```

This verifies aggregation arithmetic. The tables contain operational scores from frozen model outputs and external judgments; reproducing the underlying hosted-model responses is outside the exact offline boundary.
