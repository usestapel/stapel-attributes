# Changelog

All notable changes to stapel-attributes are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Pre-1.0 semver: **minor = breaking**, patch = compatible.

## [0.6.1] - 2026-08-31

### Fixed

- **The 0.6.0 wheel could not be imported at all.** `[tool.setuptools]
  packages` in `pyproject.toml` is an explicit list, and
  `stapel_attributes.types.group` — the package 0.6.0 exists to add — was not
  on it. So the published wheel shipped a `types/__init__.py` whose line 31
  reads `from stapel_attributes.types.group import GroupFeatureType` and a
  `types/` directory with no `group` in it: every `import stapel_attributes` on
  0.6.0 raised `ModuleNotFoundError`, which is every consumer of the library,
  not only the ones using the new kind. 0.6.1 adds the entry; the built wheel
  now carries the package (verified against the artifact, not the source tree).

- **A gate that would have caught it**, because the one in place could not:
  CI installs `-e .`, which imports from the source tree, where `group/` was
  right there — the tests passed on a layout the wheel did not have.
  `tests/test_packaging.py` compares the packages on disk against the packages
  pyproject declares, in both directions, so a new type (or a removed one)
  fails the build instead of the release.

## [0.6.0] - 2026-08-31

**Minor = breaking** (pre-1.0) only in the registry-shape sense: the built-in
registry grows a thirteenth slug, so anything enumerating the type list (a
facet-mapping table, a value-editor table, a pinned snapshot) must accept it.
Nothing about the existing twelve types changes.

### Added — `group`, the composite kind

One feature holding a small table: a list of rows, each row a set of child
features of the other kinds. The deferred item of the attributes-v2 spec
(§596, "Композитные поля (group-kind)") — and the only shape in the Avito
autoload corpus that no kind could express: **2 468 raw fields carry
`children`** (2 454 `DiscountLadderList`, 14 `CompatibleCars`), which the
importer had to count and drop.

```json
{"type": "group",
 "fields": [{"slug": "quantity", "mandatory": true, "config": {"type": "int", "min": 1}},
            {"slug": "discount", "config": {"type": "int", "min": 1, "max": 30}}],
 "repeat": {"min": 1, "max": 5}}
```

- DTO `{type, value: [{child_slug: value}, …]}`; DAO rows whose cells are the
  children's own DAOs, each carrying its `DaoMeta` (`name`, `order`, `title`,
  `badge`, `translate`) — a stored row renders without the schema.
- Every cell is validated by the child's own type through the ordinary registry
  entry points, so a group inherits each kind's constraints for free and a
  newly registered kind works inside a group the day it is registered. A cell
  failure keeps its machine code and gains a path — `rows[1].discount: Value
  must be <= 30`, `error_params={"row": 1, "child": "discount"}`. **No new
  error code**: the composite adds no error vocabulary of its own.
- A row is its own value namespace, so a `ref_select` child narrowing by
  `optionsRef.parentFeature` reads the parent from the *same row*.
- `repeat: {min, max}` bounds the row count (`BELOW_MINIMUM` / `ABOVE_MAXIMUM`);
  `repeat: null` is a single-row group. `repeat.min` bites on a submitted
  table, never on an empty optional one — an empty group is an absent value and
  requiredness stays the pipeline's business (static `mandatory` or a rule).

Three boundaries are **enforced, not documented conventions** — each is a
refused config, because the alternative in every case is a silent no-op:

- **Nesting depth 1** — a child may not be a `group`.
- **No `header` child** — a header is injected by the pipeline from the schema
  and carries no value; inside a row it would have nothing to inject into.
- **No `rules` on a child.** `evaluate_rules` reads a flat `{slug: value}` map
  of *top-level* features; a row's values are not in that namespace, so a rule
  on a child could never fire and a rule outside could never read a child's
  value. Conditional behaviour for a composite is expressed from outside, as a
  rule on the group feature itself — `require` / `show` / `hide` work on a
  group exactly as on any other kind (pinned by tests).

`get_translation_keys()` aggregates over the children: each child's `name` plus
whatever the child's own type contributes. A child is not a catalog row, so
nothing else would ever walk it.

