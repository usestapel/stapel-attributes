"""Convertible Unit Feature Type - DTO (Data Transfer Object)."""

from dataclasses import dataclass
from typing import Literal, Optional

from stapel_attributes.base import DictDataclassSerializer


@dataclass
class ConvertibleUnitDto:
    """DTO for convertible-unit feature value input.

    Raw wire shape: ``{type: 'convertible_unit', value: <number>, unit:
    <code>}`` — the number as the user entered it, tagged with which unit
    (one of the config's ``unit_m``/``unit_i``) it is expressed in.

    ``ConvertibleUnitFeatureType.normalize_dto`` converts ``value`` to the
    family's base unit *before* this dataclass is built for validation, so by
    the time ``validate_dto``/``dto_to_dao`` see it, ``value`` is already in
    the base unit. ``unit`` is kept only for that conversion step (and for
    round-tripping which unit the submission used); it plays no further role
    once normalized.
    """
    type: Literal['convertible_unit'] = 'convertible_unit'
    value: Optional[float] = None
    unit: Optional[str] = None


class ConvertibleUnitDtoSerializer(DictDataclassSerializer):
    """Serializer for convertible-unit feature DTO."""
    class Meta:
        dataclass = ConvertibleUnitDto
