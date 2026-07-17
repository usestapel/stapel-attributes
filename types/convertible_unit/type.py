"""Convertible Unit Feature Type - Type Handler.

Port of the legacy marketplace catalog's
``categories/feature_types/types/convertible_unit`` (MODULE.md's own worked
"registering a marketplace size_grid/convertible_unit type" example — this
finally ships the latter as a built-in rather than a vertical registration).

Fixed while porting (do not reintroduce — mirrors the CHANGELOG 0.1.0/0.4.0
"defects fixed in transit" precedent for this library):

- The legacy ``normalize_dto`` accepted a nested ``{value: {value, unit}}``
  payload but only ever read ``value.value`` — the ``unit`` the user actually
  entered the number in was parsed out and silently discarded, so submissions
  in a non-base unit (e.g. ``100 cm``) were stored as if they were already in
  the base unit (``100 m``). Here the wire shape is flattened to
  ``{type, value, unit}`` (consistent with every other built-in's ``{type,
  value}``, and compatible with the shared pipeline's empty-value checks in
  ``validation.py``, which read ``dto_data['value']`` directly) and
  ``normalize_dto`` actually converts ``value`` from ``unit`` to the family's
  base unit via ``constants.convert_to_base`` before validation/storage.
- The legacy ``format_value`` ignored ``unit_m``/``unit_i`` entirely and
  printed ``f"{unitType}: {value}"`` (the base-unit number under the *family*
  name, e.g. ``"length: 100"`` — not even a real unit code). Here it converts
  the stored base value into the configured display unit and appends its
  code (e.g. ``"100 cm"``).
"""

from typing import Any, Dict, List

from stapel_attributes.base import BaseFeatureType, FeatureDef
from stapel_attributes.exceptions import FeatureValidationError
from stapel_attributes.registry import register_feature_type
from stapel_attributes.results import ValidationErrorCode
from stapel_attributes.types.convertible_unit.constants import (
    UNIT_FAMILIES,
    UNIT_TYPE_KEYS,
    convert_from_base,
    convert_to_base,
    units_for_system,
)
from stapel_attributes.types.convertible_unit.config import (
    ConvertibleUnitConfig, ConvertibleUnitConfigSerializer,
)
from stapel_attributes.types.convertible_unit.dto import (
    ConvertibleUnitDto, ConvertibleUnitDtoSerializer,
)
from stapel_attributes.types.convertible_unit.dao import (
    ConvertibleUnitDao, ConvertibleUnitDaoSerializer,
)


def _allowed_units(config: ConvertibleUnitConfig) -> List[str]:
    """Units offered by this config (the metric and/or imperial pick)."""
    return [u for u in (config.unit_m, config.unit_i) if u]


