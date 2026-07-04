"""Boolean Feature Type - DTO (Data Transfer Object)."""

from dataclasses import dataclass
from typing import Literal

from stapel_attributes.base import DictDataclassSerializer


@dataclass
class BoolDto:
    """DTO for boolean feature value input."""
    type: Literal['bool'] = 'bool'
    value: bool = False


class BoolDtoSerializer(DictDataclassSerializer):
    """Serializer for boolean feature DTO."""
    class Meta:
        dataclass = BoolDto
