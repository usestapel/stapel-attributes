"""Integer Feature Type - Configuration."""

from dataclasses import dataclass
from typing import Literal, Optional, List

from stapel_attributes.base import DictDataclassSerializer


@dataclass
class IntConfig:
    """Configuration for integer feature type."""
    type: Literal['int'] = 'int'
    min: Optional[int] = None
    max: Optional[int] = None
    options: Optional[List[int]] = None
    allowCustom: bool = True
    prefix: Optional[str] = None
    postfix: Optional[str] = None
    postfix1000: Optional[str] = None
    placeholder: Optional[str] = None
    precision: int = 1


class IntConfigSerializer(DictDataclassSerializer):
    """Serializer for integer feature configuration."""
    class Meta:
        dataclass = IntConfig
