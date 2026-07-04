# stapel-attributes — MODULE.md

> Agent-facing map of this package: what it provides, where to extend it
> without forking, and what not to do. Kept in the same PR as any change
> to a seam. See also README.md and CHANGELOG.md.

**Kind: L1 library** — importable by any module (stapel-categories,
stapel-listings, ...); it has **no** models, migrations, views, urls, comm
surface or service identity of its own. Provenance: port of legacy-catalog's
`categories/feature_types` engine + the `ads` value-validation pipeline
(defects fixed in transit — see CHANGELOG 0.1.0).

## What this library provides

| Area | Contents |
|---|---|
| Engine core (`base.py`) | `BaseFeatureType[TConfig, TDto, TDao]` — the type-plugin ABC; `DictDataclassSerializer` (dataclass serializer returning dicts, drf-polymorphic-compatible); `DaoMeta` (shared DAO metadata: name/order/title/badge/translate); `FeatureDef` — the plain feature-definition structure the engine operates on (slug, config, id, name, mandatory, display flags) |
| Type registry (`registry.py`) | Open registry (`register_feature_type`, `registered_types`, `get_feature_type`, `get_all_type_slugs`); parse/convert helpers (`parse_config`, `parse_dto`, `dao_to_dict`, `dto_to_dao`, `normalize_feature_dto`, `validate_feature_config`, `validate_feature_dto`, `format_feature_value`, `get_default_value`); translation-key helpers |
| Built-in types (`types/`) | `int`, `float`, `string`, `bool`, `hex_color`, `select`, `date`, `header`, `hierarchical_select` — each a plugin directory of `config.py` / `dto.py` / `dao.py` / `type.py` |
| Polymorphic serializers (`serializers.py`) | Factories for `FeatureConfig`/`FeatureDto`/`FeatureDao` polymorphic serializers (drf-polymorphic, `type` discriminator) + `PolymorphicProxySerializer`s for OpenAPI (drf-spectacular); caches keyed on the registry version, so late registrations are always reflected |
| Validation pipeline (`validation.py`) | `validate_dto(configs, dto)` (raise-style), `normalize_to_dao(configs, dto)` (DTO→DAO with header injection and ordering), `validate_dto_structured` / `validate_configs_structured` / `validate_dao_structured` (batch results), `validate_description`; `coerce_feature_defs` accepts FeatureDef lists, dicts, or `{slug: config}` mappings |
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
   `DaoMeta` (name/order/title/badge/translate).
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

### The type registry — open registry with MERGE semantics (flagship seam)

Three layers, later wins per slug:

1. built-ins (`stapel_attributes.types` — the nine generic types);
2. `STAPEL_ATTRIBUTES["EXTRA_TYPES"]` — merged over the built-ins;
3. runtime `register_feature_type(cls)` — e.g. from a host app's
   `AppConfig.ready()`; re-registering a slug overrides it.

`registered_types()` returns the effective `slug -> instance` mapping.
The polymorphic serializer factories and the validation pipeline all resolve
against this effective registry, so a registered custom type participates in
validation, DAO normalization and OpenAPI schemas with zero further wiring.

#### Worked example: registering a marketplace `size_grid` type

legacy's `size_grid` (clothing/shoe size tables) and `convertible_unit` are
deliberately **not** shipped — they are marketplace vertical types. This is
how a vertical package adds one:

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

## App-layer override vs upstream contribution — rule of thumb

**App-layer** (host project or vertical package, no fork): registering extra
feature types (settings or runtime), custom translation keys via
`get_builtin_translation_keys`, calling the validation pipeline with your own
`FeatureDef` source, overriding a built-in type by re-registering its slug.

**Upstream contribution**: new hooks on `BaseFeatureType`, new
`ValidationErrorCode`s, changes to pipeline semantics (header injection,
ordering, empty-value policy), new generic (non-vertical) built-in types,
removal semantics for `EXTRA_TYPES`.

Litmus test: if you'd have to monkeypatch or edit code inside
`stapel_attributes/` — it's upstream. If a setting, a registered type or a
`FeatureDef` mapping gets you there — it's app-layer.