`docs/feature-def.schema.json` gains `$defs.GroupConfig` / `$defs.GroupRepeat` —
the composite is a cross-language contract (both editors draw the subform), so
it belongs in the §68 canon next to the two ref configs.

No admin config form is declared (`config_form()` returns `[]`): the Django
admin edits `fields` as raw JSON and the schema-driven config editor shows its
unsupported notice. The composer UI is `@stapel/attributes-react`.

Note the word collision, which is deliberate and load-bearing in neither
direction: `FeatureDef.group` (a string) is the *form section*; the `group`
*type* is the composite.

### Tests
- `tests/test_group_type.py` — 48 cases: the three enforced boundaries, repeat
  bounds in both directions, per-row delegation to every other built-in kind
  (parametrized), the row-scoped `ref_select` parent narrowing, DAO shape and
  child `DaoMeta`, `format_value`, translation-key aggregation, and the group
  under `require` / `hide` rules end-to-end through the pipeline.

## [0.5.1] - 2026-08-30

Patch (pre-1.0: minor = breaking, patch = compatible). Test corpus only —
no engine, schema or API change.

### Added
- `tests/golden/rules/avito/` — the Avito autoload rule corpus emitted by
  `stapel-avito-import --emit-rule-cases` (stapel-tools 0.57.1): 3890
  distinct rules (1185 parsed from dependency prose, 2705 derived from
  `values_by_group`), each with a `match` and a `nomatch` value set whose
  `expect` is recorded by the Python evaluator. Effects covered: require 153,
  show 1020, hide 12, forbid_option 2689, limit 16. Two compact array files
  (`prose.json`, `values-by-group.json`) rather than one file per case, so the
  corpus stays at ~12 MB uncompressed; `tests/test_rules_golden.py` runs every
  polarity and asserts the two polarities disagree on the owned feature. The
  TypeScript mirror in @stapel/attributes-react copies these files verbatim
  and runs the same expectations.

## [0.5.0] - 2026-08-30

**Minor = breaking** (pre-1.0). Slice S1 of the attributes-v2 architecture:
conditional rules, form metadata on `FeatureDef`, the vocabulary resolver seam
and the two vocabulary-backed types, plus `docs/feature-def.schema.json` as the
canonical shape of a feature definition.

Nothing changes for a schema that carries no `rules`: the rule pre-pass is
additive, and `tests/test_rules_pipeline.py::TestNoRulesIsUnchanged` pins that
0.4.7 parity mechanically. What *is* breaking: requiredness is now
`RuleState.required`, not `FeatureDef.mandatory`, so anything reading
`mandatory` as the whole answer is now reading half of it; a `ref_*` feature
config no longer validates without a registered resolver; and there is a new
`ValidationErrorCode`, which consumers pinning the enum must accept.

### Added
- `rules.py` — the closed conditional-rule grammar (5 effects, 4 operators, 2
  connectives, no nesting) and its single-pass evaluator. Public:
  `parse_rules(raw) -> list[Rule]`, `stringify(value) -> list[str]`,
  `evaluate_rules(feature_defs, values) -> dict[str, RuleState]`,
  `narrow_config(config_dict, state)`, `rule_warnings(rules, known_slugs)`,
  and the `Cond` / `When` / `Rule` / `RuleState` dataclasses. Django-free at
  import: only the error path of `parse_rules` reaches for
  `FeatureValidationError`.
  - **Rules reach the type plugins through the config, not through the
    types.** `narrow_config` drops forbidden options and replaces a declared
    `min`/`max`; the narrowed config then goes down the ordinary
    `parse_config` -> `validate_dto` path, so a forbidden option surfaces as
    `not_in_options` and a tightened bound as `above_maximum`. No new error
    codes for *values*, and every host-registered type gets rules for free.
  - **One pass, no fixed point**: a controlling feature's own visibility is
    never consulted, so a rule cycle is impossible by construction.
  - **An unknown controlling slug is not an error** — a feature is reused
    across categories with different field sets, where the slug simply reads
    as `empty`. It is a warning (see `validate_configs_structured` below).
