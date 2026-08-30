"""Ref Hierarchical Select Feature Type - Configuration."""

from dataclasses import dataclass, field
from typing import List, Literal, Optional

from stapel_attributes.base import DictDataclassSerializer


@dataclass
class RefHierarchicalSelectConfig:
    """Configuration for the ref_hierarchical_select feature type.

    ``levels`` is the root-to-leaf chain walked by the editor; each level
    after the first must declare the previous one as its ``parent`` in the
    vocabulary.
    """
    type: Literal['ref_hierarchical_select'] = 'ref_hierarchical_select'
    vocabulary: Optional[str] = None
    levels: List[str] = field(default_factory=list)
    minDepth: int = 1
    maxDepth: Optional[int] = None


class RefHierarchicalSelectConfigSerializer(DictDataclassSerializer):
    """Serializer for the ref_hierarchical_select feature configuration."""
    class Meta:
        dataclass = RefHierarchicalSelectConfig
        extra_kwargs = {
            'vocabulary': {'allow_blank': True, 'allow_null': True, 'required': False},
        }
