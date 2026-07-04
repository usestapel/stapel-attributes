"""Date Feature Type - Configuration."""

from dataclasses import dataclass, field
from typing import Literal, Optional, List

from stapel_attributes.base import DictDataclassSerializer


@dataclass
class DateConfig:
    """Configuration for date feature type."""
    type: Literal['date'] = 'date'
    precision: Literal['year', 'month', 'date', 'datetime'] = 'date'
    minDate: Optional[int] = None  # Unix timestamp
    maxDate: Optional[int] = None  # Unix timestamp
    allowFuture: bool = True
    allowPast: bool = True
    default: Optional[int] = None  # Unix timestamp
    options: List[int] = field(default_factory=list)
    lockInput: bool = False
    placeholder: Optional[str] = None


class DateConfigSerializer(DictDataclassSerializer):
    """Serializer for date feature configuration."""
    class Meta:
        dataclass = DateConfig
