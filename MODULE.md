# stapel-attributes — MODULE.md

> Agent-facing map of this package: what it provides, where to extend it
> without forking, and what not to do. Kept in the same PR as any change
> to a seam. See also README.md and CHANGELOG.md.

**Kind: L1 library** — importable by any module (stapel-categories,
stapel-listings, ...); it has **no** models, migrations, views, urls, comm
surface or service identity of its own. Provenance: port of the legacy
catalog's `categories/feature_types` engine + the `ads` value-validation pipeline
(defects fixed in transit — see CHANGELOG 0.1.0).

## What this library provides

| Area | Contents |
|---|---|
| Engine core (`base.py`) | `BaseFeatureType[TConfig, TDto, TDao]` — the type-plugin ABC; `DictDataclassSerializer` (dataclass serializer returning dicts, drf-polymorphic-compatible); `DaoMeta` (shared DAO metadata: name/order/title/badge/translate); `FeatureDef` — the plain feature-definition structure the engine operates on (slug, config, id, name, mandatory, display flags, `rules`, and the form metadata `description`/`example`/`default`/`hints`/`group`); `ValidationContext` — the sibling-values envelope for `validate_dto_in_context` |
| Type registry (`registry.py`) | Open registry (`register_feature_type`, `registered_types`, `get_feature_type`, `get_all_type_slugs`); parse/convert helpers (`parse_config`, `parse_dto`, `dao_to_dict`, `dto_to_dao`, `normalize_feature_dto`, `validate_feature_config`, `validate_feature_dto`, `format_feature_value`, `get_default_value`); translation-key helpers |
| Built-in types (`types/`) | `int`, `float`, `string`, `bool`, `hex_color`, `select`, `date`, `header`, `hierarchical_select`, `convertible_unit`, `ref_select`, `ref_hierarchical_select`, `group` — each a plugin directory of `config.py` / `dto.py` / `dao.py` / `type.py` |
| Polymorphic serializers (`serializers.py`) | Factories for `FeatureConfig`/`FeatureDto`/`FeatureDao` polymorphic serializers (drf-polymorphic, `type` discriminator) + `PolymorphicProxySerializer`s for OpenAPI (drf-spectacular); caches keyed on the registry version, so late registrations are always reflected |
| Validation pipeline (`validation.py`) | `validate_dto(configs, dto)` (raise-style), `normalize_to_dao(configs, dto)` (DTO→DAO with header injection and ordering), `validate_dto_structured` / `validate_configs_structured` / `validate_dao_structured` (batch results), `validate_description`; `coerce_feature_defs` accepts FeatureDef lists, dicts, or `{slug: config}` mappings |
| Conditional rules (`rules.py`) | The closed rule grammar (`parse_rules`, `Rule`/`Cond`/`When`), value canonicalization (`stringify`), the single-pass evaluator (`evaluate_rules` -> `RuleState`), the type-agnostic `narrow_config`, and `rule_warnings`. Django-free at import; mirrored in TypeScript against one shared corpus |
| Vocabulary seam (`vocabularies.py`) | `VocabularyResolver` protocol + `VocabularyInfo`/`VocabularyLevel` and the registry (`register_vocabulary_resolver`, `get_vocabulary_resolver`). The protocol only — every implementation lives outside this library |
| Canonical schema (`docs/feature-def.schema.json`) | JSON Schema 2020-12 for `FeatureDef` (+ `$defs.Rule`/`Cond`/`Hint`/`OptionsRef`/the two ref configs) — one source, several emitters; gated against the dataclass by `tests/test_feature_def_schema.py` |
| Structured errors (`results.py`, `exceptions.py`, `errors.py`) | `ValidationErrorCode` vocabulary, `FeatureValidationResult`/`ValidationBatchResult` (+ serializers), `FeatureValidationError` (a Django `ValidationError` carrying `error_code`/`ref_value`/`error_params`), localizable `error.400.feature_*` keys registered with stapel-core |

Public API: `stapel_attributes.__all__` (PEP 562 lazy — `import
stapel_attributes` is Django-free).

## Type-plugin anatomy (config / dto / dao / type)

Every feature type is four small pieces:

1. **Config** (`config.py`) — a dataclass describing the *schema* of the
   attribute (`type: Literal['<slug>']` discriminator + constraints/UI hints)
   and its `DictDataclassSerializer`.
2. **DTO** (`dto.py`) — what the client submits (`{type, value}`).
3. **DAO** (`dao.py`) — what gets stored: value + display metadata; inherits
   `DaoMeta` (name/order/title/badge/translate). A type whose value is a *code*
   (`select`, `ref_select`, `ref_hierarchical_select`) also stores a `labels`
   snapshot beside `value`, resolved at write time and positionally aligned
   with it: the projection is the whole contract with a reader, and a card
   drawing a badge must not have to fetch the category or the vocabulary to
   find the copy. `value` stays the filter/search axis.
4. **Handler** (`type.py`) — a `BaseFeatureType[TConfig, TDto, TDao]` subclass
   wiring the three together and implementing:
   - `validate_config(config)` — schema validity (raise `FeatureValidationError` with a `ValidationErrorCode`),
   - `validate_dto(config, dto)` — value validity against the config,
   - `dto_to_dao(config, dto, feature: FeatureDef)` — enrich the value with metadata,
   - optionally `normalize_dto`, `format_value`, `get_default_value`,
     `get_default_config`, `is_user_editable`, `get_translation_keys`,
     `get_builtin_translation_keys`.

The engine never touches Django models: model owners (stapel-categories)
materialize their rows into `FeatureDef`s and call the pipeline.

## Extension points (fork-free)

### Settings — `STAPEL_ATTRIBUTES` namespace (`conf.py`)

Resolution order per key: `settings.STAPEL_ATTRIBUTES[key]` -> flat Django
setting of the same name -> environment variable -> default. Read lazily at
call time; caches invalidate on `setting_changed`.

| Key | Default | Semantics | What it customizes |
|---|---|---|---|
| `EXTRA_TYPES` | `[]` | **MERGE** (additive over built-ins) | List of dotted paths loaded lazily on first registry access. Each entry is either a `BaseFeatureType` subclass (registered directly) or a module whose import registers types via `@register_feature_type`. A broken entry raises `ImportError` with the offending path. Loading is additive and idempotent — entries cannot remove built-ins. |
| `VOCABULARY_RESOLVER` | `None` | **REPLACE** (a runtime registration wins) | Dotted path to the `VocabularyResolver` the ref-types validate term codes against; a class is instantiated on first use. See "Vocabulary resolver seam" below. |

### The type registry — open registry with MERGE semantics (flagship seam)

Three layers, later wins per slug:

1. built-ins (`stapel_attributes.types` — the thirteen generic types);
2. `STAPEL_ATTRIBUTES["EXTRA_TYPES"]` — merged over the built-ins;
3. runtime `register_feature_type(cls)` — e.g. from a host app's
   `AppConfig.ready()`; re-registering a slug overrides it.

`registered_types()` returns the effective `slug -> instance` mapping.
The polymorphic serializer factories and the validation pipeline all resolve
against this effective registry, so a registered custom type participates in
validation, DAO normalization and OpenAPI schemas with zero further wiring.

#### Worked example: registering a marketplace `size_grid` type

The legacy `size_grid` (clothing/shoe size tables) is deliberately **not**
shipped — it is a marketplace vertical type (the CPU/size-table use case is
covered generically by the shipped `hierarchical_select`). This is how a
vertical package adds a type like it:

