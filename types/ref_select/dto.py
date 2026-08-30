"""Ref Select Feature Type - DTO (Data Transfer Object)."""

from dataclasses import dataclass, field
from typing import Literal, List

from stapel_attributes.base import DictDataclassSerializer


@dataclass
class RefSelectDto:
    """DTO for a ref_select value: the selected term codes."""
    type: Literal['ref_select'] = 'ref_select'
    value: List[str] = field(default_factory=list)


class RefSelectDtoSerializer(DictDataclassSerializer):
    """Serializer for the ref_select feature DTO."""
    class Meta:
        dataclass = RefSelectDto
