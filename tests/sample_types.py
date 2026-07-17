"""Sample custom feature types used by the extension-point tests.

``RatingFeatureType`` is NOT decorated — tests register it explicitly
(runtime API or an EXTRA_TYPES class path).
"""

from dataclasses import dataclass
from typing import List, Literal

from stapel_attributes.base import BaseFeatureType, DaoMeta, DictDataclassSerializer, FeatureDef
from stapel_attributes.exceptions import FeatureValidationError
from stapel_attributes.results import ValidationErrorCode


# ---------------------------------------------------------------------------
# rating — a well-behaved custom type
# ---------------------------------------------------------------------------

@dataclass
class RatingConfig:
    type: Literal['rating'] = 'rating'
    max: int = 5


class RatingConfigSerializer(DictDataclassSerializer):
    class Meta:
        dataclass = RatingConfig


@dataclass
class RatingDto:
    type: Literal['rating'] = 'rating'
    value: int = 0


class RatingDtoSerializer(DictDataclassSerializer):
    class Meta:
        dataclass = RatingDto


@dataclass
class RatingDao(DaoMeta):
    type: Literal['rating'] = 'rating'
    value: int = 0


class RatingDaoSerializer(DictDataclassSerializer):
    class Meta:
        dataclass = RatingDao


class RatingFeatureType(BaseFeatureType[RatingConfig, RatingDto, RatingDao]):
    slug = 'rating'
    name = 'Rating'

    config_class = RatingConfig
    dto_class = RatingDto
    dao_class = RatingDao

    config_serializer_class = RatingConfigSerializer
    dto_serializer_class = RatingDtoSerializer
    dao_serializer_class = RatingDaoSerializer

    def validate_config(self, config: RatingConfig) -> None:
        if config.max < 1:
            raise FeatureValidationError(
                "'max' must be positive", code=ValidationErrorCode.INVALID_CONFIG,
            )

    def validate_dto(self, config: RatingConfig, dto: RatingDto) -> None:
        if dto.value < 0:
            raise FeatureValidationError(
                "Value must be >= 0", code=ValidationErrorCode.BELOW_MINIMUM, ref_value=0,
            )
        if dto.value > config.max:
            raise FeatureValidationError(
                f"Value must be <= {config.max}",
                code=ValidationErrorCode.ABOVE_MAXIMUM,
                ref_value=config.max,
            )

    def dto_to_dao(self, config: RatingConfig, dto: RatingDto, feature: FeatureDef) -> RatingDao:
        return RatingDao(type=self.slug, value=dto.value, name=feature.name)

    def get_builtin_translation_keys(self) -> List[str]:
        return ['feature.rating.name']
