# RealTool-Loc data card

## Intended use

RealTool-Loc evaluates the post-tool realization stage: a tool has returned a correct structured record, and a model must produce a faithful final answer in the user's language. It is intended for diagnostic evaluation of language control, field coverage, evidence preservation, semantic fidelity, status localization, and predefined unsupported claims.

It is not a benchmark for tool selection, function-call argument correctness, live API reliability, general machine translation, or end-to-end agent task completion.

## Composition

The main release contains 1,024 tasks:

- 32 public tools and services as source contexts;
- four curated static API-style records per source;
- eight language settings;
- four field roles: `immutable`, `entity`, `semantic`, and `status`.

The controlled-attribution release contains 448 rows: 64 base cases under seven conditions that vary an English-versus-multilingual task condition, input representation, and the amount of explicit evidence guidance. The language-condition contrast also changes query wording and the forbidden-pattern list, so it is not an output-language-only intervention.

## Languages

The language settings are Chinese (`zh`), Japanese (`ja`), Thai (`th`), Indonesian (`id`), Tibetan (`bo`), Uyghur (`ug`), traditional Mongolian (`mn-Mong`), and Arabic-script Kazakh (`kk-Arab`). The selection is diagnostic rather than exhaustive and should not be interpreted as broad coverage of multilingual users.

## Construction

Public source contexts were selected for documented compact record schemas, verifiable field obligations, and absence of private user state. Four compact API-style records per source were curated as fixed benchmark inputs. Provider, documentation, and request URLs provide context, but the release does not archive original HTTP responses or per-record response hashes. The legacy `retrieved_at` value records dataset construction rather than a verified fetch time for each record. Field-role maps then assigned required values, accepted variants, and targeted unsupported-claim patterns. Each source record was paired with eight language-specific queries.

Development and test sets each contain 512 tasks. The split is defined at the frozen source-record level, so language variants of the same record cannot cross splits. `scripts/make_splits.py --check` reconstructs and verifies the committed ID lists.

## Fields

Each task includes:

- a target-language user query;
- a normalized tool name and compact result object;
- source context;
- required fields and field specifications;
- immutable, entity, semantic, and localizable field lists;
- accepted variants used by deterministic evaluation;
- a short list of predefined unsupported claims;
- an optional reference answer used for integrity checks.

See `data/schema.md` for the complete record description.

## Known limitations

- The benchmark emphasizes single-record outputs rather than lists, deep nesting, tables, routes, or multi-turn tool chains.
- The current field schema separates evidence roles but does not fully separate structured literals from open descriptive text.
- Only fields explicitly marked as requiring localization receive a hard localization check. Other semantic text is checked primarily for meaning preservation under the operational contract.
- Accepted variants and script heuristics are incomplete and can reject valid language or accept coincidental surface matches.
- Lower-resource settings do not have systematic native-speaker validation across the complete dataset.
- Curated static records may contain construction errors or outdated public values.

## Privacy and safety

The released tasks are associated with public services and exclude private user state. The artifact does not call live services during evaluation. Source URLs provide context; users should not interpret the curated records as current information or verbatim archived responses.
