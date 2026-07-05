"""Feature type registry — the library's flagship open seam.

Central registry for all feature types, with the house merge semantics:

1. **Built-ins** — the nine generic types shipped in ``stapel_attributes.types``,
   registered on first registry access;
2. **``STAPEL_ATTRIBUTES["EXTRA_TYPES"]``** — a list of dotted paths, merged
   over the built-ins and imported lazily. Each entry is either a
   ``BaseFeatureType`` subclass or a module whose import registers types via
   the decorator;
3. **Runtime registrations** — ``@register_feature_type`` /
   ``register_feature_type(cls)`` called directly (e.g. from a host app's
   ``AppConfig.ready()``).

Later registrations win per slug. Loading is additive and idempotent.
``registered_types()`` returns the effective slug -> instance mapping.

Key functions:

- parse_config: Convert config dict to typed dataclass
- parse_dto: Convert DTO dict to typed dataclass
- validate_feature_config: Validate and return typed config
- validate_feature_dto: Validate and return typed DTO
- dto_to_dao: Convert typed DTO to typed DAO
"""

from dataclasses import fields, is_dataclass
from importlib import import_module
from typing import Any, Dict, List, Optional, Type, TypeVar

from stapel_attributes.base import BaseFeatureType, FeatureDef, dataclass_to_dict_no_none
from stapel_attributes.exceptions import FeatureValidationError
from stapel_attributes.results import ValidationErrorCode

# Type variables
TConfig = TypeVar('TConfig')
TDto = TypeVar('TDto')
TDao = TypeVar('TDao')

# Effective registry of feature type instances (slug -> instance).
_FEATURE_TYPES: Dict[str, BaseFeatureType] = {}

# Bumped on every (re-)registration; the polymorphic serializer factories in
# ``stapel_attributes.serializers`` key their caches on it so late
# registrations are never missing from the mappings.
_version: int = 0

_builtins_loaded = False
_loaded_extra_paths: set = set()

# Re-entrancy guard: set while ``_ensure_loaded`` is importing built-ins/extras
# so the ``@register_feature_type`` decorators fired *during* that import do not
# recursively re-enter loading (which would reorder built-ins after extras).
_loading = False


def register_feature_type(cls: Type[BaseFeatureType]) -> Type[BaseFeatureType]:
    """
    Decorator to register a feature type (also callable directly at runtime).

    Usage:
        @register_feature_type
        class IntFeatureType(BaseFeatureType):
            slug = 'int'
            ...

    Re-registering a slug overrides the previous registration (later wins).

    A runtime registration first ensures the built-ins and ``EXTRA_TYPES`` are
    loaded, then applies on top of them — so a host override of a built-in slug
    (e.g. from ``AppConfig.ready()`` before the registry is first touched) is
    never clobbered by the lazy built-in load (later wins, per the house
    contract). The ``_loading`` guard keeps the decorators fired during that
    load from re-entering.
    """
    global _version
    if not _loading:
        _ensure_loaded()
    instance = cls()
    _FEATURE_TYPES[instance.slug] = instance
    _version += 1
    return cls


def _load_builtin_types() -> None:
    global _builtins_loaded
    if _builtins_loaded:
        return
    _builtins_loaded = True
    # Importing the package registers all built-in types via the decorator.
    import_module('stapel_attributes.types')


def _load_extra_types() -> None:
    """Load ``STAPEL_ATTRIBUTES["EXTRA_TYPES"]`` entries not seen yet.

    Called on every registry access, but each dotted path is imported at most
    once (additive merge). Without configured Django settings there are no
    extras to read — the built-ins still work.
    """
    try:
        from django.core.exceptions import ImproperlyConfigured
        try:
            from stapel_attributes.conf import attributes_settings
            extra_paths = list(attributes_settings.EXTRA_TYPES or [])
        except ImproperlyConfigured:
            return
    except ImportError:  # pragma: no cover - Django is a hard dependency
        return

    for path in extra_paths:
        if not path or path in _loaded_extra_paths:
            continue
        _loaded_extra_paths.add(path)
        try:
            import_module(path)
            continue
        except ImportError:
            pass
        # Not a module — resolve as a dotted path to a class.
        module_path, _, attr = path.rpartition('.')
        try:
            target = getattr(import_module(module_path), attr)
        except (ImportError, AttributeError, ValueError) as exc:
            _loaded_extra_paths.discard(path)
            raise ImportError(
                f"STAPEL_ATTRIBUTES['EXTRA_TYPES'] entry '{path}' is neither an "
                f"importable module nor a dotted path to a class: {exc}"
            ) from exc
        if not (isinstance(target, type) and issubclass(target, BaseFeatureType)):
            _loaded_extra_paths.discard(path)
            raise ImportError(
                f"STAPEL_ATTRIBUTES['EXTRA_TYPES'] entry '{path}' must point to a "
                f"BaseFeatureType subclass or a module, got {target!r}"
            )
        register_feature_type(target)


