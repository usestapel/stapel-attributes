"""String Feature Type - DTO (Data Transfer Object)."""

from dataclasses import dataclass
from typing import Literal

from stapel_attributes.base import DictDataclassSerializer


@dataclass
class StringDto:
    """DTO for string feature value input."""
    type: Literal['string'] = 'string'
    value: str = ''


class StringDtoSerializer(DictDataclassSerializer):
    """Serializer for string feature DTO."""
    class Meta:
        dataclass = StringDto
