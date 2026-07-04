"""Hex Color Feature Type - Configuration."""

from dataclasses import dataclass, field
from typing import Literal, Optional, List

from stapel_attributes.base import DictDataclassSerializer


@dataclass
class HexColorOption:
    """Option for hex color feature type."""
    simple: str  # Simple color category (required)
    hex: Optional[str] = None  # #RGB or #RRGGBB
    label: Optional[str] = None  # Translation key


@dataclass
class HexColorConfig:
    """Configuration for hex color feature type."""
    type: Literal['hex_color'] = 'hex_color'
    options: List[HexColorOption] = field(default_factory=list)
    allowCustom: bool = False


class HexColorOptionSerializer(DictDataclassSerializer):
    """Serializer for hex color option."""
    class Meta:
        dataclass = HexColorOption
        extra_kwargs = {
            'hex': {'allow_blank': True},
            'label': {'allow_blank': True},
        }


class HexColorConfigSerializer(DictDataclassSerializer):
    """Serializer for hex color feature configuration."""
    class Meta:
        dataclass = HexColorConfig
        extra_kwargs = {
            'options': {
                'child_kwargs': {
                    'extra_kwargs': {
                        'hex': {'allow_blank': True},
                        'label': {'allow_blank': True},
                    }
                }
            }
        }
