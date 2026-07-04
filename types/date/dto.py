"""Date Feature Type - DTO (Data Transfer Object)."""

from dataclasses import dataclass
from typing import Literal, Optional

from stapel_attributes.base import DictDataclassSerializer


@dataclass
class DateDto:
    """DTO for date feature value input."""
    type: Literal['date'] = 'date'
    value: Optional[int] = None  # Unix timestamp


class DateDtoSerializer(DictDataclassSerializer):
    """Serializer for date feature DTO."""
    class Meta:
        dataclass = DateDto