```python
# fashion_vertical/attribute_types/size_grid/type.py
from dataclasses import dataclass
from typing import Literal, Optional

from stapel_attributes import (
    BaseFeatureType, DaoMeta, DictDataclassSerializer,
    FeatureDef, FeatureValidationError, ValidationErrorCode,
    register_feature_type,
)

SIZE_TABLES = {"clothing_women": [...], "shoes_men": [...]}  # vertical data

@dataclass
class SizeGridConfig:
    type: Literal["size_grid"] = "size_grid"
    table: Optional[str] = None

class SizeGridConfigSerializer(DictDataclassSerializer):
    class Meta:
        dataclass = SizeGridConfig

@dataclass
class SizeGridDto:
    type: Literal["size_grid"] = "size_grid"
    system: Optional[str] = None      # 'EU' | 'US' | ...
    rowIndex: Optional[int] = None
    customSize: Optional[str] = None

class SizeGridDtoSerializer(DictDataclassSerializer):
    class Meta:
        dataclass = SizeGridDto

@dataclass
class SizeGridDao(DaoMeta):
    type: Literal["size_grid"] = "size_grid"
    system: Optional[str] = None
    rowIndex: Optional[int] = None
    customSize: Optional[str] = None

class SizeGridDaoSerializer(DictDataclassSerializer):
    class Meta:
        dataclass = SizeGridDao

@register_feature_type            # decorator = registers on import
class SizeGridFeatureType(BaseFeatureType[SizeGridConfig, SizeGridDto, SizeGridDao]):
    slug = "size_grid"
    name = "Size Grid"
    config_class = SizeGridConfig
    dto_class = SizeGridDto
    dao_class = SizeGridDao
    config_serializer_class = SizeGridConfigSerializer
    dto_serializer_class = SizeGridDtoSerializer
    dao_serializer_class = SizeGridDaoSerializer

    def validate_config(self, config):
        if config.table not in SIZE_TABLES:
            raise FeatureValidationError(
                f"Unknown size table: {config.table}",
                code=ValidationErrorCode.INVALID_CONFIG,
                ref_value=sorted(SIZE_TABLES),
            )

    def validate_dto(self, config, dto):
        if dto.rowIndex is None and not dto.customSize:
            raise FeatureValidationError(
                "Either rowIndex or customSize is required",
                code=ValidationErrorCode.INVALID_FORMAT,
            )
        # ... table/system/rowIndex checks against SIZE_TABLES ...

    def dto_to_dao(self, config, dto, feature: FeatureDef):
        return SizeGridDao(
            type=self.slug, system=dto.system, rowIndex=dto.rowIndex,
            customSize=dto.customSize, name=feature.name,
        )
```

Then either (settings flavor):

```python
STAPEL_ATTRIBUTES = {
    "EXTRA_TYPES": ["fashion_vertical.attribute_types.size_grid.type"],
}
```

or (runtime flavor, from the vertical's `AppConfig.ready()`):

```python
from stapel_attributes import register_feature_type
from .attribute_types.size_grid.type import SizeGridFeatureType
register_feature_type(SizeGridFeatureType)
```

Custom types should raise `FeatureValidationError` with a code from
`ValidationErrorCode`; a plain `ValidationError` still works but degrades to
`invalid_format` in structured results.

### `convertible_unit` — values with convertible units

Unlike `size_grid`, `convertible_unit` (values with a user-facing unit —
lengths, weights, areas, volumes, temperatures) is generic enough to ship as
a built-in (`types/convertible_unit/`) rather than stay a vertical
registration; it used to be paired with `size_grid` in the "not shipped"
note above.

- **Unit families are presets, not user config**: `types/convertible_unit/constants.UNIT_FAMILIES`
  ships `length`, `weight`, `area`, `volume`, `temperature`, each shaped
  `{'base_unit': <code>, 'units': {<code>: <factor-to-base>, ...}}`. A
  feature's config picks one family (`unitType`) and which metric/imperial
  unit of it to offer (`unit_m`/`unit_i`, at least one required) —
  ported from the legacy marketplace catalog's `UNIT_DEFINITIONS`/`UNIT_SYSTEMS`.
- **Storage is always in the base unit**: the DAO's `value` is always the
  family's canonical base unit (`m`, `kg`, `m2`, `l`, or `c` for
  temperature — an affine, not multiplicative, conversion). The DTO wire
  shape is `{type, value, unit}` — the number as entered plus which offered
  unit it's in; `normalize_dto` converts it to the base unit (via
  `constants.convert_to_base`) before validation ever sees it. Omitting
  `unit` means "already in the base unit" (the same contract int/float use
  for their plain `value` — a headless caller writing canonical values
  directly).
- **`min`/`max` and range filtering are both in the base unit**: config
  `min`/`max` bound the base-unit value directly, so `validate_dto` never
  needs to know which display unit the submission used. The same base-unit
  canon is why range-filter search (e.g. "listings between 1m and 2m") needs
  no per-type engine support here — a consumer (stapel-listings) converts its
  query bounds to the base unit once (`constants.convert_to_base` /
  `ConvertibleUnitFeatureType.to_base`) and then runs a plain numeric
  `BETWEEN` against the stored `value`, exactly like an `int`/`float` range
  filter already would.
