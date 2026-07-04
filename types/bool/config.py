"""Boolean Feature Type - Configuration."""

from dataclasses import dataclass
from typing import Literal, Optional

from stapel_attributes.base import DictDataclassSerializer


@dataclass
class BoolConfig:
    """Configuration for boolean feature type."""
    type: Literal['bool'] = 'bool'
    trueLabel: Optional[str] = None
    falseLabel: Optional[str] = None


class BoolConfigSerializer(DictDataclassSerializer):
    """Serializer for boolean feature configuration."""
    class Meta:
        dataclass = BoolConfig
