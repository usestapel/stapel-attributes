"""Header Feature Type - Type Handler."""

from typing import Any, Dict, List

from stapel_attributes.base import BaseFeatureType, FeatureDef
from stapel_attributes.exceptions import FeatureValidationError
from stapel_attributes.registry import register_feature_type
from stapel_attributes.results import ValidationErrorCode
from stapel_attributes.types.header.constants import VALID_STYLES
from stapel_attributes.types.header.config import HeaderConfig, HeaderConfigSerializer
from stapel_attributes.types.header.dto import HeaderDto, HeaderDtoSerializer
from stapel_attributes.types.header.dao import HeaderDao, HeaderDaoSerializer


@register_feature_type
class HeaderFeatureType(BaseFeatureType[HeaderConfig, HeaderDto, HeaderDao]):
    """
    Header feature type handler.

    A quasi-type for visual section headers/separators.
    Users cannot fill this, but will see it between functional blocks.

    Config:
        - type: "header" (required)
        - style: "l" | "m" (required)

    The header text comes from the feature definition's name (translation key).
    Value: null (not user-editable)
    """

    slug = 'header'
    name = 'Header'

    # Dataclass types
    config_class = HeaderConfig
    dto_class = HeaderDto
    dao_class = HeaderDao

    # Serializer classes (auto-generated from dataclasses)
    config_serializer_class = HeaderConfigSerializer
    dto_serializer_class = HeaderDtoSerializer
    dao_serializer_class = HeaderDaoSerializer

    def validate_config(self, config: HeaderConfig) -> None:
        """Validate header configuration."""
        if not config.style:
            raise FeatureValidationError(
                "'style' is required for header type",
                code=ValidationErrorCode.INVALID_CONFIG,
            )

        if config.style not in VALID_STYLES:
            raise FeatureValidationError(
                f"'style' must be one of: {', '.join(sorted(VALID_STYLES))}",
                code=ValidationErrorCode.INVALID_CONFIG,
                ref_value=sorted(VALID_STYLES),
            )

    def validate_dto(self, config: HeaderConfig, dto: HeaderDto) -> None:
        """Validate header DTO data."""
        if dto.value is not None:
            raise FeatureValidationError(
                "Header type does not accept values",
                code=ValidationErrorCode.INVALID_FORMAT,
            )

    def dto_to_dao(
        self,
        config: HeaderConfig,
        dto: HeaderDto,
        feature: FeatureDef
    ) -> HeaderDao:
        """Convert header DTO to DAO with metadata."""
        return HeaderDao(
            type=self.slug,
            style=config.style,
            name=feature.name,
            title=False,
            badge=False,
            translate=feature.translate if feature.translate != 'all' else None,
        )

    def normalize_dto(self, config: HeaderConfig, dto_data: Dict[str, Any]) -> HeaderDto:
        """Normalize header DTO data. Always return None value."""
        return HeaderDto(type=self.slug, value=None)

    def get_default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            'type': self.slug,
            'style': 'l',
        }

    def get_default_value(self, config: HeaderConfig) -> None:
        """Headers have no default value."""
        return None

    def is_user_editable(self, config: HeaderConfig) -> bool:
        """Headers are never user-editable."""
        return False

    def format_value(self, config: HeaderConfig, dao: HeaderDao) -> str:
        """Return the name for display."""
        return dao.name or ''

    def get_translation_keys(self, config: HeaderConfig) -> List[str]:
        """Return translation keys. Header uses the feature name, managed separately."""
        return []
