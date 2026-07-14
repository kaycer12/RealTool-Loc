# RealTool-Loc Dataset Schema

Each sample represents a curated static API-style record associated with a public tool or service. The task assumes that this record is the result available to a tool-using agent. The model must not call the tool again and must faithfully communicate the supplied record in the user's language.

## Task Definition

### Input

- `user_query`: The user's request in the target language.
- `tool_name`: A normalized wrapper name for the public API or tool.
- `tool_source`: Source context, including the provider, documentation URL, representative request URL, and legacy dataset-construction date in `retrieved_at`. This date is not a verified per-record fetch timestamp.
- `tool_result`: A compact curated JSON-like record used as the fixed tool result.
- `field_specs`: Field-level evaluation specifications.
- `required_fields`: Fields that the final answer must express.
- `immutable_fields`: Identifiers or codes that must be copied verbatim.
- `entity_fields`: Names or titles whose identity must be preserved; common localized aliases are allowed.
- `semantic_fields`: Dates, quantities, Boolean values, measurements, statuses, and other fields whose meaning must be preserved.
- `forbidden_hallucinations`: Predefined unsupported claims used by the deterministic evaluator.

### Output

- A final user-facing answer in `expected_answer_language`.

The model must not call the tool again, query a live API, or introduce facts that are absent from `tool_result`.

## Field Roles

- `immutable`: Requires exact string preservation. Examples include DOIs, ISBNs, barcodes, API country codes, and Open Library keys.
- `entity`: Requires preservation of entity identity while allowing natural localization. Examples include city names, book titles, publishers, and product names.
- `semantic`: Requires preservation of the value's meaning while allowing formatting changes. Examples include dates, temperatures, counts, and page numbers.
- `status`: A semantic label that may require localization. The raw English or API label may help establish value coverage, but copying it without an explanation in a non-English answer is treated as insufficient localization.

This role system does not require every entity to remain in English, and it does not penalize valid localization of names such as cities.

## Evaluation Policies

The deterministic evaluator supports two policies:

- `strict`: The original default policy. Every `immutable` field must appear as the original string. This policy measures complete record verbalization and exact field preservation.
- `relaxed`: Allows natural-language equivalents for a limited set of metadata codes. For example, `CN` may be expressed as “China,” `usd` as “US dollars,” and `en` as “English.” True identifiers, including DOIs, ISBNs, URLs, version strings, package names, and error codes, must still be copied exactly.

Reports should distinguish these targets explicitly: `strict` measures field-level exactness under the complete-record contract, whereas `relaxed` better accommodates semantic equivalence in natural user-facing answers.

## Tools and APIs

Version 3 contains records from 32 public tools and APIs:

- Open-Meteo Historical Weather API
- Open-Meteo Air Quality API
- USGS Earthquake Catalog API
- Nager.Date Holiday API
- World Bank Country API
- World Bank Indicators API
- Crossref REST API
- Open Library Books API
- Gutendex API
- Open Food Facts Product API
- GitHub REST API
- PyPI JSON API
- npm Registry API
- crates.io API
- Wikidata EntityData API
- Wikipedia REST API
- OpenStreetMap Nominatim API
- Zippopotam.us Postal Code API
- GBIF Species API
- MusicBrainz API
- Frankfurter Exchange Rates API
- CoinGecko Simple Price API
- WorldTimeAPI
- Sunrise-Sunset API
- Open Notify ISS Location API
- Hipolabs Universities API
- Hacker News Firebase API
- Stack Exchange API
- arXiv API
- ClinicalTrials.gov API
- openFDA Drug Label API
- GBFS Station Status API

The benchmark stores curated static records. Experiments do not depend on the current state or availability of any live API. The release does not contain a per-record raw-response archive.

## Languages

Version 3 includes the following language settings:

- `zh`: Chinese
- `ja`: Japanese
- `th`: Thai
- `id`: Indonesian
- `bo`: Tibetan
- `ug`: Uyghur
- `mn-Mong`: Traditional Mongolian script
- `kk-Arab`: Arabic-script Kazakh

Tibetan, Uyghur, traditional Mongolian, and Arabic-script Kazakh help expose lower-resource-language and script-control failures. The language set is diagnostic rather than exhaustive, and the lower-resource settings would benefit from further review by native speakers or authoritative language resources.

## Reported Metrics

The deterministic evaluator reports:

- `language_accuracy`
- `field_coverage`
- `immutable_preservation`
- `entity_fidelity`
- `semantic_fidelity`
- `localization_quality`
- `hallucination_free`
- `faithful_localization_score`
- `core_pass`

Reports should include the component metrics rather than only an average score. `core_pass` is the strict conjunction of all required checks, while `faithful_localization_score` is more suitable for diagnostic analysis.
