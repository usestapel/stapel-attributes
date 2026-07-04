# stapel-attributes

Typed attributes engine for the [Stapel framework](https://github.com/usestapel) —
a polymorphic type system for attribute ("feature") configurations: an open
registry of feature types, Config/DTO/DAO layering per type, polymorphic DRF
serializers with OpenAPI schemas, and a structured value-validation pipeline.

This is an **L1 library**, not a module: it ships no models, migrations,
views, urls or comm surface. Both `stapel-categories` (attribute schema) and
`stapel-listings` (attribute values) import it — the code both need
synchronously lives one layer down, like `stapel-core` itself.

Provenance: port of the `categories/feature_types` engine and the
`ads` validation pipeline from legacy-catalog (see CHANGELOG for what was
fixed in transit).

## Install

```bash
pip install stapel-attributes
```

No `INSTALLED_APPS` entry, no urls — just import it:

```python
from stapel_attributes import (
    FeatureDef,
    validate_dto,
    normalize_to_dao,
    validate_dto_structured,
)

configs = [
    FeatureDef(slug="mileage", config={"type": "int", "min": 0, "postfix": "km"}),
    FeatureDef(slug="condition", config={"type": "bool"}, mandatory=True),
]
payload = {"mileage": {"type": "int", "value": 120000},
           "condition": {"type": "bool", "value": True}}

validate_dto(configs, payload)              # raises ValidationError on failure
dao = normalize_to_dao(configs, payload)    # {"mileage": {"type": "int", "value": 120000, "postfix": "km", "order": 0}, ...}
result = validate_dto_structured(configs, payload)  # machine-readable batch result
```

## Built-in types

`int`, `float`, `string`, `bool`, `hex_color`, `select`, `date`, `header`,
`hierarchical_select`. Each type is a plugin: a Config dataclass (schema), a
DTO (client input), a DAO (stored value + display metadata) and a handler
(`BaseFeatureType[TConfig, TDto, TDao]`).

Marketplace-specific types (size grids, convertible units, ...) are **not**
shipped — hosts register their own via the open registry (see MODULE.md for
the worked example).

## Settings

All configuration lives in the `STAPEL_ATTRIBUTES` namespace (dict setting,
flat setting, or env var — resolved lazily):

| Key | Default | Meaning |
|---|---|---|
| `EXTRA_TYPES` | `[]` | Dotted paths of extra feature types, **merged** over the built-ins (each entry: a `BaseFeatureType` subclass or a module that registers types on import). |

## Structured validation

Every validation failure carries a machine code end-to-end
(`ValidationErrorCode`) via `FeatureValidationError` — no message parsing.
Batch validators return `ValidationBatchResult` rows with `error`,
`ref_value`, `localizable_error` (an `error.400.feature_*` key) and `params`.

## Extension points

See [MODULE.md](MODULE.md) — the agent-facing map of every fork-free seam
(settings, the type registry, serializer factories, translation-key hooks).

## Development

```bash
pip install -e . && pip install pytest pytest-django ruff
./setup-hooks.sh
pytest tests/
```

## License

MIT
