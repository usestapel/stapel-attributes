"""Hex Color Feature Type - DAO (Data Access Object)."""

from dataclasses import dataclass
from typing import Literal, Optional

from stapel_attributes.base import DaoMeta, DictDataclassSerializer


@dataclass
class HexColorDao(DaoMeta):
    """DAO for hex color feature stored value."""
    type: Literal['hex_color'] = 'hex_color'
    simple: str = ''  # Simple color category
    hex: Optional[str] = None  # #RRGGBB normalized
    label: Optional[str] = None  # Translation key


class HexColorDaoSerializer(DictDataclassSerializer):
    """Serializer for hex color feature DAO."""
    class Meta:
        dataclass = HexColorDao
        extra_kwargs = {
            'simple': {'allow_blank': True},
            'hex': {'allow_blank': True},
            'label': {'allow_blank': True},
        }
