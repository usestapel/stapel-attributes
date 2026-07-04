"""Hex Color Feature Type - DTO (Data Transfer Object)."""

from dataclasses import dataclass
from typing import Literal, Optional

from stapel_attributes.base import DictDataclassSerializer


@dataclass
class HexColorValue:
    """Value for hex color feature."""
    simple: str  # Simple color category (required)
    hex: Optional[str] = None  # #RGB or #RRGGBB
    label: Optional[str] = None  # Translation key


@dataclass
class HexColorDto:
    """DTO for hex color feature value input."""
    type: Literal['hex_color'] = 'hex_color'
    value: Optional[HexColorValue] = None


class HexColorValueSerializer(DictDataclassSerializer):
    """Serializer for hex color value."""
    class Meta:
        dataclass = HexColorValue
        extra_kwargs = {
            'hex': {'allow_blank': True},
            'label': {'allow_blank': True},
        }


class HexColorDtoSerializer(DictDataclassSerializer):
    """Serializer for hex color feature DTO."""
    value = HexColorValueSerializer(required=False, allow_null=True)

    class Meta:
        dataclass = HexColorDto
