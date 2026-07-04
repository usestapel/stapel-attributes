"""Date Feature Type - DAO (Data Access Object)."""

from dataclasses import dataclass
from typing import Literal, Optional

from stapel_attributes.base import DaoMeta, DictDataclassSerializer


@dataclass
class DateDao(DaoMeta):
    """DAO for date feature stored value."""
    type: Literal['date'] = 'date'
    value: Optional[int] = None  # Unix timestamp


class DateDaoSerializer(DictDataclassSerializer):
    """Serializer for date feature DAO."""
    class Meta:
        dataclass = DateDao
