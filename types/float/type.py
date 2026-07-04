"""Float Feature Type - Type Handler."""

from typing import Any, Dict, List

from stapel_attributes.base import BaseFeatureType, FeatureDef
from stapel_attributes.exceptions import FeatureValidationError
from stapel_attributes.registry import register_feature_type
from stapel_attributes.results import ValidationErrorCode
from stapel_attributes.types.float.config import FloatConfig, FloatConfigSerializer
from stapel_attributes.types.float.dto import FloatDto, FloatDtoSerializer
from stapel_attributes.types.float.dao import FloatDao, FloatDaoSerializer


@register_feature_type
class FloatFeatureType(BaseFeatureType[FloatConfig, FloatDto, FloatDao]):
    """
    Float feature type handler.

    Config:
        - type: "float" (required)
        - min: minimum value (optional)
        - max: maximum value (optional)
        - precision: decimal places (default: 2)
        - options: list of predefined values (optional)
        - allowCustom: allow values not in options (default: true if no options)
        - prefix, postfix, postfix1000, placeholder: UI hints

    DTO value: number (float)
    DAO value: number + metadata
    """

    slug = 'float'
    name = 'Float'

    # Dataclass types
    config_class = FloatConfig
    dto_class = FloatDto
    dao_class = FloatDao

    # Serializer classes (auto-generated from dataclasses)
    config_serializer_class = FloatConfigSerializer
    dto_serializer_class = FloatDtoSerializer
    dao_serializer_class = FloatDaoSerializer

    def validate_config(self, config: FloatConfig) -> None:
        """Validate float feature configuration."""
        if config.min is not None and config.max is not None:
            if config.min > config.max:
                raise FeatureValidationError(
                    "'min' cannot be greater than 'max'",
                    code=ValidationErrorCode.MIN_GREATER_THAN_MAX,
                )

        if config.options is not None:
            for i, opt in enumerate(config.options):
                if not isinstance(opt, (int, float)):
                    raise FeatureValidationError(
                        f"Option at index {i} must be a number",
                        code=ValidationErrorCode.INVALID_CONFIG,
                    )

        if config.precision is not None and config.precision < 0:
            raise FeatureValidationError(
                "'precision' must be a non-negative integer",
                code=ValidationErrorCode.INVALID_CONFIG,
            )

    def validate_dto(self, config: FloatConfig, dto: FloatDto) -> None:
        """Validate float DTO data against configuration."""
        value = dto.value

        if config.min is not None and value < config.min:
            raise FeatureValidationError(
                f"Value must be >= {config.min}",
                code=ValidationErrorCode.BELOW_MINIMUM,
                ref_value=config.min,
            )

        if config.max is not None and value > config.max:
            raise FeatureValidationError(
                f"Value must be <= {config.max}",
                code=ValidationErrorCode.ABOVE_MAXIMUM,
                ref_value=config.max,
            )

        allow_custom = config.allowCustom if config.allowCustom is not None else (config.options is None)
        precision = config.precision if config.precision is not None else 2

        if config.options and not allow_custom:
            float_options = [round(float(o), precision) for o in config.options]
            rounded_value = round(value, precision)
            if rounded_value not in float_options:
                raise FeatureValidationError(
                    f"Value must be one of: {', '.join(str(o) for o in config.options)}",
                    code=ValidationErrorCode.NOT_IN_OPTIONS,
                    ref_value=list(config.options),
                )

    def dto_to_dao(
        self,
        config: FloatConfig,
        dto: FloatDto,
        feature: FeatureDef
    ) -> FloatDao:
        """Convert float DTO to DAO with metadata."""
        precision = config.precision if config.precision is not None else 2
        value = round(dto.value, precision)

        return FloatDao(
            type=self.slug,
            value=value,
            prefix=config.prefix,
            postfix=config.postfix,
            postfix1000=config.postfix1000,
            precision=precision,
            name=feature.name,
            title=feature.show_at_title if feature.show_at_title else None,
            badge=feature.show_as_badge if feature.show_as_badge else None,
            translate=feature.translate if feature.translate != 'all' else None,
        )

    def normalize_dto(self, config: FloatConfig, dto_data: Dict[str, Any]) -> FloatDto:
        """Normalize float DTO data."""
        precision = config.precision if config.precision is not None else 2
        value = dto_data.get('value')
        if value is not None:
            try:
                value = round(float(value), precision)
            except (ValueError, TypeError):
                raise FeatureValidationError(
                    f"Value must be a number, got: {type(value).__name__}",
                    code=ValidationErrorCode.INVALID_TYPE,
                )
        return FloatDto(
            type=self.slug,
            value=value if value is not None else 0.0,
        )

    def get_default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            'type': self.slug,
            'precision': 2,
        }

    def format_value(self, config: FloatConfig, dao: FloatDao) -> str:
        """Format float value for display."""
        value = dao.value
        if value is None:
            return ''

        prefix = config.prefix or ''
        postfix = config.postfix or ''
        postfix1000 = config.postfix1000 or ''
        precision = config.precision if config.precision is not None else 2

        # Format with thousands separator if postfix1000 is set
        if postfix1000 and abs(value) >= 1000:
            formatted = f"{value / 1000:.{precision}f}".rstrip('0').rstrip('.')
            postfix = postfix1000
        else:
            formatted = f"{value:.{precision}f}"

        if prefix:
            formatted = f"{prefix} {formatted}"
        if postfix:
            formatted = f"{formatted} {postfix}"

        return formatted

    def get_translation_keys(self, config: FloatConfig) -> List[str]:
        """Return translation keys used by this feature."""
        keys = []
        if config.prefix:
            keys.append(config.prefix)
        if config.postfix:
            keys.append(config.postfix)
        if config.postfix1000:
            keys.append(config.postfix1000)
        return keys
