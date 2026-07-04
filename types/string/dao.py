"""String Feature Type - DAO (Data Access Object)."""

from dataclasses import dataclass
from typing import Literal, Optional

from stapel_attributes.base import DaoMeta, DictDataclassSerializer


@dataclass
class StringDao(DaoMeta):
    """DAO for string feature stored value."""
    type: Literal['string'] = 'string'
    value: str = ''
    prefix: Optional[str] = None
    postfix: Optional[str] = None


class StringDaoSerializer(DictDataclassSerializer):
    """Serializer for string feature DAO."""
    class Meta:
        dataclass = StringDao
