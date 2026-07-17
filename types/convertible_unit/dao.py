"""Convertible Unit Feature Type - DAO (Data Access Object)."""

from dataclasses import dataclass
from typing import Literal, Optional

from stapel_attributes.base import DaoMeta, DictDataclassSerializer


@dataclass
class ConvertibleUnitDao(DaoMeta):
    """DAO for convertible-unit feature stored value.

    ``value`` is always in the family's canonical base unit
    (``UNIT_FAMILIES[unitType]['base_unit']``) — never in ``unit_m``/
    ``unit_i``. Display/formatting and range-filter bounds convert on the way
    in/out via ``constants.convert_to_base``/``convert_from_base``; storage
    and comparisons on ``value`` itself are always plain base-unit numbers.
    """
    type: Literal['convertible_unit'] = 'convertible_unit'
    value: float = 0.0
    unitType: Optional[str] = None
    unit_m: Optional[str] = None
    unit_i: Optional[str] = None
    precision: Optional[int] = None
    prefix: Optional[str] = None


class ConvertibleUnitDaoSerializer(DictDataclassSerializer):
    """Serializer for convertible-unit feature DAO."""
    class Meta:
        dataclass = ConvertibleUnitDao
