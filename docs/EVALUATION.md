# Evaluation protocol

## Deterministic checks

For an answer `a`, CorePass is the conjunction

```text
L(a) × C(a) × I(a) × E(a) × S(a) × Z(a) × H(a)
```

where:

- `L`: expected language and script;
- `C`: all required fields are covered;
- `I`: immutable fields are preserved;
- `E`: entity identity is retained;
- `S`: semantic values are retained;
- `Z`: fields marked as requiring localization are not left only as raw source labels;
- `H`: none of the task's predefined unsupported claims appears.

The evaluator reports both the seven components and their conjunction. Fractional component scores are diagnostic; CorePass is true only when all seven components equal one.

## Strict and relaxed policies

`strict` is the exact operational contract used for the primary deterministic score. Immutable fields must appear as stored, while entities and semantic values may use task-level accepted variants.

`relaxed` additionally allows documented natural-language equivalents for selected metadata fields: country codes, currencies, and language codes. DOI, ISBN, package names, versions, URLs, and error codes remain exact-copy fields.

The evaluator version is included in every output report. Strict and relaxed results should never be combined without naming the policy.

## Auxiliary judgments

The released result tables also contain semantic-faithfulness, Hybrid Faithfulness, and naturalness columns produced by external model judgments in the paper experiment. These signals remain separate from the deterministic evaluator:

- Hybrid Faithfulness requires both relaxed CorePass and a positive semantic-faithfulness judgment.
- Naturalness is measured on a five-point scale and does not override factual failure.
- The naturalness protocol judges all four strategies for the same task together; semantic-faithfulness sampling was strategy-specific in the reported experiment.

This artifact freezes the resulting aggregate tables but does not hard-code a commercial model endpoint. External model judgments are not deterministic and may vary by model version, provider, and sampling implementation.

## Input and output

The evaluator accepts JSONL records containing `id`, `method`, and `answer`. It returns:

- evaluator version and selected policy;
- method-level, language-level, and domain-level aggregates;
- per-sample diagnostic records with missing fields, corruptions, mismatches, underlocalized fields, and forbidden-pattern hits.

## Important limitations

- Language detection is a documented collection of script and lexical heuristics, not a general language-identification model.
- Predefined unsupported-claim patterns provide a lower bound on hallucination; absence of a hit does not prove that an answer contains no unsupported content.
- Surface matching can produce boundary cases. For example, a short exact code may coincidentally occur inside another retained string. The release preserves the paper evaluator rather than silently changing historical scores.
- Accepted variants cannot enumerate every valid localization.
- Protected-Slot can reinsert open source-language semantic text under the current contract. A future schema should separate literal preservation from mandatory semantic translation.
