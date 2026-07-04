"""Boolean Feature Type - DAO (Data Access Object)."""

from dataclasses import dataclass
from typing import Literal, Optional

from stapel_attributes.base import DaoMeta, DictDataclassSerializer


@dataclass
class BoolDao(DaoMeta):
    """DAO for boolean feature stored value."""
    type: Literal['bool'] = 'bool'
    value: bool = False
    trueLabel: Optional[str] = None
    falseLabel: Optional[str] = None


class BoolDaoSerializer(DictDataclassSerializer):
    """Serializer for boolean feature DAO."""
    class Meta:
        dataclass = BoolDao
