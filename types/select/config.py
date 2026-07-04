"""Select Feature Type - Configuration."""

from dataclasses import dataclass
from typing import Literal, Optional, List

from stapel_attributes.base import DictDataclassSerializer


@dataclass
class SelectOption:
    """Option for select feature type."""
    value: str
    label: str  # Translation key
    icon: Optional[str] = None
    default: bool = False


@dataclass
class SelectConfig:
    """Configuration for select feature type."""
    type: Literal['select'] = 'select'
    options: List[SelectOption] = None  # type: ignore
    uiStyle: Literal['dropdown', 'checkboxes', 'chips'] = 'dropdown'
    minSelected: int = 0
    maxSelected: Optional[int] = None  # None = unlimited; 1 = single select
    lockUserInput: bool = False
    translatable_options: bool = True  # If True, option labels are translation keys


class SelectOptionSerializer(DictDataclassSerializer):
    """Serializer for select option."""
    class Meta:
        dataclass = SelectOption
        extra_kwargs = {
            'icon': {'allow_blank': True},
        }


class SelectConfigSerializer(DictDataclassSerializer):
    """Serializer for select feature configuration."""
    class Meta:
        dataclass = SelectConfig
        extra_kwargs = {
            'options': {
                'child_kwargs': {
                    'extra_kwargs': {
                        'icon': {'allow_blank': True},
                    }
                }
            }
        }
