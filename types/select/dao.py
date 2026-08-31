"""Select Feature Type - DAO (Data Access Object)."""

from dataclasses import dataclass, field
from typing import Literal, Optional, List

from stapel_attributes.base import DaoMeta, DictDataclassSerializer


@dataclass
class SelectDao(DaoMeta):
    """DAO for select feature stored value.

    ``value`` holds the option values (the filter/search axis — facets and
    queries read these and nothing else); ``labels`` is the display snapshot
    taken at write time, positionally aligned with ``value``, so a reader
    renders a stored listing without ever fetching the category config.
    """
    type: Literal['select'] = 'select'
    value: List[str] = field(default_factory=list)
    labels: List[str] = field(default_factory=list)
    uiStyle: Optional[Literal['dropdown', 'checkboxes', 'chips']] = None
    maxSelected: Optional[int] = None  # None = unlimited; 1 = single select


class SelectDaoSerializer(DictDataclassSerializer):
    """Serializer for select feature DAO."""
    class Meta:
        dataclass = SelectDao
