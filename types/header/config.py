"""Header Feature Type - Configuration."""

from dataclasses import dataclass
from typing import Literal

from stapel_attributes.base import DictDataclassSerializer


@dataclass
class HeaderConfig:
    """Configuration for header feature type."""
    type: Literal['header'] = 'header'
    style: Literal['l', 'm'] = 'l'


class HeaderConfigSerializer(DictDataclassSerializer):
    """Serializer for header feature configuration."""
    class Meta:
        dataclass = HeaderConfig
