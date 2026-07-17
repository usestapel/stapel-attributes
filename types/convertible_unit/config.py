"""Convertible Unit Feature Type - Configuration."""

from dataclasses import dataclass
from typing import Literal, Optional

from stapel_attributes.base import DictDataclassSerializer


@dataclass
class ConvertibleUnitConfig:
    """Configuration for the convertible-unit feature type.

    ``unitType`` selects a shipped unit family (a key of
    ``constants.UNIT_FAMILIES``: ``length``, ``weight``, ``area``,
    ``volume``, ``temperature``). ``unit_m``/``unit_i`` pick which metric /
    imperial unit of that family the user is offered (at least one of the
    two is required); both stay available so a listing can be entered in
    either system.

    Values are always stored and range-checked in the family's canonical
    **base unit** (``UNIT_FAMILIES[unitType]['base_unit']``) — ``min``/``max``
    here are expressed in that base unit, not in ``unit_m``/``unit_i``.
    """
    type: Literal['convertible_unit'] = 'convertible_unit'
    unitType: Optional[str] = None
    unit_m: Optional[str] = None
    unit_i: Optional[str] = None
    precision: int = 2
    prefix: Optional[str] = None
    min: Optional[float] = None
    max: Optional[float] = None


class ConvertibleUnitConfigSerializer(DictDataclassSerializer):
    """Serializer for convertible-unit feature configuration."""
    class Meta:
        dataclass = ConvertibleUnitConfig
