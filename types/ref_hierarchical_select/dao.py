"""Ref Hierarchical Select Feature Type - DAO (Data Access Object)."""

from dataclasses import dataclass, field
from typing import List, Literal, Optional

from stapel_attributes.base import DaoMeta, DictDataclassSerializer


@dataclass
class RefHierarchicalSelectDao(DaoMeta):
    """Stored ref_hierarchical_select value: the code path plus its labels."""
    type: Literal['ref_hierarchical_select'] = 'ref_hierarchical_select'
    value: List[str] = field(default_factory=list)
    labels: List[str] = field(default_factory=list)
    vocabulary: Optional[str] = None
    levels: List[str] = field(default_factory=list)


class RefHierarchicalSelectDaoSerializer(DictDataclassSerializer):
    """Serializer for the ref_hierarchical_select feature DAO."""
    class Meta:
        dataclass = RefHierarchicalSelectDao
