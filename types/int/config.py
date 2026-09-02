"""Integer Feature Type - Configuration."""

from dataclasses import dataclass
from typing import Literal, Optional, List

from stapel_attributes.base import DictDataclassSerializer
from stapel_attributes.types.ref_select.config import OptionsRef


@dataclass
class IntConfig:
    """Configuration for integer feature type.

    ``optionsRef`` makes the allowed set vocabulary-backed, exactly as on the
    ref-types: the value must be a term of ``level`` (codes are the decimal
    digits of the integer), and with ``parentFeature`` filled, a child of the
    selected parent term. The value itself stays an ``int`` on the wire and
    in the DAO — only membership reads the vocabulary. ``min``/``max`` keep
    applying as coarse static bounds (and remain the target a ``limit`` rule
    replaces).
    """
    type: Literal['int'] = 'int'
    min: Optional[int] = None
    max: Optional[int] = None
    options: Optional[List[int]] = None
    allowCustom: bool = True
    prefix: Optional[str] = None
    postfix: Optional[str] = None
    postfix1000: Optional[str] = None
    placeholder: Optional[str] = None
    precision: int = 1
    optionsRef: Optional[OptionsRef] = None


class IntConfigSerializer(DictDataclassSerializer):
    """Serializer for integer feature configuration."""
    class Meta:
        dataclass = IntConfig
        extra_kwargs = {
            'optionsRef': {
                'required': False,
                'allow_null': True,
                'extra_kwargs': {
                    'parentFeature': {'allow_blank': True, 'allow_null': True, 'required': False},
                },
            },
        }
