"""Hierarchical Select Feature Type - DAO (Data Access Object)."""

from dataclasses import dataclass, field
from typing import Literal, List

from stapel_attributes.base import DaoMeta, DictDataclassSerializer


@dataclass
class HierarchicalSelectDao(DaoMeta):
    """DAO for hierarchical select feature stored value.

    Stores the selection path as ordered array of values from root to leaf.
    Example: ['electronics', 'phones', 'smartphones'] for a 3-level selection.
    """
    type: Literal['hierarchical_select'] = 'hierarchical_select'
    value: List[str] = field(default_factory=list)


class HierarchicalSelectDaoSerializer(DictDataclassSerializer):
    """Serializer for hierarchical select feature DAO."""
    class Meta:
        dataclass = HierarchicalSelectDao
