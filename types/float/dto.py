"""Float Feature Type - DTO (Data Transfer Object)."""

from dataclasses import dataclass
from typing import Literal

from stapel_attributes.base import DictDataclassSerializer


@dataclass
class FloatDto:
    """DTO for float feature value input."""
    type: Literal['float'] = 'float'
    value: float = 0.0


class FloatDtoSerializer(DictDataclassSerializer):
    """Serializer for float feature DTO."""
    class Meta:
        dataclass = FloatDto
