"""String Feature Type - Type Handler."""

import re
from typing import Any, Dict, List

from stapel_attributes.base import BaseFeatureType, FeatureDef
from stapel_attributes.exceptions import FeatureValidationError
from stapel_attributes.registry import register_feature_type
from stapel_attributes.results import ValidationErrorCode
from stapel_attributes.types.string.config import StringConfig, StringConfigSerializer
from stapel_attributes.types.string.dto import StringDto, StringDtoSerializer
from stapel_attributes.types.string.dao import StringDao, StringDaoSerializer


@register_feature_type
class StringFeatureType(BaseFeatureType[StringConfig, StringDto, StringDao]):
    """
    String feature type handler.

    Config:
        - type: "string" (required)
        - minLength: minimum string length (optional)
        - maxLength: maximum string length (optional)
        - pattern: regex pattern for validation (optional)
        - options: list of allowed values (optional)
        - allowCustom: allow values not in options (default: true if no options)
        - prefix, postfix, placeholder: UI hints

    DTO value: string
    DAO value: string + metadata
    """

    slug = 'string'
    name = 'String'

    # Dataclass types
    config_class = StringConfig
    dto_class = StringDto
    dao_class = StringDao

    # Serializer classes (auto-generated from dataclasses)
    config_serializer_class = StringConfigSerializer
    dto_serializer_class = StringDtoSerializer
    dao_serializer_class = StringDaoSerializer

    def validate_config(self, config: StringConfig) -> None:
        """Validate string feature configuration."""
        if config.minLength is not None and config.maxLength is not None:
            if config.minLength > config.maxLength:
                raise FeatureValidationError(
                    "'minLength' cannot be greater than 'maxLength'",
                    code=ValidationErrorCode.MIN_GREATER_THAN_MAX,
                )

        if config.pattern is not None:
            try:
                re.compile(config.pattern)
            except re.error as e:
                raise FeatureValidationError(
                    f"Invalid regex pattern: {e}",
                    code=ValidationErrorCode.INVALID_CONFIG,
                )

    def validate_dto(self, config: StringConfig, dto: StringDto) -> None:
        """Validate string DTO data against configuration."""
        value = dto.value

        if config.minLength is not None and len(value) < config.minLength:
            raise FeatureValidationError(
                f"Value must be at least {config.minLength} characters",
                code=ValidationErrorCode.BELOW_MINIMUM,
                ref_value=config.minLength,
            )

        if config.maxLength is not None and len(value) > config.maxLength:
            raise FeatureValidationError(
                f"Value must be at most {config.maxLength} characters",
                code=ValidationErrorCode.ABOVE_MAXIMUM,
                ref_value=config.maxLength,
            )

        if config.pattern:
            if not re.match(config.pattern, value):
                raise FeatureValidationError(
                    f"Value does not match pattern: {config.pattern}",
                    code=ValidationErrorCode.INVALID_FORMAT,
                    ref_value=config.pattern,
                )

        options = config.options if config.options is not None else []
        allow_custom = config.allowCustom if config.allowCustom is not None else (config.options is None)

        if options and not allow_custom:
            if value not in options:
                raise FeatureValidationError(
                    f"Value must be one of: {', '.join(options)}",
                    code=ValidationErrorCode.NOT_IN_OPTIONS,
                    ref_value=list(options),
                )

    def dto_to_dao(
        self,
        config: StringConfig,
        dto: StringDto,
        feature: FeatureDef
    ) -> StringDao:
        """Convert string DTO to DAO with metadata."""
        return StringDao(
            type=self.slug,
            value=dto.value,
            prefix=config.prefix,
            postfix=config.postfix,
            name=feature.name,
            title=feature.show_at_title if feature.show_at_title else None,
            badge=feature.show_as_badge if feature.show_as_badge else None,
            translate=feature.translate if feature.translate != 'all' else None,
        )

    def normalize_dto(self, config: StringConfig, dto_data: Dict[str, Any]) -> StringDto:
        """Normalize string DTO data."""
        value = dto_data.get('value')
        if value is not None:
            value = str(value)
        return StringDto(
            type=self.slug,
            value=value if value is not None else '',
        )

    def format_value(self, config: StringConfig, dao: StringDao) -> str:
        """Format string value for display."""
        value = dao.value
        if value is None:
            return ''

        prefix = config.prefix or ''
        postfix = config.postfix or ''
        formatted = str(value)

        if prefix:
            formatted = f"{prefix} {formatted}"
        if postfix:
            formatted = f"{formatted} {postfix}"

        return formatted

    def get_translation_keys(self, config: StringConfig) -> List[str]:
        """Return translation keys used by this feature."""
        keys = []
        if config.prefix:
            keys.append(config.prefix)
        if config.postfix:
            keys.append(config.postfix)
        return keys
