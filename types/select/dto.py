"""Select Feature Type - DTO (Data Transfer Object)."""

from dataclasses import dataclass, field
from typing import Literal, List

from stapel_attributes.base import DictDataclassSerializer


@dataclass
class SelectDto:
    """DTO for select feature value input."""
    type: Literal['select'] = 'select'
    value: List[str] = field(default_factory=list)


class SelectDtoSerializer(DictDataclassSerializer):
    """Serializer for select feature DTO."""
    class Meta:
        dataclass = SelectDto
