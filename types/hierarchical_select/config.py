"""Hierarchical Select Feature Type - Configuration."""

from dataclasses import dataclass, field
from typing import Literal, Optional, List

from stapel_attributes.base import DictDataclassSerializer


@dataclass
class HierarchicalOption:
    """Recursive option in hierarchical select. Can contain nested children."""
    value: str
    label: Optional[str] = None  # Translation key (optional, defaults to value)
    icon: Optional[str] = None
    childrenTitle: Optional[str] = None  # Translation key for children picker title
    children: List['HierarchicalOption'] = field(default_factory=list)


@dataclass
class HierarchicalSelectConfig:
    """Configuration for hierarchical select feature type.

    Supports recursive tree structure where each option can have nested children.
    User navigates through the tree and selected path is stored as array of values.
    """
    type: Literal['hierarchical_select'] = 'hierarchical_select'
    options: List[HierarchicalOption] = field(default_factory=list)
    required: bool = True
    minDepth: int = 1  # Minimum selection depth required
    maxDepth: Optional[int] = None  # Maximum depth allowed (None = unlimited)
    translatable_options: bool = True  # If True, option labels are translation keys


class HierarchicalOptionSerializer(DictDataclassSerializer):
    """Serializer for hierarchical option."""
    class Meta:
        dataclass = HierarchicalOption
        extra_kwargs = {
            'label': {'allow_blank': True, 'allow_null': True, 'required': False},
            'icon': {'allow_blank': True},
            'childrenTitle': {'allow_blank': True},
        }


class HierarchicalSelectConfigSerializer(DictDataclassSerializer):
    """Serializer for hierarchical select feature configuration."""
    class Meta:
        dataclass = HierarchicalSelectConfig
        extra_kwargs = {
            'options': {
                'child_kwargs': {
                    'extra_kwargs': {
                        'label': {'allow_blank': True, 'allow_null': True, 'required': False},
                        'icon': {'allow_blank': True},
                        'childrenTitle': {'allow_blank': True},
                    }
                }
            }
        }
