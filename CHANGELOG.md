# Changelog

All notable changes to stapel-attributes are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Pre-1.0 semver: **minor = breaking**, patch = compatible.

## [Unreleased]

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
