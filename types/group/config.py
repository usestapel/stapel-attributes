"""Group (composite) Feature Type - Configuration."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional

from stapel_attributes.base import DictDataclassSerializer


@dataclass
class GroupRepeat:
    """Row-count bounds of a repeatable group.

    ``max=None`` means unbounded. A group whose ``repeat`` is ``None`` is not
    repeatable at all: it holds exactly one row.
    """
    min: int = 0
    max: Optional[int] = None


@dataclass
class GroupConfig:
    """Configuration for the composite (``group``) feature type.

    ``fields`` holds full feature definitions — the same shape as a top-level
    :class:`~stapel_attributes.base.FeatureDef` dict — of any *other*
    registered type. Nesting depth is 1: a group cannot contain a group, and
    the check is in :meth:`GroupFeatureType.validate_config`, not a convention.
    """
    type: Literal['group'] = 'group'
    fields: List[Dict[str, Any]] = field(default_factory=list)
    repeat: Optional[GroupRepeat] = None


class GroupRepeatSerializer(DictDataclassSerializer):
    """Serializer for the repeat bounds."""
    class Meta:
        dataclass = GroupRepeat


class GroupConfigSerializer(DictDataclassSerializer):
    """Serializer for group feature configuration.

    ``fields`` passes through as raw dicts on purpose: each child carries its
    own ``config`` discriminated by ``type``, parsed by that type's own strict
    serializer when the group validates its children.
    """
    class Meta:
        dataclass = GroupConfig
        extra_kwargs = {
            'repeat': {'required': False, 'allow_null': True},
        }