@register_feature_type
class ConvertibleUnitFeatureType(BaseFeatureType[ConvertibleUnitConfig, ConvertibleUnitDto, ConvertibleUnitDao]):
    """
    Convertible-unit feature type handler — a numeric value with a
    user-facing unit that is converted to/from a canonical base unit.

    Config:
        - type: "convertible_unit" (required)
        - unitType: unit family — length | weight | area | volume | temperature (required)
        - unit_m: metric unit code offered to the user (nullable)
        - unit_i: imperial unit code offered to the user (nullable)
        - precision: decimal places, applied to the stored base-unit value (default: 2)
        - prefix: display prefix like "~" (optional)
        - min / max: bounds in the base unit (optional)

    DTO value: ``{value: number, unit: code}`` — the number as entered, in
    ``unit`` (one of ``unit_m``/``unit_i``). Normalized to the base unit
    before validation.

    DAO value: number always in the base unit + metadata (unitType, unit_m,
    unit_i, precision, prefix). Because the DAO value is canonical, a
    range-filter query (e.g. "listings with length between 1m and 2m") never
    needs type-specific fan-out: convert the query bounds to the base unit
    with ``convert_to_base`` (or ``ConvertibleUnitFeatureType.to_base``) once,
    then run a plain numeric ``BETWEEN`` against the stored ``value`` — the
    same way int/float range filters already work.
    """

    slug = 'convertible_unit'
    name = 'Convertible Unit'

    # Dataclass types
    config_class = ConvertibleUnitConfig
    dto_class = ConvertibleUnitDto
    dao_class = ConvertibleUnitDao

    # Serializer classes (auto-generated from dataclasses)
    config_serializer_class = ConvertibleUnitConfigSerializer
    dto_serializer_class = ConvertibleUnitDtoSerializer
    dao_serializer_class = ConvertibleUnitDaoSerializer

    def validate_config(self, config: ConvertibleUnitConfig) -> None:
        """Validate convertible-unit feature configuration."""
        unit_type = config.unitType

        if unit_type is None:
            raise FeatureValidationError(
                "'unitType' is required",
                code=ValidationErrorCode.INVALID_CONFIG,
            )

        if unit_type not in UNIT_FAMILIES:
            raise FeatureValidationError(
                f"Unknown unit type: {unit_type}. Available: {', '.join(sorted(UNIT_FAMILIES))}",
                code=ValidationErrorCode.INVALID_CONFIG,
                ref_value=sorted(UNIT_FAMILIES),
            )

        if config.unit_m is None and config.unit_i is None:
            raise FeatureValidationError(
                "At least one of 'unit_m' or 'unit_i' must be specified",
                code=ValidationErrorCode.INVALID_CONFIG,
            )

        if config.unit_m is not None:
            metric_units = units_for_system(unit_type, 'metric')
            if config.unit_m not in metric_units:
                raise FeatureValidationError(
                    f"Invalid metric unit: {config.unit_m}. Available: {', '.join(metric_units)}",
                    code=ValidationErrorCode.INVALID_CONFIG,
                    ref_value=metric_units,
                )

        if config.unit_i is not None:
            imperial_units = units_for_system(unit_type, 'imperial')
            if config.unit_i not in imperial_units:
                raise FeatureValidationError(
                    f"Invalid imperial unit: {config.unit_i}. Available: {', '.join(imperial_units)}",
                    code=ValidationErrorCode.INVALID_CONFIG,
                    ref_value=imperial_units,
                )

        if config.precision is not None and config.precision < 0:
            raise FeatureValidationError(
                "'precision' must be a non-negative integer",
                code=ValidationErrorCode.INVALID_CONFIG,
            )

        if config.min is not None and config.max is not None and config.min > config.max:
            raise FeatureValidationError(
                "'min' cannot be greater than 'max'",
                code=ValidationErrorCode.MIN_GREATER_THAN_MAX,
            )

    def validate_dto(self, config: ConvertibleUnitConfig, dto: ConvertibleUnitDto) -> None:
        """Validate convertible-unit DTO data against configuration.

        ``dto.value`` is already normalized to the base unit at this point
        (see ``normalize_dto``); ``min``/``max`` are compared as-is.
        """
        value = dto.value if dto.value is not None else 0.0

        if config.min is not None and value < config.min:
            raise FeatureValidationError(
                f"Value in base unit must be >= {config.min}",
                code=ValidationErrorCode.BELOW_MINIMUM,
                ref_value=config.min,
            )

        if config.max is not None and value > config.max:
            raise FeatureValidationError(
                f"Value in base unit must be <= {config.max}",
                code=ValidationErrorCode.ABOVE_MAXIMUM,
                ref_value=config.max,
            )

    def dto_to_dao(
        self,
        config: ConvertibleUnitConfig,
        dto: ConvertibleUnitDto,
        feature: FeatureDef,
    ) -> ConvertibleUnitDao:
        """Convert convertible-unit DTO to DAO with metadata."""
        precision = config.precision if config.precision is not None else 2
        value = round(dto.value if dto.value is not None else 0.0, precision)

        return ConvertibleUnitDao(
            type=self.slug,
            value=value,
            unitType=config.unitType,
            unit_m=config.unit_m,
            unit_i=config.unit_i,
            precision=precision,
            prefix=config.prefix,
            name=feature.name,
            title=feature.show_at_title if feature.show_at_title else None,
            badge=feature.show_as_badge if feature.show_as_badge else None,
            translate=feature.translate if feature.translate != 'all' else None,
        )

    def normalize_dto(self, config: ConvertibleUnitConfig, dto_data: Dict[str, Any]) -> ConvertibleUnitDto:
        """Normalize convertible-unit DTO data: convert ``value`` from the
        submitted ``unit`` into the family's base unit.

        - ``unit`` omitted: ``value`` is taken as already expressed in the
          base unit (headless/back-office callers writing canonical values
          directly — the same contract int/float use for their plain
          ``value``).
        - ``unit`` given: it must be one of the config's ``unit_m``/
          ``unit_i``; ``value`` is converted to the base unit and rounded to
          ``precision``.
        """
        precision = config.precision if config.precision is not None else 2
        raw_value = dto_data.get('value')
        unit = dto_data.get('unit')

        if raw_value is None:
            return ConvertibleUnitDto(type=self.slug, value=0.0, unit=unit)

        try:
            numeric = float(raw_value)
        except (TypeError, ValueError):
            raise FeatureValidationError(
                f"Value must be a number, got: {type(raw_value).__name__}",
                code=ValidationErrorCode.INVALID_TYPE,
            )

        if unit is None:
            base_value = numeric
        else:
            allowed = _allowed_units(config)
            if unit not in allowed:
                raise FeatureValidationError(
                    f"Unknown unit '{unit}' for '{config.unitType}'. Available: {', '.join(allowed)}",
                    code=ValidationErrorCode.NOT_IN_OPTIONS,
                    ref_value=allowed,
                )
            base_value = convert_to_base(numeric, unit, config.unitType)

        return ConvertibleUnitDto(
            type=self.slug,
            value=round(base_value, precision),
            unit=unit,
        )

    def get_default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            'type': self.slug,
            'unitType': 'length',
            'unit_m': 'cm',
            'unit_i': 'in',
            'precision': 2,
        }

    def format_value(self, config: ConvertibleUnitConfig, dao: ConvertibleUnitDao) -> str:
        """Format the stored base-unit value for display in the configured
        unit (``unit_m`` if set, else ``unit_i``), appending the unit code.
        """
        value = dao.value
        if value is None:
            return ''

        precision = config.precision if config.precision is not None else 2
        display_unit = config.unit_m or config.unit_i

        display_value = (
            convert_from_base(value, display_unit, config.unitType)
            if display_unit and config.unitType else value
        )

        formatted = f"{display_value:.{precision}f}".rstrip('0').rstrip('.')
        if config.prefix:
            formatted = f"{config.prefix} {formatted}"
        if display_unit:
            formatted = f"{formatted} {display_unit}"
        return formatted

    def get_translation_keys(self, config: ConvertibleUnitConfig) -> List[str]:
        """Return translation keys used by this feature."""
        keys: List[str] = []
        if config.unitType and config.unitType in UNIT_TYPE_KEYS:
            keys.append(UNIT_TYPE_KEYS[config.unitType])
        for unit_code in _allowed_units(config):
            keys.append(f'feature.unit.{unit_code}.name')
        return keys

    @staticmethod
    def to_base(value: float, unit: str, unit_type: str) -> float:
        """Convenience wrapper over ``constants.convert_to_base`` for
        consumers building a range-filter query — convert a UI-entered bound
        (e.g. a search box in 'km') into the base unit the DAO ``value`` is
        stored in, once, before running a plain numeric range comparison.
        """
        return convert_to_base(value, unit, unit_type)

    @staticmethod
    def from_base(base_value: float, unit: str, unit_type: str) -> float:
        """Convenience wrapper over ``constants.convert_from_base``."""
        return convert_from_base(base_value, unit, unit_type)
