"""Group (composite) Feature Type - DTO (Data Transfer Object)."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal

from stapel_attributes.base import DictDataclassSerializer


@dataclass
class GroupDto:
    """DTO for a composite feature value.

    ``value`` is a list of rows; each row is an object keyed by child slug,
    holding that child's own DTO (``{"type": ..., "value": ...}``) or a bare
    value. A non-repeatable group (``repeat: null``) carries a single row.

    Example::

        {"type": "group", "value": [{"quantity": 5, "discount": 10}]}
    """
    type: Literal['group'] = 'group'
    value: List[Dict[str, Any]] = field(default_factory=list)


class GroupDtoSerializer(DictDataclassSerializer):
    """Serializer for group feature DTO."""
    class Meta:
        dataclass = GroupDto
