"""String Feature Type - Configuration."""

from dataclasses import dataclass
from typing import Literal, Optional, List

from stapel_attributes.base import DictDataclassSerializer


@dataclass
class StringConfig:
    """Configuration for string feature type."""
    type: Literal['string'] = 'string'
    minLength: Optional[int] = None
    maxLength: Optional[int] = None
    pattern: Optional[str] = None
    options: Optional[List[str]] = None
    allowCustom: bool = True
    prefix: Optional[str] = None
    postfix: Optional[str] = None
    placeholder: Optional[str] = None
    translatable_options: bool = True  # If True, option values are translation keys


class StringConfigSerializer(DictDataclassSerializer):
    """Serializer for string feature configuration."""
    class Meta:
        dataclass = StringConfig
