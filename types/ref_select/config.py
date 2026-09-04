"""Ref Select Feature Type - Configuration."""

from dataclasses import dataclass
from typing import Literal, Optional

from stapel_attributes.base import DictDataclassSerializer


@dataclass
class OptionsRef:
    """Pointer to one level of an external vocabulary.

    ``parentFeature`` is the slug of a sibling feature holding the parent
    term's code; when it carries a value, this feature's codes are restricted
    to that parent's children.
    """
    vocabulary: str = ''
    level: str = ''
    parentFeature: Optional[str] = None


@dataclass
class RefSelectConfig:
    """Configuration for the ref_select feature type.

    ``prefix``/``postfix`` are the display affixes ``int``/``float`` carry,
    with the same semantics and the same translation convention: they are
    translation keys, they are snapshotted into the DAO at write time, and
    ``format_value`` wraps the rendered labels in them. A vocabulary-backed
    select whose terms are numbers needs a unit as much as an integer does:
    without one a stored floor prints as a bare "3".
    """
    type: Literal['ref_select'] = 'ref_select'
    optionsRef: Optional[OptionsRef] = None
    minSelected: int = 0
    maxSelected: Optional[int] = 1
    uiStyle: Literal['dropdown', 'chips'] = 'dropdown'
    prefix: Optional[str] = None
    postfix: Optional[str] = None


class OptionsRefSerializer(DictDataclassSerializer):
    """Serializer for the vocabulary pointer."""
    class Meta:
        dataclass = OptionsRef
        extra_kwargs = {
            'parentFeature': {'allow_blank': True, 'allow_null': True, 'required': False},
        }


class RefSelectConfigSerializer(DictDataclassSerializer):
    """Serializer for the ref_select feature configuration."""
    class Meta:
        dataclass = RefSelectConfig
        extra_kwargs = {
            'optionsRef': {
                'required': False,
                'allow_null': True,
                'extra_kwargs': {
                    'parentFeature': {'allow_blank': True, 'allow_null': True, 'required': False},
                },
            },
        }
