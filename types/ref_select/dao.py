"""Ref Select Feature Type - DAO (Data Access Object)."""

from dataclasses import dataclass, field
from typing import Literal, List, Optional

from stapel_attributes.base import DaoMeta, DictDataclassSerializer


@dataclass
class RefSelectDao(DaoMeta):
    """Stored ref_select value.

    ``value`` holds the term codes (what facets and search read); ``labels``
    is the display snapshot resolved at write time, so rendering a stored
    listing never needs the vocabulary. ``prefix``/``postfix`` are the config's
    display affixes, snapshotted the same way and for the same reason
    ``int``/``float`` snapshot theirs — a renderer holding only the DAO can
    print the unit.
    """
    type: Literal['ref_select'] = 'ref_select'
    value: List[str] = field(default_factory=list)
    labels: List[str] = field(default_factory=list)
    vocabulary: Optional[str] = None
    level: Optional[str] = None
    prefix: Optional[str] = None
    postfix: Optional[str] = None


class RefSelectDaoSerializer(DictDataclassSerializer):
    """Serializer for the ref_select feature DAO."""
    class Meta:
        dataclass = RefSelectDao