def _ensure_loaded() -> None:
    global _loading
    if _loading:
        return
    _loading = True
    try:
        _load_builtin_types()
        _load_extra_types()
    finally:
        _loading = False


def registry_version() -> int:
    """Monotonic counter, bumped on every registration (cache key for
    serializer factories)."""
    _ensure_loaded()
    return _version


def registered_types() -> Dict[str, BaseFeatureType]:
    """The effective ``slug -> feature type instance`` mapping (a copy).

    Built-ins <- ``EXTRA_TYPES`` <- runtime registrations, later wins.
    """
    _ensure_loaded()
    return dict(_FEATURE_TYPES)


def get_feature_type(slug: str) -> BaseFeatureType:
    """
    Get a feature type by its slug.

    Args:
        slug: The feature type slug (discriminator value)

    Returns:
        The feature type instance

    Raises:
        ValueError: If the feature type is not registered
    """
    _ensure_loaded()
    if slug not in _FEATURE_TYPES:
        available = ', '.join(sorted(_FEATURE_TYPES.keys()))
        raise ValueError(f"Unknown feature type: '{slug}'. Available types: {available}")
    return _FEATURE_TYPES[slug]


def get_all_feature_types() -> List[BaseFeatureType]:
    """Get all registered feature types."""
    _ensure_loaded()
    return list(_FEATURE_TYPES.values())


def get_all_type_slugs() -> List[str]:
    """Get all registered type slugs (sorted)."""
    _ensure_loaded()
    return sorted(_FEATURE_TYPES.keys())


# =============================================================================
# Parse functions: dict -> typed dataclass
# =============================================================================


def _flatten_serializer_errors(errors: Any, prefix: str = '') -> Dict[str, str]:
    """Flatten a nested DRF serializer ``.errors`` tree into
    ``{dotted.field.path: message}`` with plain ``str`` messages.

    Keeps the structured shape (so it JSON-serializes and localizes per field)
    without exposing ``ErrorDetail`` reprs or list nesting to the caller.
    """
    out: Dict[str, str] = {}
    if isinstance(errors, dict):
        for key, val in errors.items():
            path = f"{prefix}{key}" if not prefix else f"{prefix}.{key}"
            out.update(_flatten_serializer_errors(val, path))
    elif isinstance(errors, (list, tuple)):
        # A list of per-item dicts (nested serializers) or of message strings.
        if errors and all(isinstance(e, (dict, list, tuple)) for e in errors):
            for idx, item in enumerate(errors):
                path = f"{prefix}.{idx}" if prefix else str(idx)
                out.update(_flatten_serializer_errors(item, path))
        else:
            out[prefix or '_'] = '; '.join(str(e) for e in errors)
    else:
        out[prefix or '_'] = str(errors)
    return out


