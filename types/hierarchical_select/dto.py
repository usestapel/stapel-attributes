"""Hierarchical Select Feature Type - DTO (Data Transfer Object)."""

from dataclasses import dataclass, field
from typing import Literal, List

from stapel_attributes.base import DictDataclassSerializer


@dataclass
class HierarchicalSelectDto:
    """DTO for hierarchical select feature value input.

    Accepts the selection path as ordered array of values from root to leaf.
    Example: ['electronics', 'phones', 'smartphones'] for a 3-level selection.
    """
    type: Literal['hierarchical_select'] = 'hierarchical_select'
    value: List[str] = field(default_factory=list)


class HierarchicalSelectDtoSerializer(DictDataclassSerializer):
    """Serializer for hierarchical select feature DTO."""
    class Meta:
        dataclass = HierarchicalSelectDto