- **Display** (`format_value`) converts the stored base value back to
  `unit_m` (or `unit_i` if unset) and appends the unit code — the legacy
  type's `format_value` ignored `unit_m`/`unit_i` and printed the base value
  under the family name (e.g. `"length: 100"`, not even a real unit); fixed
  in transit here, same as the other CHANGELOG-documented port fixes.
- Not yet declared: an admin `config_form()` (defaults to an empty
  declaration, same as any registered type that doesn't override it — see
  `tests/sample_types.RatingFeatureType`). A JS value-editor widget is a
  follow-up if/when this type needs an admin UI; nothing in the engine
  blocks adding one later (`registerValueEditor`/`registerConfigWidget`, see
  the Admin UI section below).

### Conditional rules (`rules.py`) — closed grammar, single pass

`FeatureDef.rules` is a **sibling of `mandatory`, never part of `config`**: a
rule is type-independent, while `config` goes through a strict per-type
serializer. The grammar is closed so both evaluators (this module and
attributes-react's `evaluateRules`) can be proven equal against one corpus:

```
Rule := { effect: require|show|hide|forbid_option|limit,
          when:   { all: [Cond, …≥1] } | { any: [Cond, …≥1] },   # exactly one key
          option?: str,          # forbid_option only, required there
          min?: num, max?: num } # limit only, at least one
Cond := { feature: slug, op: in|not_in, values: [str, …≥1] }
      | { feature: slug, op: filled|empty }
```

Anything else is `FeatureValidationError(INVALID_RULES)` at config-validation
time (`error.400.feature_invalid_rules`). An unknown controlling slug is **not**
an error — the same feature is reused in categories with different field sets,
so it simply reads as `empty`; `validate_configs_structured(configs,
known_slugs=...)` reports it as a non-blocking warning.

- **One pass, no fixed point.** `evaluate_rules(feature_defs, values)` reads the
  raw submitted values once. A controlling feature's own visibility is not
  consulted, so rule cycles are impossible by construction.
- **Comparison is on strings.** `stringify(value)` is the exact shared table
  (`False` -> `['false']` — a false bool is *filled*; a non-integral number ->
  its shortest decimal, never an exponent; a `{type, value}` DTO envelope is
  unwrapped). Both languages compare the same strings.
- **Rules reach types through the config, not through the types.**
  `narrow_config(config_dict, state)` drops forbidden options and replaces a
  *declared* `min`/`max`; the narrowed config then goes down the ordinary
  `parse_config` -> `validate_dto` path. So a forbidden option comes back as
  `not_in_options` and a tightened bound as `above_maximum` — **no new error
  codes for values, and every host type gets rules for free.** Narrowing never
  *introduces* a bound the config did not declare.
- **Requiredness is `RuleState.required`**, not `FeatureDef.mandatory`:
  `visible and (mandatory or any matching require)`. A hidden feature is never
  required, is not validated, and is dropped from the DAO even if a value was
  submitted. `header` is always visible and never required.

The shared corpus lives in `tests/golden/rules/{cases,pipeline}/` (record with
`GOLDEN_RECORD=1`); `tests/golden/rules/avito/` is filled by the importer.

### Vocabulary resolver seam (`vocabularies.py`)

`ref_select` / `ref_hierarchical_select` point at an **external** vocabulary
(`optionsRef = {vocabulary, level, parentFeature?}`) because the vocabularies
they exist for have thousands of terms per level — inlining options into a
category schema is not an option. This library declares only the protocol:

```python
class VocabularyResolver(Protocol):
    def describe(self, vocabulary) -> VocabularyInfo | None
    def exists(self, vocabulary, level, code) -> bool
    def is_child(self, vocabulary, level, code, parent_level, parent_code) -> bool
    def labels(self, vocabulary, level, codes) -> dict[str, str]
```

Two ways in, later wins: `STAPEL_ATTRIBUTES["VOCABULARY_RESOLVER"]` (dotted
path, resolved lazily; a class is instantiated once) and a runtime
`register_vocabulary_resolver(resolver)` from an `AppConfig.ready()`. **With no
resolver a ref-type CONFIG is loudly invalid** (`INVALID_CONFIG`, "no vocabulary
resolver registered") — at authoring time, not on the first submitted value.
Parsing a stored config never needs a resolver.

### The two ref-types

| | `ref_select` | `ref_hierarchical_select` |
|---|---|---|
| Config | `optionsRef{vocabulary, level, parentFeature?}`, `minSelected`, `maxSelected` (default 1), `uiStyle` | `vocabulary`, `levels` (root→leaf parent chain), `minDepth`, `maxDepth` |
| DTO | `{type, value: [code, …]}` | `{type, value: [code, …]}` — the path |
| DAO | codes + `labels` snapshot + `vocabulary`/`level` | codes + `labels` + `vocabulary`/`levels` |

- Codes are checked with `exists`; a filled `parentFeature` narrows the level to
  that term's children via `is_child` (violation -> `NOT_IN_OPTIONS`). An
  **empty** parent allows the whole level on purpose, so a form validates
  without forcing a fill order.
- `dto_to_dao` snapshots `labels` (unknown code labels as itself) so rendering a
  stored listing never reads the vocabulary; `format_value` uses only the DAO.
- `get_translation_keys()` is `[]`: term labels are owned by the vocabulary,
  not by the category schema.
- Facets read `value` (the codes), exactly as for `select`.

### `group` — the composite (a repeatable subform)

One feature holding a small table: a list of rows, each row a set of child
features of the *other* kinds. It exists because roughly 2 % of the Avito
autoload corpus is exactly this shape (2 468 fields carry `children`, e.g.
`DiscountLadderList` — "quantity from N, discount M %", up to five rows), and
no other kind could express it.

```json
{"type": "group",
 "fields": [{"slug": "quantity", "name": "Quantity", "mandatory": true,
             "config": {"type": "int", "min": 1}},
            {"slug": "discount", "name": "Discount", "config": {"type": "int", "min": 1, "max": 30}}],
 "repeat": {"min": 1, "max": 5}}
```

| | |
|---|---|
| Config | `fields` (child feature definitions, non-empty), `repeat` (`{min, max}` or `null`) |
| DTO | `{type, value: [{child_slug: value or {type, value}}, …]}` |
| DAO | `{type, value: [{child_slug: <child DAO with its own DaoMeta + order>}, …]}` |

- **Nesting depth is 1**, and it is enforced, not a convention: a child may not
  be a `group` (nor a `header`) — `INVALID_CONFIG`.
- **A child may not carry `rules`.** `evaluate_rules` reads a flat
  `{slug: value}` map of *top-level* features; a row's values are not in that
  namespace, so a rule written on a child could never fire and a rule outside
  could never read a child's value. Rather than accept such a rule and silently
  never fire it, the config is refused. Conditional behaviour for a composite is
  expressed **from outside**, as a rule on the group feature itself — `require`,
  `show` and `hide` all work on a group exactly as on any other kind.
- Each cell is validated by the child's own type through the ordinary registry
  entry points, so a group inherits every kind's constraints for free and a
  newly registered kind works inside a group the day it is registered. A cell
  failure keeps its own machine code and gains a path:
  `rows[1].discount: Value must be <= 30` with `error_params={"row": 1,
  "child": "discount"}`.
- **A row is its own value namespace**: a `ref_select` child narrowing by
  `optionsRef.parentFeature` reads the parent from the *same row*.
- `repeat: null` means one row; `repeat.min` bites on a submitted table, never
  on an empty optional one (an empty group is an absent value, and requiredness
  stays the pipeline's business).
- `get_translation_keys()` aggregates over the children — each child's `name`
  plus whatever the child's own type contributes. A child is not a catalog row,
  so nothing else would ever walk it.
- **Not a facet.** stapel-search maps `group` to `skip`: a table has no single
  filterable value. A composite is a form shape, not a search axis.
- No admin config form is declared (`config_form()` is `[]`): the Django admin
  edits a group's `fields` as raw JSON, and the schema-driven config editor
  falls back to its unsupported notice. The composer UI is
  `@stapel/attributes-react`.
- Careful: `FeatureDef.group` (a string, the *form section*) and the `group`
  *type* are different things that share a word.

### `validate_dto_in_context` — the sibling-values hook

The pipeline calls `BaseFeatureType.validate_dto_in_context(config, dto,
ValidationContext(values, feature_defs))`, whose default simply delegates to
`validate_dto` — every existing type notices nothing. Override it only when
validity genuinely depends on another field; `ref_select`'s parent narrowing is
the reference (and, so far, only) case.

### Validation API (what modules call)

All functions take `configs` first — any of: a list of `FeatureDef`s, a list
of feature-def dicts (`{"slug", "config", "mandatory", ...}`), or a mapping
`{slug: config-dict}` (e.g. the JSON payload of a future
`categories.features` comm function).

| Function | Returns | Use |
|---|---|---|
| `validate_dto(configs, dto)` | raises `ValidationError` (message per feature) | Gate before accepting a submission |
| `normalize_to_dao(configs, dto)` | `{slug: dao_dict}` with `order` + injected headers | Persisting validated values |
| `validate_dto_structured(configs, dto)` | `ValidationBatchResult` | API endpoints needing machine-readable per-feature results |
| `validate_configs_structured(configs)` | `ValidationBatchResult` | Saving attribute schemas (category editor) |
| `validate_dao_structured(configs, dao)` | `ValidationBatchResult` | Integrity checks on stored data |
| `validate_description(text, min_length=4, max_length=500)` | `FeatureValidationResult \| None` | Free-text length checks in the same vocabulary |

Error codes surface as `ValidationErrorCode` + `ref_value` + a localizable
`error.400.feature_*` key (`errors.ERROR_CODE_TO_KEY`).

#### Unknown config keys — silently dropped, warned (not rejected)

`parse_config` builds each type's typed config dataclass through a DRF
`DataclassSerializer` (`DictDataclassSerializer`). DRF's default
`to_internal_value` only reads the input keys it has a declared field for —
an input key with no matching dataclass field is neither an error nor
present in `validated_data`; it is just dropped. So a typo'd constraint
(`{"type": "string", "minLenght": 5}`) does not fail — it silently becomes a
config with no `minLength` at all.

Rejecting this outright would mean swapping every type's config serializer
for one with a strict/unknown-fields mode — a real change to the shared
parse seam every type plugin goes through, not a point fix. Instead,
`validate_configs_structured` does the cheap half: it diffs the raw config
dict's keys against the target dataclass's field names and, when the config
is otherwise valid, attaches a non-blocking `FeatureValidationResult.warnings`
list (e.g. `["Unknown config key(s) ignored: minLenght"]`). A warning never
flips `status`/`valid` to failed — the config *was* accepted, this only flags
that part of the input was dead weight. `validate_dto_structured` and
`validate_dao_structured` do not run this check (they parse configs already
known-good from storage, not freshly authored ones) — it is scoped to the
config-authoring path (category/attribute-schema editing).

### Translation keys

- `get_translation_keys(config)` — per-feature keys (labels, prefixes, ...).
- `get_builtin_translation_keys()` — static keys a type always contributes
  (`feature.bool.true`, `feature.date.name`, ...). Override in custom types;
  `collect_all_builtin_translation_keys()` aggregates over the *effective*
  registry, so vertical types feed the host's translation export too.

### Serializer factories

`get_feature_{config,dto,dao}_serializer_class()` and the
`get_feature_*_proxy_serializer()` OpenAPI variants rebuild whenever the
registry changes. Views in consuming modules should call the factory at
request/schema time, never cache the class at import.

## Admin UI — schema-driven config editor (Lit 3)

Python is the source of truth for each type's admin form. A type declares its
config form via `config_form()` → a list of `FormField(name, kind, label_key,
required, default, params)`; `form_declarations()` is a JSON snapshot of every
registered type (built-ins + `EXTRA_TYPES` + runtime). The committed Lit-3
bundle (`static/stapel_attributes/attributes-admin.js`, built from `static_src/`)
renders the form from that declaration — **a new type using only the standard
field-kinds gets an admin form with zero JS.**

**Field-kind dictionary** (`config_form.FIELD_KINDS`, minimally sufficient for the
eleven built-ins that declare a form): `number`, `text`, `checkbox`, `translatable_text`,
`number_options`, `string_options`, `color_options`, `select`,
`select_options_with_default`, `max_selected_dropdown`, `hierarchical_options`,
`timestamp`, `timestamp_array`. Validation stays Python-side (declarations +
structured errors); the JS mirrors only UX validation.

**Django widget**: `ConfigEditorWidget` (a `forms.Widget`) renders a
progressive-enhancement `<textarea>` (works with no JS) + a mount point + the
declarations/config/locale/messages via `json_script`; an inline ES-module
imports the bundle and mounts `<stapel-config-editor>`. Value editors for the
nine legacy-ported types (`bool`, `string`/`int`/`float`, `select`, `date`,
`hex_color`, `hierarchical_select`, `header`) render a DTO from a config;
unknown types — including the two ref-types, whose editor is a typeahead over
an HTTP vocabulary and therefore lives in attributes-react — fall back to
`UnsupportedEditor`.

### Admin seams (fork-free)

| Customize | Seam |
|---|---|
| Config form of a new type | `config_form()` field-kind declaration (zero JS for standard kinds) |
| Where a ref-type's terms come from | `STAPEL_ATTRIBUTES["VOCABULARY_RESOLVER"]` or `register_vocabulary_resolver()` |
| Exotic UI for a kind/type | JS registries: `window.StapelAttributes.registerConfigWidget(kind, factory)` / `registerValueEditor(type, factory)` — MERGE over built-ins |
| Look & feel | `--stapel-*` CSS vars (light + `[data-theme="dark"]`); `STAPEL_ATTRIBUTES["ADMIN_EXTRA_CSS"/"ADMIN_EXTRA_JS"]` |
| Widget behaviour | subclass `ConfigEditorWidget`, or swap via `STAPEL_ATTRIBUTES["ADMIN_WIDGETS"]` (dotted-path merge) |
| Admin locales | `STAPEL_ATTRIBUTES["ADMIN_LOCALES"]` — partial dict/static-path merged over built-in `en`/`ru` |

Worked example — a host ships a `size_grid` JS widget for its app-layer type
(paired with the `size_grid` feature type registered via `EXTRA_TYPES`):

```js
// fashion_vertical/static/.../size_grid_widget.js  (loaded via ADMIN_EXTRA_JS)
import { html, LitElement } from "https://.../lit";  // or the host's bundler
class SizeGridEditor extends LitElement { /* ...renders a table, emits a DTO... */ }
customElements.define("size-grid-editor", SizeGridEditor);
window.StapelAttributes.registerValueEditor(
  "size_grid",
  (opts) => Object.assign(new SizeGridEditor(), opts),
);
```

`registerConfigWidget(kind, factory)` works the same way for a config **field-kind**:
`<stapel-config-editor>` resolves every kind through the registry before its
built-in renderer, so a host factory overrides a built-in kind or supplies an
exotic one. Built-in kinds are seeded at import (a `BUILTIN_CONFIG_WIDGET`
sentinel = "render natively"), so `registeredConfigWidgetKinds()` lists them and
an override wins (later wins).

The screens that *drive* these components (feature-editor, children-editor,
convert-type) live in **stapel-categories**, not here (see
docs/attributes-admin-ui.md §"Разделение собственности").

### Dual build — django bundle + npm lib (`static_src/build.mjs`)

One source tree, two outputs:

| Build | `node build.mjs …` | Output | Lit | Registration |
|---|---|---|---|---|
| **django** | (default) | committed `static/stapel_attributes/` (drift-gated, **byte-stable**) | inlined | side-effect imports (`index.ts`) self-register |
| **lib** | `lib` | `dist/` (gitignored) `@stapel/attributes-admin` ESM + `.d.ts` | **peerDependency** (`^3`, external) | none on import — host calls `defineElements()` |

The editor/component modules keep their self-registration tail fenced by
`// @stapel-auto-define:start … :end`. The django build keeps it; the **lib**
build strips it (`strip-auto-define.mjs`) so the package is honestly
`sideEffects: false` and importing `lib.ts` registers nothing. Consumers
(`@stapel/attributes-react`) import `defineElements`, `mountConfigEditor`,
`createValueEditor`, the element classes, and the `ValidationErrorCode` mirror.
The django build sets esbuild `ignoreAnnotations: true` so the lib's
`sideEffects:false` can't prune the admin bundle's registrations. Publishing is
opt-in (not done here). Both builds are covered by vitest (`builds-lib.test.ts`
side-effect-free import + `defineElements`; `builds-django.test.ts` self-register
+ `window.StapelAttributes`).

### Cross-language golden bridge (`tests/golden/`)

The config a JS widget emits is validated by the Python engine; `tests/golden/`
pins that round-trip. One JSON corpus is run by **both** `tests/test_golden.py`
(pytest) and `static_src/src/golden.test.ts` (vitest), with a cross-agreement
assertion — the two engines must agree unless a case records an explicit
`divergence`. Regenerate expectations with `GOLDEN_RECORD=1` (byte-stable) and
keep `tests/golden/declarations.json` (the committed `form_declarations()`
snapshot, drift-gated) in sync when a declaration changes. The same bridge pins
the **error-code contract**: `tests/golden/error_codes.json` (generated from the
`ValidationErrorCode` enum) is asserted by both the Python runner and the TS
mirror `static_src/src/error-codes.ts` — a code added on one side but not the
other turns a test red.

The rule engine has its own corpus under `tests/golden/rules/` on the same
contract: `cases/` pins `evaluate_rules` semantics (every effect, operator and
connective plus the whole `stringify` table) and `pipeline/` pins the
end-to-end effect through `validate_dto_structured` + `normalize_to_dao`.
attributes-react runs a generated copy of both.

**Pattern contract**: a string `pattern` matches the **whole** value
(`re.fullmatch` / `^(?:…)$`) and is a JS-RegExp-compatible subset. String
length is counted in Unicode **code points** on both sides.

## Admin categories — `@access` declarations (admin-suite AS-5)

N/A — this library owns no Django models and no `admin.py` (verified:
no `models.py`/`models/` package anywhere outside `.venv`/`build`, no
`ModelAdmin` registrations). Attribute *values* live on the host
application's own tables (`CategoryFeature`-style DAOs in `types/*/dao.py`
write through host-provided storage, not a table this package migrates);
category/access classification is the owning host model's decision, not
this library's. Nothing to decorate.

## Anti-patterns

- **Don't fork to add a type** — the registry is the seam. If a new hook on
  `BaseFeatureType` is needed to express your type, that's an upstream
  contribution, not a fork.
- **Don't parse validation messages** — the machine code is on the exception
  (`FeatureValidationError.error_code`) and in batch results. Regex-parsing
  of messages is the exact defect this port removed.
- **Don't import Django models into the engine** — the boundary is
  `FeatureDef`. Model owners map ORM rows to `FeatureDef`s at the call site.
- **Don't give this library a comm surface / urls / models** — it is L1; if
  you need an endpoint or a table, it belongs in a module (stapel-categories,
  stapel-listings).
- **Don't bypass the settings namespace** with `os.getenv` at import time.
- **Don't cache polymorphic serializer classes at import time** — always go
  through the factories (they version-track the registry).
- **Don't extend the rule grammar locally** — it is closed so two evaluators
  can be proven equal. A rule that needs nesting or arithmetic is a design
  question, not a config.
- **Don't read `FeatureDef.mandatory` as the whole answer** — with rules in
  play, requiredness is `evaluate_rules(...)[slug].required`.
- **Don't inline a vocabulary into a config** — that is exactly what the
  ref-types and the resolver seam exist to avoid.

## App-layer override vs upstream contribution — rule of thumb

**App-layer** (host project or vertical package, no fork): registering extra
feature types (settings or runtime), custom translation keys via
`get_builtin_translation_keys`, calling the validation pipeline with your own
`FeatureDef` source, overriding a built-in type by re-registering its slug.

**Upstream contribution**: new hooks on `BaseFeatureType`, new
`ValidationErrorCode`s, changes to pipeline semantics (header injection,
ordering, empty-value policy), new generic (non-vertical) built-in types,
removal semantics for `EXTRA_TYPES`, **anything about the rule grammar** (it is
closed on both sides of the wire — a new effect or operator is a two-language
change plus corpus, never a local extension).

Litmus test: if you'd have to monkeypatch or edit code inside
`stapel_attributes/` — it's upstream. If a setting, a registered type or a
`FeatureDef` mapping gets you there — it's app-layer.