- `ValidationErrorCode.INVALID_RULES` + `error.400.feature_invalid_rules`,
  raised when `rules` deviate from the grammar. Mirrored in
  `static_src/src/error-codes.ts` and in `tests/golden/error_codes.json`.
- `FeatureDef` v2 fields: `rules`, `description`, `example`, `default`,
  `hints`, `group`. `DaoMeta` is deliberately **not** extended — form metadata
  never lands in a stored value.
- `base.ValidationContext` and `BaseFeatureType.validate_dto_in_context(config,
  dto, context)`, defaulting to `validate_dto`. The pipeline now calls the
  context form; every existing type notices nothing.
- `vocabularies.py` — the `VocabularyResolver` protocol (`describe` / `exists`
  / `is_child` / `labels`), `VocabularyInfo` / `VocabularyLevel`, and the
  registry (`register_vocabulary_resolver`, `get_vocabulary_resolver`). The
  protocol only: every implementation lives outside this library.
- `STAPEL_ATTRIBUTES["VOCABULARY_RESOLVER"]` — dotted path resolved lazily
  through the settings `import_strings` seam (a class is instantiated once). A
  runtime registration wins over it.
- Two built-in types, bringing the registry to twelve:
  - `ref_select` — `optionsRef {vocabulary, level, parentFeature?}`,
    `minSelected` / `maxSelected` / `uiStyle`. Codes are checked with
    `exists`; a *filled* `parentFeature` narrows the level to that term's
    children (`is_child`, violation -> `not_in_options`), while an empty parent
    allows the whole level so a form need not be filled in order. `dto_to_dao`
    snapshots `labels` (unknown code labels as itself) and the
    vocabulary/level, so display never re-reads the vocabulary;
    `get_translation_keys()` is `[]` because term labels are the vocabulary's.
  - `ref_hierarchical_select` — `vocabulary` + a root-to-leaf `levels` parent
    chain with `minDepth`/`maxDepth`; existence per level plus the `is_child`
    chain, one label per level in the DAO.
  - Both are **loud without a resolver**: `validate_config` raises
    `INVALID_CONFIG` ("no vocabulary resolver registered") when the feature is
    saved, not when the first value is submitted. Parsing a stored config
    never needs a resolver.
- `docs/feature-def.schema.json` — JSON Schema 2020-12 with `$defs` for
  `FeatureDef`, `Rule`, `Cond`, `Hint`, `OptionsRef`, `RefSelectConfig`,
  `RefHierarchicalSelectConfig`; shipped in the wheel. Gated by
  `tests/test_feature_def_schema.py`: the dataclass fields equal the schema
  properties, `required == ["slug", "config"]`, every rule in the corpus
  validates against `$defs.Rule`, and the schema rejects exactly what
  `parse_rules` rejects.
- Golden rule corpus `tests/golden/rules/` — 59 `cases/` (every effect,
  operator and connective; the whole `stringify` table; unknown controlling
  slugs; headers; empty payloads) and 10 `pipeline/` cases (hidden features
  dropped, forbidden options rejected, narrowed bounds enforced), run by
  `tests/test_rules_golden.py` with the same `GOLDEN_RECORD=1` protocol as
  `tests/test_golden.py`. attributes-react runs a generated copy of both, so
  the two evaluators cannot diverge silently.
- Config-form declarations for the two new types. The vocabulary pointer is
  the one nested config key in the library, declared by dotted path
  (`optionsRef.vocabulary`); no new field-kind was needed, so the committed
  admin bundle is untouched. en/ru admin locale entries added.

### Changed
- `validate_dto`, `validate_dto_structured` and `normalize_to_dao` run one
  rule pre-pass and then: take requiredness from `RuleState.required` instead
  of `FeatureDef.mandatory`; **skip a hidden feature entirely** (not
  validated, `OK` in the structured result, silently dropped from the DAO even
  if a value was submitted); and parse the *narrowed* config. `validate_dto`
  raises `INVALID_RULES` on a broken grammar, `validate_dto_structured`
  reports it on `_root` — the schema, not the payload, is what is broken.
- `validate_configs_structured(configs, known_slugs=None)` — new optional
  argument. It now also parses `rules` (failing the feature with
  `INVALID_RULES`) and, when `known_slugs` is given, warns about rule
  conditions and `optionsRef.parentFeature` naming slugs that set does not
  contain. Warnings stay non-blocking, as before.
