"""Integer Feature Type - DAO (Data Access Object)."""

from dataclasses import dataclass
from typing import Literal, Optional

from stapel_attributes.base import DaoMeta, DictDataclassSerializer


@dataclass
class IntDao(DaoMeta):
    """DAO for integer feature stored value."""
    type: Literal['int'] = 'int'
    value: int = 0
    prefix: Optional[str] = None
    postfix: Optional[str] = None
    postfix1000: Optional[str] = None
    precision: Optional[int] = None


class IntDaoSerializer(DictDataclassSerializer):
    """Serializer for integer feature DAO."""
    class Meta:
        dataclass = IntDao
