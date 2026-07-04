"""stapel-attributes — typed attributes engine for the Stapel framework.

A polymorphic type system for attribute (feature) configurations: an open
registry of feature types, Config/DTO/DAO layering per type, polymorphic
DRF serializers with OpenAPI schemas, and a structured value-validation
pipeline (DTO -> DAO). Ported from legacy-catalog's ``categories/feature_types``
engine; see MODULE.md for provenance and extension points.

This is an L1 *library*: it has no models, migrations, views, urls or comm
surface of its own. Both stapel-categories (schema side) and stapel-listings
(value side) import it.

Public API is lazily exported (PEP 562) — importing this package never pulls
in Django or requires configured settings.
"""

__all__ = [
    # Settings
    "attributes_settings",
    # Base abstractions
    "BaseFeatureType",
    "DaoMeta",
    "DictDataclassSerializer",
    "FeatureDef",
    "dataclass_to_dict_no_none",
    # Structured errors & results
    "FeatureValidationError",
    "FeatureValidationResult",
    "ValidationBatchResult",
    "ValidationErrorCode",
    "ValidationStatus",
    # Registry
    "register_feature_type",
    "registered_types",
    "get_feature_type",
    "get_all_feature_types",
    "get_all_type_slugs",
    # Parse / convert
    "parse_config",
    "parse_dto",
    "dao_to_dict",
    "validate_feature_config",
    "validate_feature_dto",
    "dto_to_dao",
    "normalize_feature_dto",
    "get_default_value",
    "format_feature_value",
    "collect_translation_keys_for_feature",
    "collect_all_builtin_translation_keys",
    # Validation pipeline (configs -> DTO -> DAO)
    "coerce_feature_defs",
    "get_feature_slug",
    "build_feature_lookup",
    "validate_dto",
    "normalize_to_dao",
    "validate_dto_structured",
    "validate_configs_structured",
    "validate_dao_structured",
    "validate_description",
    # Config-form contract (schema-driven admin UI)
    "FIELD_KINDS",
    "FormField",
    "form_declarations",
    "ConfigEditorWidget",
    "get_config_editor_widget",
    # Polymorphic serializer factories
    "get_feature_config_serializer_class",
    "get_feature_dto_serializer_class",
    "get_feature_dao_serializer_class",
    "get_feature_config_proxy_serializer",
    "get_feature_dto_proxy_serializer",
    "get_feature_dao_proxy_serializer",
]

# name -> submodule that defines it. Resolution is deferred until first
# attribute access so that `import stapel_attributes` stays Django-free.
_LAZY_EXPORTS = {
    "attributes_settings": ".conf",
    # base
    "BaseFeatureType": ".base",
    "DaoMeta": ".base",
    "DictDataclassSerializer": ".base",
    "FeatureDef": ".base",
    "dataclass_to_dict_no_none": ".base",
    # errors & results
    "FeatureValidationError": ".exceptions",
    "FeatureValidationResult": ".results",
    "ValidationBatchResult": ".results",
    "ValidationErrorCode": ".results",
    "ValidationStatus": ".results",
    # registry
    "register_feature_type": ".registry",
    "registered_types": ".registry",
    "get_feature_type": ".registry",
    "get_all_feature_types": ".registry",
    "get_all_type_slugs": ".registry",
    "parse_config": ".registry",
    "parse_dto": ".registry",
    "dao_to_dict": ".registry",
    "validate_feature_config": ".registry",
    "validate_feature_dto": ".registry",
    "dto_to_dao": ".registry",
    "normalize_feature_dto": ".registry",
    "get_default_value": ".registry",
    "format_feature_value": ".registry",
    "collect_translation_keys_for_feature": ".registry",
    "collect_all_builtin_translation_keys": ".registry",
    # validation pipeline
    "coerce_feature_defs": ".validation",
    "get_feature_slug": ".validation",
    "build_feature_lookup": ".validation",
    "validate_dto": ".validation",
    "normalize_to_dao": ".validation",
    "validate_dto_structured": ".validation",
    "validate_configs_structured": ".validation",
    "validate_dao_structured": ".validation",
    "validate_description": ".validation",
    # config-form contract
    "FIELD_KINDS": ".config_form",
    "FormField": ".config_form",
    "form_declarations": ".config_form",
    # admin widget (Django-importing; lazy so package import stays Django-free)
    "ConfigEditorWidget": ".widgets",
    "get_config_editor_widget": ".widgets",
    # serializer factories
    "get_feature_config_serializer_class": ".serializers",
    "get_feature_dto_serializer_class": ".serializers",
    "get_feature_dao_serializer_class": ".serializers",
    "get_feature_config_proxy_serializer": ".serializers",
    "get_feature_dto_proxy_serializer": ".serializers",
    "get_feature_dao_proxy_serializer": ".serializers",
}


def __getattr__(name):
    if name in _LAZY_EXPORTS:
        from importlib import import_module

        value = getattr(import_module(_LAZY_EXPORTS[name], __name__), name)
        globals()[name] = value  # cache for subsequent lookups
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return sorted(set(globals()) | set(__all__))
