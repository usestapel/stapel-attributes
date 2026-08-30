"""Ref Hierarchical Select Feature Type - DTO (Data Transfer Object)."""

from dataclasses import dataclass, field
from typing import List, Literal

from stapel_attributes.base import DictDataclassSerializer


@dataclass
class RefHierarchicalSelectDto:
    """DTO for a ref_hierarchical_select value: term codes along ``levels``."""
    type: Literal['ref_hierarchical_select'] = 'ref_hierarchical_select'
    value: List[str] = field(default_factory=list)


class RefHierarchicalSelectDtoSerializer(DictDataclassSerializer):
    """Serializer for the ref_hierarchical_select feature DTO."""
    class Meta:
        dataclass = RefHierarchicalSelectDto
