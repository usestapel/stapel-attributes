"""Group (composite) Feature Type - DAO (Data Access Object)."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal

from stapel_attributes.base import DaoMeta, DictDataclassSerializer


@dataclass
class GroupDao(DaoMeta):
    """DAO for a stored composite value.

    ``value`` is a list of rows; each row is an object keyed by child slug
    whose cells are the children's own DAOs — carrying the child's
    :class:`~stapel_attributes.base.DaoMeta` (``name``, ``order``, ``title``,
    ``badge``, ``translate``), so a stored row renders without the schema.

    Example::

        {"type": "group", "name": "Discount ladder", "value": [
            {"quantity": {"type": "int", "value": 5, "name": "Quantity", "order": 0},
             "discount": {"type": "int", "value": 10, "name": "Discount", "order": 1}}
        ]}
    """
    type: Literal['group'] = 'group'
    value: List[Dict[str, Any]] = field(default_factory=list)


class GroupDaoSerializer(DictDataclassSerializer):
    """Serializer for group feature DAO."""
    class Meta:
        dataclass = GroupDao
