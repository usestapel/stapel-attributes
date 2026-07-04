"""Polymorphic serializers for feature types.

Uses drf-polymorphic to handle polymorphic serialization/deserialization
with automatic OpenAPI schema generation via drf-spectacular.

Note: drf-polymorphic requires serializer_mapping as a class attribute,
checked at __new__ time. We use factory functions to create serializer
classes with the mapping set dynamically after all types are registered.
Because the registry is open (EXTRA_TYPES / runtime registration), the
factories cache per registry version: registering a new type invalidates
the cached classes, so late registrations are always reflected.
"""

from typing import Dict, List, Tuple, Type

from rest_framework import serializers
from drf_polymorphic.serializers import PolymorphicSerializer
from drf_spectacular.utils import PolymorphicProxySerializer

from stapel_attributes.registry import get_all_feature_types, get_all_type_slugs, registry_version


def _get_config_serializers() -> List[Type[serializers.Serializer]]:
    """Get list of all config serializer classes."""
    return [ft.config_serializer_class for ft in get_all_feature_types()]


def _get_dto_serializers() -> List[Type[serializers.Serializer]]:
    """Get list of all DTO serializer classes."""
    return [ft.dto_serializer_class for ft in get_all_feature_types()]


def _get_dao_serializers() -> List[Type[serializers.Serializer]]:
    """Get list of all DAO serializer classes."""
    return [ft.dao_serializer_class for ft in get_all_feature_types()]


def _build_mapping(kind: str) -> Dict[str, Type[serializers.Serializer]]:
    """Build slug -> serializer class mapping for the given layer."""
    attr = f'{kind}_serializer_class'
    return {ft.slug: getattr(ft, attr) for ft in get_all_feature_types()}


def _get_type_choices():
    """Get all registered type slugs as choices."""
    return [(s, s) for s in get_all_type_slugs()]


# kind -> (registry_version, serializer class)
_serializer_cache: Dict[str, Tuple[int, Type[PolymorphicSerializer]]] = {}

_CLASS_NAMES = {
    'config': 'FeatureConfigPolymorphicSerializer',
    'dto': 'FeatureDtoPolymorphicSerializer',
    'dao': 'FeatureDaoPolymorphicSerializer',
}

_DOCS = {
    'config': """
        Polymorphic serializer for feature configs.

        Handles serialization/deserialization of feature configurations
        based on the 'type' discriminator field.
        """,
    'dto': """
        Polymorphic serializer for feature DTOs.

        Handles serialization/deserialization of feature data
        from clients when creating/updating listings.
        Non-strict: unknown types during output serialization
        return base fields instead of crashing (draft payloads
        may contain raw unvalidated data).
        """,
    'dao': """
        Polymorphic serializer for feature DAOs.

        Handles serialization/deserialization of feature data
        stored in the owning model's JSON field.
        """,
}


def _get_polymorphic_serializer_class(kind: str) -> Type[PolymorphicSerializer]:
    version = registry_version()
    cached = _serializer_cache.get(kind)
    if cached is not None and cached[0] == version:
        return cached[1]

    attrs = {
        'serializer_mapping': _build_mapping(kind),
        'discriminator_field': 'type',
        'type': serializers.ChoiceField(choices=_get_type_choices()),
        '__doc__': _DOCS[kind],
    }
    if kind == 'dto':
        attrs['strict'] = False

    cls = type(_CLASS_NAMES[kind], (PolymorphicSerializer,), attrs)
    _serializer_cache[kind] = (version, cls)
    return cls


def get_feature_config_serializer_class() -> Type[PolymorphicSerializer]:
    """
    Get or create the FeatureConfigPolymorphicSerializer class.

    This factory function ensures the serializer_mapping reflects the
    current effective registry (built-ins + EXTRA_TYPES + runtime).
    """
    return _get_polymorphic_serializer_class('config')


def get_feature_dto_serializer_class() -> Type[PolymorphicSerializer]:
    """
    Get or create the FeatureDtoPolymorphicSerializer class.

    This factory function ensures the serializer_mapping reflects the
    current effective registry (built-ins + EXTRA_TYPES + runtime).
    """
    return _get_polymorphic_serializer_class('dto')


def get_feature_dao_serializer_class() -> Type[PolymorphicSerializer]:
    """
    Get or create the FeatureDaoPolymorphicSerializer class.

    This factory function ensures the serializer_mapping reflects the
    current effective registry (built-ins + EXTRA_TYPES + runtime).
    """
    return _get_polymorphic_serializer_class('dao')


# ============================================================================
# OpenAPI Schema Serializers (using drf-spectacular's PolymorphicProxySerializer)
# ============================================================================

# kind -> (registry_version, proxy serializer)
_proxy_cache: Dict[str, Tuple[int, PolymorphicProxySerializer]] = {}

_PROXY_COMPONENTS = {
    'config': ('FeatureConfig', _get_config_serializers),
    'dto': ('FeatureDto', _get_dto_serializers),
    'dao': ('FeatureDao', _get_dao_serializers),
}


def _get_proxy_serializer(kind: str) -> PolymorphicProxySerializer:
    version = registry_version()
    cached = _proxy_cache.get(kind)
    if cached is not None and cached[0] == version:
        return cached[1]

    component_name, get_serializers = _PROXY_COMPONENTS[kind]
    proxy = PolymorphicProxySerializer(
        component_name=component_name,
        serializers=get_serializers(),
        resource_type_field_name='type',
    )
    _proxy_cache[kind] = (version, proxy)
    return proxy


def get_feature_config_proxy_serializer():
    """
    Get PolymorphicProxySerializer for feature config OpenAPI schema.

    Returns a serializer that generates proper oneOf schema with discriminator.
    """
    return _get_proxy_serializer('config')


def get_feature_dto_proxy_serializer():
    """
    Get PolymorphicProxySerializer for feature DTO OpenAPI schema.

    Returns a serializer that generates proper oneOf schema with discriminator.
    """
    return _get_proxy_serializer('dto')


def get_feature_dao_proxy_serializer():
    """
    Get PolymorphicProxySerializer for feature DAO OpenAPI schema.

    Returns a serializer that generates proper oneOf schema with discriminator.
    """
    return _get_proxy_serializer('dao')


__all__ = [
    'get_feature_config_serializer_class',
    'get_feature_dto_serializer_class',
    'get_feature_dao_serializer_class',
    'get_feature_config_proxy_serializer',
    'get_feature_dto_proxy_serializer',
    'get_feature_dao_proxy_serializer',
]