def parse_config(config_dict: Dict[str, Any]) -> Any:
    """
    Parse config dict into typed dataclass instance.

    Use this when you need typed access to config fields:
        config = parse_config(feature_def.config)
        if config.min is not None:  # typed field access
            ...

    Args:
        config_dict: Raw config dict with 'type' field

    Returns:
        Typed config dataclass instance (e.g., IntConfig)

    Raises:
        FeatureValidationError: If config is invalid or type unknown
    """
    if is_dataclass(config_dict) and not isinstance(config_dict, type):
        return config_dict  # already typed

    if not isinstance(config_dict, dict):
        raise FeatureValidationError(
            "Config must be a dict", code=ValidationErrorCode.INVALID_CONFIG,
        )

    if 'type' not in config_dict:
        raise FeatureValidationError(
            "Config must have a 'type' field", code=ValidationErrorCode.INVALID_CONFIG,
        )

    type_slug = config_dict['type']

    try:
        feature_type = get_feature_type(type_slug)
    except ValueError as e:
        raise FeatureValidationError(
            str(e), code=ValidationErrorCode.UNKNOWN_FEATURE_TYPE, ref_value=type_slug,
        )

    # Use serializer to properly handle nested dataclasses
    serializer_class = feature_type.config_serializer_class
    serializer = serializer_class(data=config_dict)

    if not serializer.is_valid():
        # B6: don't leak the raw DRF ``ErrorDetail`` repr into the message.
        # Flatten the serializer errors into plain per-field strings and carry
        # them as structured ``params`` so a consumer can localize per field,
        # while the message stays a short, stable human summary.
        field_errors = _flatten_serializer_errors(serializer.errors)
        summary = ', '.join(sorted(field_errors)) if field_errors else 'invalid'
        raise FeatureValidationError(
            f"Invalid config for type '{type_slug}' ({summary})",
            code=ValidationErrorCode.INVALID_CONFIG,
            params={'type': type_slug, 'config_errors': field_errors},
        )

    # The serializer returns dict (DictDataclassSerializer), convert to dataclass
    validated_data = serializer.validated_data
    if isinstance(validated_data, dict):
        config_class = feature_type.config_class
        valid_fields = {f.name for f in fields(config_class)}
        filtered_data = {k: v for k, v in validated_data.items() if k in valid_fields}
        try:
            return config_class(**filtered_data)
        except TypeError as e:
            raise FeatureValidationError(
                f"Invalid config for type '{type_slug}': {e}",
                code=ValidationErrorCode.INVALID_CONFIG,
            )

    return validated_data


def parse_dto(type_slug: str, dto_dict: Dict[str, Any]) -> Any:
    """
    Parse DTO dict into typed dataclass instance.

    Args:
        type_slug: Feature type slug (e.g., 'int', 'bool')
        dto_dict: Raw DTO dict

    Returns:
        Typed DTO dataclass instance (e.g., IntDto)

    Raises:
        FeatureValidationError: If DTO is invalid
    """
    try:
        feature_type = get_feature_type(type_slug)
    except ValueError as e:
        raise FeatureValidationError(
            str(e), code=ValidationErrorCode.UNKNOWN_FEATURE_TYPE, ref_value=type_slug,
        )

    dto_class = feature_type.dto_class
    valid_fields = {f.name for f in fields(dto_class)}
    filtered_data = {k: v for k, v in dto_dict.items() if k in valid_fields}

    try:
        return dto_class(**filtered_data)
    except TypeError as e:
        raise FeatureValidationError(
            f"Invalid DTO for type '{type_slug}': {e}",
            code=ValidationErrorCode.INVALID_TYPE,
        )


def dao_to_dict(dao: Any) -> Dict[str, Any]:
    """
    Convert DAO dataclass to dict for storage.

    Args:
        dao: Typed DAO dataclass instance

    Returns:
        Dict with None values excluded
    """
    if isinstance(dao, dict):
        return {k: v for k, v in dao.items() if v is not None}

    if is_dataclass(dao) and not isinstance(dao, type):
        return dataclass_to_dict_no_none(dao)

    return dao


# =============================================================================
# Validation functions
# =============================================================================


def validate_feature_config(config_dict: Dict[str, Any]) -> Any:
    """
    Validate config dict and return typed config instance.

    Args:
        config_dict: Raw config dict with 'type' field

    Returns:
        Typed config dataclass instance

    Raises:
        FeatureValidationError: If config is invalid
    """
    config = parse_config(config_dict)
    feature_type = get_feature_type(config.type)
    feature_type.validate_config(config)
    return config


