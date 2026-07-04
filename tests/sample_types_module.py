"""A module-style EXTRA_TYPES entry: importing it registers a type.

Used by the registry tests to prove the module-path flavor of
``STAPEL_ATTRIBUTES["EXTRA_TYPES"]``.
"""

from dataclasses import dataclass
from typing import Literal, Optional

from stapel_attributes.base import BaseFeatureType, DaoMeta, DictDataclassSerializer, FeatureDef
from stapel_attributes.registry import register_feature_type


@dataclass
class StickerConfig:
    type: Literal['sticker'] = 'sticker'


class StickerConfigSerializer(DictDataclassSerializer):
    class Meta:
        dataclass = StickerConfig


@dataclass
class StickerDto:
    type: Literal['sticker'] = 'sticker'
    value: Optional[str] = None


class StickerDtoSerializer(DictDataclassSerializer):
    class Meta:
        dataclass = StickerDto


@dataclass
class StickerDao(DaoMeta):
    type: Literal['sticker'] = 'sticker'
    value: Optional[str] = None


class StickerDaoSerializer(DictDataclassSerializer):
    class Meta:
        dataclass = StickerDao


@register_feature_type
class StickerFeatureType(BaseFeatureType[StickerConfig, StickerDto, StickerDao]):
    slug = 'sticker'
    name = 'Sticker'

    config_class = StickerConfig
    dto_class = StickerDto
    dao_class = StickerDao

    config_serializer_class = StickerConfigSerializer
    dto_serializer_class = StickerDtoSerializer
    dao_serializer_class = StickerDaoSerializer

    def validate_config(self, config):
        pass

    def validate_dto(self, config, dto):
        pass

    def dto_to_dao(self, config, dto, feature: FeatureDef):
        return StickerDao(type=self.slug, value=dto.value, name=feature.name)
