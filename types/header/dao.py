"""Header Feature Type - DAO (Data Access Object)."""

from dataclasses import dataclass
from typing import Literal

from stapel_attributes.base import DaoMeta, DictDataclassSerializer


@dataclass
class HeaderDao(DaoMeta):
    """DAO for header feature stored value."""
    type: Literal['header'] = 'header'
    style: Literal['l', 'm'] = 'l'


class HeaderDaoSerializer(DictDataclassSerializer):
    """Serializer for header feature DAO."""
    class Meta:
        dataclass = HeaderDao