def validate_feature_dto(config: Any, dto_dict: Dict[str, Any]) -> Any:
    """
    Validate DTO dict and return typed DTO instance.

    Args:
        config: Config (typed dataclass or dict with 'type' key)
        dto_dict: Raw DTO dict

    Returns:
        Typed DTO dataclass instance

    Raises:
        FeatureValidationError: If DTO is invalid
    """
    # Parse config to typed dataclass if it's a dict
    if isinstance(config, dict):
        config = parse_config(config)

    feature_type = get_feature_type(config.type)

    # Normalize and parse DTO
    dto = feature_type.normalize_dto(config, dto_dict)

    # Validate
    feature_type.validate_dto(config, dto)

    return dto


def dto_to_dao(config: Any, dto: Any, feature: FeatureDef) -> Any:
    """
    Convert typed DTO to typed DAO.

    Args:
        config: Config (typed dataclass or dict with 'type' key)
        dto: Typed DTO dataclass instance
        feature: The FeatureDef the value belongs to

    Returns:
        Typed DAO dataclass instance
    """
    # Parse config to typed dataclass if it's a dict
    if isinstance(config, dict):
        config = parse_config(config)

    feature_type = get_feature_type(config.type)
    return feature_type.dto_to_dao(config, dto, feature)


# =============================================================================
# Convenience functions
# =============================================================================


def normalize_feature_dto(config: Any, dto_dict: Dict[str, Any]) -> Any:
    """
    Normalize raw DTO dict into typed DTO dataclass.

    Args:
        config: Config (typed dataclass or dict with 'type' key)
        dto_dict: Raw DTO dict

    Returns:
        Typed DTO dataclass instance
    """
    if isinstance(config, dict):
        config = parse_config(config)

    feature_type = get_feature_type(config.type)
    return feature_type.normalize_dto(config, dto_dict)


def get_default_value(config: Any) -> Optional[Any]:
    """
    Get the default value for a feature configuration.

    Args:
        config: Config (typed dataclass or dict with 'type' key)

    Returns:
        Default value or None
    """
    if isinstance(config, dict):
        config = parse_config(config)

    feature_type = get_feature_type(config.type)
    return feature_type.get_default_value(config)


def format_feature_value(config: Any, dao: Any) -> str:
    """
    Format a feature DAO value for display.

    Args:
        config: Config (typed dataclass or dict with 'type' key)
        dao: Typed DAO dataclass instance (or dict)

    Returns:
        Formatted string for display
    """
    if isinstance(config, dict):
        if 'type' not in config:
            value = dao.get('value') if isinstance(dao, dict) else getattr(dao, 'value', None)
            return str(value) if value is not None else ''
        config = parse_config(config)

    feature_type = get_feature_type(config.type)
    return feature_type.format_value(config, dao)


# =============================================================================
# Translation-key helpers
# =============================================================================


def collect_translation_keys_for_feature(config: Any) -> List[str]:
    """
    Collect translation keys for a single feature based on its config.

    Args:
        config: Feature configuration (dataclass or dict with 'type' key)

    Returns:
        List of translation keys used by this feature
    """
    type_slug = config.type if hasattr(config, 'type') else config.get('type') if isinstance(config, dict) else None

    if not type_slug:
        return []

    try:
        feature_type = get_feature_type(type_slug)
    except ValueError:
        return []

    # Parse config if it's a dict
    if isinstance(config, dict):
        config = parse_config(config)

    return feature_type.get_translation_keys(config)


def collect_all_builtin_translation_keys() -> set:
    """
    Collect all static translation keys contributed by registered feature
    types (built-ins and host-registered alike), via each type's
    ``get_builtin_translation_keys()`` hook.

    Returns:
        Set of all built-in translation keys
    """
    keys = set()
    for feature_type in get_all_feature_types():
        keys.update(feature_type.get_builtin_translation_keys())
    return keys


__all__ = [
    'register_feature_type',
    'registered_types',
    'registry_version',
    'get_feature_type',
    'get_all_feature_types',
    'get_all_type_slugs',
    'parse_config',
    'parse_dto',
    'dao_to_dict',
    'validate_feature_config',
    'validate_feature_dto',
    'dto_to_dao',
    'normalize_feature_dto',
    'get_default_value',
    'format_feature_value',
    'collect_translation_keys_for_feature',
    'collect_all_builtin_translation_keys',
]
