# Changelog

All notable changes to stapel-attributes are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Pre-1.0 semver: **minor = breaking**, patch = compatible.

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
  `uiStyle='dropdown'` and `maxSelected` = unlimited, not legacy's `chips` / `1`.
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
  for the nine types, ported 1:1 from legacy `feature_types.js`), and
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

Initial release: port of the typed-attribute engine from
`legacy-catalog` (`categories/feature_types` + the `ads` value-validation
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

### Changed (vs legacy-catalog)
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
