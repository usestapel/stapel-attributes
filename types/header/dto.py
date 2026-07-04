"""Header Feature Type - DTO (Data Transfer Object)."""

from dataclasses import dataclass
from typing import Literal, Optional

from stapel_attributes.base import DictDataclassSerializer


@dataclass
class HeaderDto:
    """DTO for header feature (no value needed)."""
    type: Literal['header'] = 'header'
    value: Optional[str] = None


class HeaderDtoSerializer(DictDataclassSerializer):
    """Serializer for header feature DTO."""
    class Meta:
        dataclass = HeaderDto
