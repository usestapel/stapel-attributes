"""Base abstractions of the typed-attribute engine.

This module defines the core abstractions:

- ``BaseFeatureType``: generic type handler with typed validation and serializers
- ``DictDataclassSerializer``: DataclassSerializer for polymorphic compatibility (returns dict)
- ``DaoMeta``: base dataclass with common metadata fields for all DAOs
- ``FeatureDef``: the plain feature-definition structure the engine operates on.

Unlike the legacy-catalog origin, the engine is decoupled from any Django
model: ``dto_to_dao`` and the validation pipeline receive :class:`FeatureDef`
structures (built from JSON/dicts or by a model owner such as the future
stapel-categories module), never ORM instances.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, fields, is_dataclass
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from rest_framework import serializers
from rest_framework_dataclasses.serializers import DataclassSerializer


# Type variables for generic BaseFeatureType
TConfig = TypeVar('TConfig')
TDto = TypeVar('TDto')
TDao = TypeVar('TDao')


def dataclass_to_dict_no_none(instance: Any) -> Dict[str, Any]:
    """
    Convert dataclass to dict, excluding None values.
    Recursively handles nested dataclasses and lists.
    """
    if not is_dataclass(instance) or isinstance(instance, type):
        return instance

    result = {}
    for field in fields(instance):
        value = getattr(instance, field.name)

        if value is None:
            continue

        if is_dataclass(value) and not isinstance(value, type):
            value = dataclass_to_dict_no_none(value)
        elif isinstance(value, list):
            value = [
                dataclass_to_dict_no_none(item) if is_dataclass(item) and not isinstance(item, type) else item
                for item in value
            ]

        result[field.name] = value

    return result


# Backwards-compatible alias (the legacy framework exported the underscored name).
_dataclass_to_dict_no_none = dataclass_to_dict_no_none


class DictDataclassSerializer(DataclassSerializer):
    """
    DataclassSerializer that returns dict for drf-polymorphic compatibility.

    Features:
    - Returns dict for compatibility with drf-polymorphic
    - Excludes None values from serialized output (reduces JSON size)
    - Handles nested dataclasses efficiently
    - Allows blank strings for Optional[str] fields

    Note: Use parse_config/parse_dto from the registry to get typed dataclass
    instances when you need type-safe access to fields.
    """

    class Meta:
        extra_kwargs = {}

    def get_fields(self):
        """Override to allow blank strings for optional CharField fields."""
        fields = super().get_fields()

        for field_name, field in fields.items():
            # Allow blank for optional string fields
            if isinstance(field, serializers.CharField):
                if field.allow_null or not field.required:
                    field.allow_blank = True

        return fields

    def to_internal_value(self, data):
        """Deserialize input data to dict (not dataclass)."""
        if isinstance(data, dict):
            instance = super().to_internal_value(data)
            if instance is not None and is_dataclass(instance) and not isinstance(instance, type):
                return dataclass_to_dict_no_none(instance)
            return instance
        return data

    def to_representation(self, instance):
        """Serialize dataclass/dict to dict, excluding None values."""
        if isinstance(instance, dict):
            return {k: v for k, v in instance.items() if v is not None}

        if is_dataclass(instance) and not isinstance(instance, type):
            return dataclass_to_dict_no_none(instance)

        return super().to_representation(instance)


@dataclass
class DaoMeta:
    """
    Common metadata fields for all DAO types.

    All DAO dataclasses should inherit from this to include:
    - name: Feature name (translation key) for UI display
    - order: Display order in feature list
    - title: Whether to show in listing title
    - badge: Whether to show as badge
    - translate: Translation mode ('all', 'title', 'none')

    Example:
        @dataclass
        class BoolDao(DaoMeta):
            type: Literal['bool'] = 'bool'
            value: bool = False
    """
    name: Optional[str] = None
    order: Optional[int] = None
    title: Optional[bool] = None
    badge: Optional[bool] = None
    translate: Optional[str] = None  # 'all' | 'title' | 'none'


@dataclass
class FeatureDef:
    """A feature definition — the structure the engine operates on.

    This is the library-level replacement for legacy's ``categories.models.Feature``:
    the owning module (e.g. stapel-categories) materializes its model rows into
    ``FeatureDef`` instances (or plain dicts of the same shape) and hands them
    to the validation pipeline.

    Attributes:
        slug: Payload key the feature is submitted under.
        config: Type-specific configuration dict with a ``type`` discriminator
            (or an already-parsed Config dataclass).
        id: Optional stable identifier (also accepted as a payload key).
        name: Display name / translation key (defaults to ``slug``).
        mandatory: Whether a value is required.
        show_at_title: Whether the value is shown in the listing title.
        show_as_badge: Whether the value is shown as a badge.
        translate: Translation mode ('all' | 'title' | 'none').
    """
    slug: str
    config: Union[Dict[str, Any], Any]
    id: Optional[Union[int, str]] = None
    name: Optional[str] = None
    mandatory: bool = False
    show_at_title: bool = False
    show_as_badge: bool = False
    translate: str = 'all'

    def __post_init__(self) -> None:
        if self.name is None:
            self.name = self.slug

    @classmethod
    def from_dict(cls, data: Dict[str, Any], slug: Optional[str] = None) -> 'FeatureDef':
        """Build a FeatureDef from a plain dict (e.g. a comm-function payload).

        Accepted keys: ``slug``, ``config``, ``id``, ``name``, ``mandatory``,
        ``show_at_title``, ``show_as_badge``, ``translate``. Unknown keys are
        ignored. ``slug`` may alternatively be supplied as an argument (mapping
        form ``{slug: {...}}``).
        """
        resolved_slug = data.get('slug') or slug
        if not resolved_slug:
            raise ValueError("FeatureDef requires a 'slug' (key or field)")
        known = {f.name for f in fields(cls)}
        kwargs = {k: v for k, v in data.items() if k in known and k != 'slug'}
        if 'config' not in kwargs:
            raise ValueError(f"FeatureDef '{resolved_slug}' requires a 'config'")
        return cls(slug=str(resolved_slug), **kwargs)


class BaseFeatureType(ABC, Generic[TConfig, TDto, TDao]):
    """
    Base class for feature type implementations.

    Generic type parameters:
    - TConfig: Configuration dataclass (e.g., IntConfig)
    - TDto: Data Transfer Object dataclass (e.g., IntDto)
    - TDao: Data Access Object dataclass (e.g., IntDao)

    Each feature type must define:
    - slug: unique identifier (discriminator value)
    - name: human-readable name
    - config_class: dataclass type for configuration
    - dto_class: dataclass type for DTO (input from frontend)
    - dao_class: dataclass type for DAO (stored representation)
    - config_serializer_class: DRF serializer for config
    - dto_serializer_class: DRF serializer for DTO
    - dao_serializer_class: DRF serializer for DAO

    Methods receive typed dataclass instances (not dicts) for type safety.
    Validation failures should be raised as
    :class:`stapel_attributes.exceptions.FeatureValidationError` so the
    machine error code travels with the exception.
    """

    slug: str
    name: str

    # Dataclass types
    config_class: Type[TConfig]
    dto_class: Type[TDto]
    dao_class: Type[TDao]

    # Serializer classes
    config_serializer_class: Type[serializers.Serializer]
    dto_serializer_class: Type[serializers.Serializer]
    dao_serializer_class: Type[serializers.Serializer]

    @abstractmethod
    def validate_config(self, config: TConfig) -> None:
        """
        Validate the feature configuration.

        Args:
            config: Typed configuration dataclass instance

        Raises:
            FeatureValidationError: If configuration is invalid
        """
        pass

    @abstractmethod
    def validate_dto(self, config: TConfig, dto: TDto) -> None:
        """
        Validate DTO data against configuration.

        Args:
            config: Typed configuration dataclass instance
            dto: Typed DTO dataclass instance

        Raises:
            FeatureValidationError: If DTO data is invalid
        """
        pass

    @abstractmethod
    def dto_to_dao(self, config: TConfig, dto: TDto, feature: FeatureDef) -> TDao:
        """
        Convert DTO to DAO with metadata from config and feature definition.

        Args:
            config: Typed configuration dataclass instance
            dto: Typed DTO dataclass instance
            feature: The FeatureDef the value belongs to

        Returns:
            Typed DAO dataclass instance
        """
        pass

    def get_default_config(self) -> Dict[str, Any]:
        """Return the default configuration dict for this type."""
        return {'type': self.slug}

    def config_form(self) -> List[Any]:
        """Declare this type's admin config form as a list of ``FormField``.

        Python is the source of truth for the config-form schema
        (docs/attributes-admin-ui.md decision 1): the admin JS renders the form
        from this declaration, so a type using only the standard field-kinds
        needs zero JS. The nine built-ins resolve their ported declaration by
        slug from ``config_form.BUILTIN_FORMS``; host-registered types override
        this to declare their own fields (or return ``[]`` and ship a custom JS
        config widget). Kinds must be keys of ``config_form.FIELD_KINDS``.
        """
        from stapel_attributes.config_form import BUILTIN_FORMS

        builder = BUILTIN_FORMS.get(self.slug)
        return builder() if builder else []

    def get_default_value(self, config: TConfig) -> Optional[Any]:
        """
        Return the default value for this feature type.

        Args:
            config: Typed configuration dataclass instance

        Returns:
            Default value or None
        """
        return None

    def normalize_dto(self, config: TConfig, dto_data: Dict[str, Any]) -> TDto:
        """
        Normalize raw DTO dict data into typed DTO dataclass.

        Override in subclasses for type-specific normalization.

        Args:
            config: Typed configuration dataclass instance
            dto_data: Raw DTO data as dict

        Returns:
            Typed DTO dataclass instance
        """
        # Default: construct DTO from dict
        valid_fields = {f.name for f in fields(self.dto_class)}
        filtered_data = {k: v for k, v in dto_data.items() if k in valid_fields}
        return self.dto_class(**filtered_data)

    def is_user_editable(self, config: TConfig) -> bool:
        """
        Check if this feature can be edited by users.

        Args:
            config: Typed configuration dataclass instance

        Returns:
            True if user can edit, False if locked
        """
        return True

    def format_value(self, config: TConfig, dao: TDao) -> str:
        """
        Format DAO value for display.

        Args:
            config: Typed configuration dataclass instance
            dao: Typed DAO dataclass instance

        Returns:
            Formatted string for display
        """
        value = getattr(dao, 'value', None)
        return str(value) if value is not None else ''

    def get_translation_keys(self, config: TConfig) -> List[str]:
        """
        Return translation keys used by a concrete feature configuration.

        Args:
            config: Typed configuration dataclass instance

        Returns:
            List of translation key strings
        """
        return []

    def get_builtin_translation_keys(self) -> List[str]:
        """
        Return static translation keys this type contributes regardless of
        configuration (e.g. 'feature.bool.true'). Used by
        ``collect_all_builtin_translation_keys``; custom types registered by
        the host may override this to publish their own keys.
        """
        return []

    def __str__(self) -> str:
        return f"{self.name} ({self.slug})"

    def __repr__(self) -> str:
        return f"<FeatureType: {self.slug}>"


__all__ = [
    'BaseFeatureType',
    'DaoMeta',
    'DictDataclassSerializer',
    'FeatureDef',
    'dataclass_to_dict_no_none',
]
