"""Float Feature Type - Configuration."""

from dataclasses import dataclass
from typing import Literal, Optional, List

from stapel_attributes.base import DictDataclassSerializer


@dataclass
class FloatConfig:
    """Configuration for float feature type."""
    type: Literal['float'] = 'float'
    min: Optional[float] = None
    max: Optional[float] = None
    precision: int = 2
    options: Optional[List[float]] = None
    allowCustom: bool = True
    prefix: Optional[str] = None
    postfix: Optional[str] = None
    postfix1000: Optional[str] = None
    placeholder: Optional[str] = None


class FloatConfigSerializer(DictDataclassSerializer):
    """Serializer for float feature configuration."""
    class Meta:
        dataclass = FloatConfig
