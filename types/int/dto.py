"""Integer Feature Type - DTO (Data Transfer Object)."""

from dataclasses import dataclass
from typing import Literal

from stapel_attributes.base import DictDataclassSerializer


@dataclass
class IntDto:
    """DTO for integer feature value input."""
    type: Literal['int'] = 'int'
    value: int = 0


class IntDtoSerializer(DictDataclassSerializer):
    """Serializer for integer feature DTO."""
    class Meta:
        dataclass = IntDto