- `Makefile`: `--budget 5200` for `llms.txt` (43 surface entries now). The
  standing call is to raise the ceiling, never to trim intent lines to fit.

## [0.4.7] - 2026-08-22

Patch (pre-1.0: minor = breaking, patch = compatible). Bug fix, no schema
change to the individual config/DTO/DAO components — only to the OpenAPI
`discriminator.mapping` describing them.

Filed by @stapel/categories-react (the storefront spec §13.7
note 5): the `FeatureConfig`/`FeatureDto`/`FeatureDao` polymorphic OpenAPI
schemas emitted a `discriminator.mapping` with a single bogus `"null"` entry
instead of the ten type-slug entries. openapi-typescript consequently
stripped `type` from generated call-sites and re-added a synthetic,
*wrong* one (e.g. `IntConfig` declaring `type: "IntConfig"` where the wire
actually sends `"int"`), mangling every generated feature-config type.

### Fixed
- `serializers.py`'s `_get_proxy_serializer` now builds the
  `PolymorphicProxySerializer` from an explicit `{slug: serializer_class}`
  mapping instead of a bare list of serializer classes. drf-spectacular's
  `PolymorphicProxySerializerExtension` has two modes: given a list, it
  *infers* each `resource_type` by instantiating the sub-serializer and
  calling `to_representation(None)` on its `type` field; given a dict, it
  uses the keys verbatim. Our `type` field is a plain
  `djangorestframework-dataclasses`-built `ChoiceField` (from
  `Literal['int']` etc.), and DRF's `ChoiceField.to_representation`
  short-circuits `None`/`''` input straight back to `None` — it never
  consults the field's constant/default value. Every sub-serializer's
  inferred `resource_type` was therefore the Python object `None`, and the
  dict comprehension building `discriminator.mapping` collapsed all ten
  entries into one `{None: <last schema>}`, serialized to JSON as the single
  `"null"` key. Passing the mapping explicitly (we already had it —
  `_build_mapping()` was already used for the runtime polymorphic
  serializer) sidesteps the inference path entirely.
- Added `tests/test_openapi_discriminator.py`: a contract test asserting the
  `FeatureConfig`/`FeatureDto`/`FeatureDao` discriminator mappings are
  slug-keyed, contain all ten registered type slugs, and never contain
  `"null"`.

## [0.4.6] - 2026-08-21

Additive-only. Patch (pre-1.0: minor = breaking, patch = compatible).

Upstream contribution from the stapel-forms build (tasks/stapel-forms-design.md
§3.1/§11b): the `string` type had no way to declare a textarea vs. a
single-line input.

### Added
- `StringConfig.multiline` (default `False`) — a rendering-only hint (textarea
  vs. single-line input); no validation semantics change (`minLength` /
  `maxLength` / `pattern` behave identically either way). Declared in
  `config_form._string_form()` as a `checkbox` field (default `False`,
  matching the engine's normalized default) and exposed in the admin
  en/ru locale catalogs (`admin.attributes.form.string.multiline`).
- `FeatureValidationResult.warnings` (optional, default `None`) — a
  non-blocking, informational findings list. `validate_configs_structured`
  now populates it when a raw config dict carries a key its type's config
  dataclass doesn't recognize (e.g. a typo'd `minLenght`): previously such a
  key was silently dropped by the DRF-based parser with no signal to the
  caller. A warning never flips `status`/`valid` — the config is still
  accepted; this only flags that part of the input was ignored. See
  MODULE.md "Unknown config keys — silently dropped, warned (not rejected)"
  for the full contract and why a hard-reject (unknown-fields-strict
  serializer) was judged out of scope as a redesign of the shared parse seam.

## [0.4.5] - 2026-08-02

Packaging / contract only. Patch.

### Added
- `docs/llms.txt` — the fifth contract artifact — is now emitted, drift-gated
  by `make contract`/`contract-check`, and badged in the README.
  `docs/capabilities.json` remains hand-written (stapel-catalog sweep); these
  targets manage only `docs/llms.txt` and never touch `capabilities.json`.
  No `surface` entries exist yet, so the generated llms.txt's Usage surface
  section is empty (pre-existing gap, not introduced here).

