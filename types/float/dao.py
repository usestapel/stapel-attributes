"""Float Feature Type - DAO (Data Access Object)."""

from dataclasses import dataclass
from typing import Literal, Optional

from stapel_attributes.base import DaoMeta, DictDataclassSerializer


@dataclass
class FloatDao(DaoMeta):
    """DAO for float feature stored value."""
    type: Literal['float'] = 'float'
    value: float = 0.0
    prefix: Optional[str] = None
    postfix: Optional[str] = None
    postfix1000: Optional[str] = None
    precision: Optional[int] = None


class FloatDaoSerializer(DictDataclassSerializer):
    """Serializer for float feature DAO."""
    class Meta:
        dataclass = FloatDao