### Fixed
- `docs/capabilities.json`'s hand-maintained `version` field had drifted to
  `0.4.3` (missed the 0.4.4 bump); corrected to match `pyproject.toml`. Content
  (provides/axes/extension_points/surface) unchanged.
- CI now tests Python 3.14 (the version actually deployed), badge canon
  applied, and `docs/llms.txt`/`docs/capabilities.json`/`docs/flows.json`/
  `docs/errors.json`/`CONFIG.MD` are now listed in `package-data` so they ship
  in the wheel.

## [0.4.3] - 2026-07-17

Additive-only. Patch (pre-1.0: minor = breaking, patch = compatible).

### Added
- `profile_bridge.py` (§66, docs/pending/profile-fields.md §4): a small
  `PROFILE_KIND_TO_FIELD_KIND` lookup table + `field_kind_for()` helper
  mapping a `stapel_profiles.field_defs.ProfileFieldKind` value (`text`,
  `bool`, `enum`, `model_ref`, `geohash`) to the matching
  `stapel_attributes.config_form.FIELD_KINDS` key — so a shop/classified
  projection building a filterable attribute FROM a profile field (e.g. an
  `occupation` custom field) doesn't re-derive the admin-config-form shape
  by hand. No dependency on `stapel-profiles` added — this module is a pure
  string-keyed dict, `stapel_profiles.field_defs.ProfileFieldDef.attribute_kind`
  is the (optional, try/except ImportError) caller.

## [0.4.2] - 2026-07-17

Ships `convertible_unit` as a built-in type (was documented in MODULE.md as
"deliberately not shipped" alongside `size_grid`; `size_grid` stays a
vertical-only registration, `convertible_unit` is generic enough to graduate).
Additive — a new registered slug, no changes to existing types' behavior.
Patch (pre-1.0: minor = breaking, patch = compatible; this is purely additive).

### Added
- `types/convertible_unit/` — a numeric value with a user-facing unit,
  converted to/from a canonical base unit. Ships five unit-family presets
  (`constants.UNIT_FAMILIES`): `length` (base `m`), `weight` (base `kg`),
  `area` (base `m2`), `volume` (base `l`), `temperature` (base `c`, affine).
  Config picks a family (`unitType`) and offers a metric and/or imperial unit
  of it (`unit_m`/`unit_i`); `min`/`max` and the DAO's stored `value` are
  always in the base unit, so range-filter queries need only convert their
  bounds to the base unit once (`constants.convert_to_base` /
  `ConvertibleUnitFeatureType.to_base`) and then run a plain numeric range
  comparison — no type-specific filter support needed elsewhere.
- Ported from the legacy marketplace catalog's
  `categories/feature_types/types/convertible_unit`, with two defects fixed
  in transit (see `types/convertible_unit/type.py` docstring for detail):
  the legacy `normalize_dto` accepted `{value: {value, unit}}` but discarded
  `unit`, silently storing non-base-unit submissions as if they were already
  in the base unit; the legacy `format_value` ignored `unit_m`/`unit_i` and
  printed the base value under the family name instead of a real unit.

## [0.4.1] - 2026-07-17

Fleet follow-up to stapel-core 0.12.0 (legacy shim sweep). No source
changes needed. Full suite green against core 0.12.0.

### Changed
- `stapel-core` dependency ceiling `<0.12` → `<0.13`.

## [0.4.0] - 2026-07-17

Legacy-compat scrub. Minor bump (pre-1.0: minor = breaking) — a plugin-facing
compat behavior is removed.

### Removed
- `base._dataclass_to_dict_no_none` — backwards-compatible underscored alias
  for `dataclass_to_dict_no_none` (the legacy framework's exported name).
  Unused; the public name is unchanged.
- `validation._error_info` and its degradation path: a bare Django
  `ValidationError` raised by a type plugin was degraded to `INVALID_FORMAT`
  in `validate_dto_structured` / `validate_configs_structured`. Feature types
  MUST raise `FeatureValidationError` (machine code + ref_value); a bare
  `ValidationError` now propagates instead of being masked. **Breaking** for
  third-party types that never adopted the structured exception.
- `tests/sample_types.LegacyFeatureType` (+ its Config/Dto/Dao/serializers)
  and `test_plain_validation_error_degrades_to_invalid_format` — existed only
  to exercise the removed degradation path.

## [0.3.4] - 2026-07-17

### Changed
- `stapel-core` ceiling raised `>=0.10,<0.11` → `>=0.10,<0.12` (core 0.11
  fleet re-pin: default bus, nav, config-checks, error params/language —
  additive for modules). Suite green as-is.

## [0.3.2] - 2026-07-08

### Changed
- Reworded internal provenance comments/docstrings for consistency. No
  behavior change.

## [0.3.1] - 2026-07-06

### Changed
- Pinned `stapel-core` to the `>=0.8,<0.9` window (library-standard §7.1: one
  minor window; floor `0.8.0` is published on PyPI — no pin into the void).
- CI: added the release-track job (library-standard §7.4) — installs the package
  the way an end user does (`pip install .`, dependencies resolved from PyPI
  strictly by the declared pins, no git-main core, no editable siblings), asserts
  `stapel-core` resolves inside the `0.8` window, and runs an import smoke.
  Advisory (continue-on-error) until the whole stapel graph is on PyPI; becomes
  the blocking precondition for a `vX.Y.Z` tag once it is.


## [0.3.0] - 2026-07-06

Dual-build packaging for the admin UI + a contract-level error-code addition.
Minor bump: additive `ValidationErrorCode` members (new machine codes).

### Added — npm packaging (`@stapel/attributes-admin`)
- **Dual build from one source** (`static_src/build.mjs`):
  1. **django** — the committed admin bundle under `static/stapel_attributes/`
     (Lit inlined). Unchanged and **byte-stable**: same hash, drift gate green.
  2. **lib** — an externalized-Lit ESM package for npm consumers
     (`@stapel/attributes-react`). Lit is a **peerDependency** (`^3`), types
     (`.d.ts`) are emitted, `sideEffects: false`. Output to `dist/` (gitignored,
     not published here — publishing is the user's decision).
- **Side-effect split without forking sources.** Each editor/component module
  keeps its self-registration tail (django bundle relies on it), fenced by
  `// @stapel-auto-define:start … :end`. The lib build strips those fences
  (`strip-auto-define.mjs`), so importing the lib registers **nothing** until the
  host calls the new `defineElements()`. Preserves byte-stability of the django
  bundle (no source refactor perturbs esbuild's minifier) while giving the lib an
  honest `sideEffects: false`.
- New pure entry `src/lib.ts`: `defineElements()`, `mountConfigEditor`,
  `createValueEditor`, the element/registry/i18n exports, and the error-code
  mirror — no `window` global, no implicit `customElements.define`.
- The django build passes `ignoreAnnotations: true` so `sideEffects: false` (for
  the npm lib) cannot tree-shake the admin bundle's registrations.
- vitest covers **both builds**: the lib artifact is side-effect-free on import
  and `defineElements()` registers the full set; the django entry self-registers
  and installs `window.StapelAttributes`.

### Added — validation vocabulary (follow-up: fix-catalog-feature-editor)
- `ValidationErrorCode.NOT_ALLOWED` (`not_allowed`) — a referenced feature slug
  is not permitted for its owner (e.g. a listing submits a feature its category
  disallows). Canonical replacement for the temporary
  `error.400.listing_feature_not_allowed` key in stapel-listings; reused by
  listings/categories. Localizable key: `error.400.feature_not_allowed`.
- `ValidationErrorCode.UNKNOWN_FEATURE` (`unknown_feature`) — a referenced slug
  is unknown/undefined (distinct from `UNKNOWN_FEATURE_TYPE`, an unregistered
  config `type`). Localizable key: `error.400.feature_unknown`.
- TS mirror `static_src/src/error-codes.ts` (`ValidationErrorCode`,
  `VALIDATION_ERROR_CODES`) exported from the lib. A golden snapshot
  (`tests/golden/error_codes.json`, generated from the Python enum) is asserted
  by **both** the Python runner and the TS mirror test — the py↔ts sync gate.

## [0.2.0] - 2026-07-05

Code-review fixes for the schema-driven admin UI (config-form declaration ↔ JS
editor ↔ Python engine round-trip). Minor bump: two contract-level default
changes (B2, B5b).

### Changed — contract (migration notes)
- **B2 — select form defaults** now match the **engine** dataclass
  (`SelectConfig`): the untouched admin form emits/round-trips to
  `uiStyle='dropdown'` and `maxSelected` = unlimited, not the legacy `chips` / `1`.
  *Migration:* a select saved through the admin UI without touching these fields
  now stores `dropdown` / unlimited (previously the UI showed chips/1 but the
  engine stored dropdown/unlimited — the two are now consistent). No stored
  config that already carries explicit `uiStyle`/`maxSelected` is affected. To
  keep a single-select chips control, set both explicitly in the form.
- **B5b — string `pattern` semantics**: validation now requires the pattern to
  match the **entire** value (`re.fullmatch`, both ends anchored) instead of a
  prefix (`re.match`); the admin JS mirrors it with `^(?:<pattern>)$`.
  *Migration:* patterns that previously passed on a prefix match (e.g. `[0-9]+`
  accepting `12ab`) now reject. Anchor or broaden such patterns. `pattern` is a
  JS-RegExp-compatible subset; engine-only regex features are out of contract.

### Fixed
- **B1** — the config-widget registry is live: `<stapel-config-editor>` resolves
  each field-kind through `resolveConfigWidget` before its built-in switch, so a
  host `registerConfigWidget(kind, …)` override (or an exotic kind) renders.
  Built-in kinds are seeded at import (`registeredConfigWidgetKinds()` is no
  longer empty) via a `BUILTIN_CONFIG_WIDGET` sentinel.
- **B3** — a runtime `register_feature_type()` override of a built-in slug (e.g.
  from `AppConfig.ready()` before first registry access) is no longer clobbered
  by the lazy built-in load; `register_feature_type` ensures built-ins/extras are
  loaded first (later wins), guarded against re-entrancy.
- **B4** — a mandatory feature submitted with an empty value (`null` / `''` /
  `[]`) is now rejected as `MANDATORY_MISSING` on both API pipelines
  (`validate_dto`, `validate_dto_structured`) instead of normalizing to a
  valid-but-empty value that silently vanished from the DAO.
- **B5a** — string length counts Unicode **code points** on both sides (Python
  `len()`; JS `[...s].length`), so emoji-bearing values agree.
- **B6** — an invalid config now raises a **localizable envelope**: field errors
  are flattened into `FeatureValidationError.error_params['config_errors']`
  (`{dotted.path: message}`) instead of a raw DRF `ErrorDetail` repr in the
  message.
- **B7** — the header config form no longer declares a dead, required `label`
  field; header text is authored via the feature's `name`.
- **maxSelected** unlimited now emits a real `null` (was `NaN`, "working" only
  because JSON coerces it — latent LN-B07).

### Added
- **Cross-language golden bridge** (`tests/golden/`): one JSON corpus (13
  starter cases) run by both a pytest runner (`tests/test_golden.py`) and a
  vitest runner (`static_src/src/golden.test.ts`), with a byte-stable
  `GOLDEN_RECORD=1` record mode, a committed `declarations.json` snapshot with a
  drift gate, and a JS↔Python cross-agreement assertion (documented divergences
  are explicit per case). Closes the B2/B4/B5/B6 class against future drift.

## [0.1.2] - 2026-07-05

### Added — schema-driven admin UI (Lit 3)
- **Field-kind contract** (`config_form.py`): `FIELD_KINDS` (13 kinds),
  `FormField`, `config_form()` hook on `BaseFeatureType` (built-in declarations
  for the nine types, ported 1:1 from the legacy catalog's `feature_types.js`), and
  `form_declarations()` — a JSON snapshot of all registered types.
- **`static_src/`** — Lit 3 + TypeScript source (esbuild/vitest toolchain);
  committed bundle `static/stapel_attributes/attributes-admin.js` (~15 KB gzip)
  + `admin-tokens.css` (light + dark) + `locales/en.json`+`ru.json`.
- **`<stapel-config-editor>`** (renders all 13 field-kinds) and value-editors for
  the nine types, with two open merge registries
  (`window.StapelAttributes.registerConfigWidget`/`registerValueEditor`) and an
  `UnsupportedEditor` fallback. Mini-i18n (en+ru, merge without fork), `--stapel-*`
  theming, CSRF + StapelError-envelope runtime, `<stapel-dialog>`, Test dialog.
- **`ConfigEditorWidget`** (`widgets.py`) — Django admin widget with a
  progressive-enhancement textarea + `json_script` mount; settings
  `ADMIN_LOCALES`, `ADMIN_WIDGETS`, `ADMIN_EXTRA_CSS`, `ADMIN_EXTRA_JS`.
- Extraction inventory `static_src/LOGIC-NOTES.md` (1:1 port source of truth).
- CI: node job (vitest + typecheck) with a drift gate (rebuild must not change
  `static/`).

## [0.1.0] - 2026-07-04

Initial release: port of the typed-attribute engine from a legacy
catalog app (`categories/feature_types` + the `ads` value-validation
pipeline: `validators.py`, `feature_validator.py`, `validation_result.py`),
restructured as an L1 Stapel library.

### Added
- `BaseFeatureType[TConfig, TDto, TDao]` with Config/DTO/DAO layering,
  `DictDataclassSerializer`, `DaoMeta` (`base.py`).
- Nine generic built-in types: `int`, `float`, `string`, `bool`, `hex_color`,
  `select`, `date`, `header`, `hierarchical_select` (`types/`).
- Open type registry with house merge semantics: built-ins +
  `STAPEL_ATTRIBUTES["EXTRA_TYPES"]` (dotted paths, lazily imported, additive)
  + runtime `register_feature_type()`; `registered_types()` introspection
  (`registry.py`).
- Polymorphic serializer factories (drf-polymorphic) and OpenAPI proxy
  serializers (drf-spectacular), now cache-keyed on the registry version so
  late registrations are always reflected (`serializers.py`).
- Structured validation vocabulary: `ValidationStatus`, `ValidationErrorCode`,
  `FeatureValidationResult`, `ValidationBatchResult` (`results.py`) and
  `FeatureValidationError` carrying machine codes end-to-end (`exceptions.py`).
- Model-decoupled validation pipeline over `FeatureDef` structures:
  `validate_dto`, `normalize_to_dao`, `validate_dto_structured`,
  `validate_configs_structured`, `validate_dao_structured`,
  `validate_description` (`validation.py`).
- Localizable `error.400.feature_*` keys registered with stapel-core
  (`errors.py`).
- `get_builtin_translation_keys()` hook on `BaseFeatureType`;
  `collect_all_builtin_translation_keys()` now iterates the registry instead
  of hardcoding type constants.

### Changed (vs the legacy catalog)
- The engine operates on `FeatureDef` config structures, not on
  `categories.models.Feature` / `Category` — the future stapel-categories
  module owns the models and calls this library.
- `SelectConfig.maxSelected` default fixed to `None` (unlimited), matching the
  documented semantics and the source test suite (the dataclass default `1`
  contradicted both).

### Fixed (source defects, not carried over)
- `feature_validator._extract_error_info` regex-parsed ValidationError
  message strings to recover error codes — replaced with structured
  exceptions (`FeatureValidationError`) carrying `ValidationErrorCode`,
  `ref_value` and params end-to-end.
- `_get_feature_slug` / `_build_feature_lookup` were duplicated across three
  source files — single `get_feature_slug` / `build_feature_lookup` here.
- Stale polymorphic-serializer caches: factories cached forever, so types
  registered after first use were missing from the mappings — caches are now
  keyed on the registry version.

### Excluded (marketplace-specific, app-layer registrations)
- `size_grid` and `convertible_unit` types — registered by vertical packages
  through the open registry; `size_grid` is the worked example in MODULE.md.
- Phantom types referenced only in source docstrings/admin (`file_list`,
  `checklist`, `price_range`) — no dead references ported.
