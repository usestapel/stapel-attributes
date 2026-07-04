"""Integer Feature Type - Type Handler."""

from typing import Dict, List, Any

from stapel_attributes.base import BaseFeatureType, FeatureDef
from stapel_attributes.exceptions import FeatureValidationError
from stapel_attributes.registry import register_feature_type
from stapel_attributes.results import ValidationErrorCode
from stapel_attributes.types.int.config import IntConfig, IntConfigSerializer
from stapel_attributes.types.int.dto import IntDto, IntDtoSerializer
from stapel_attributes.types.int.dao import IntDao, IntDaoSerializer


@register_feature_type
class IntFeatureType(BaseFeatureType[IntConfig, IntDto, IntDao]):
    """
    Integer feature type handler.

    Config:
        - type: "int" (required)
        - min: minimum value (optional)
        - max: maximum value (optional)
        - options: list of predefined values (optional)
        - allowCustom: allow values not in options (default: true if no options)
        - precision: decimal places for postfix1000 formatting (default: 1)
        - prefix, postfix, postfix1000, placeholder: UI hints

    DTO value: integer
    DAO value: integer + metadata
    """

    slug = 'int'
    name = 'Integer'

    # Dataclass types
    config_class = IntConfig
    dto_class = IntDto
    dao_class = IntDao

    # Serializer classes
    config_serializer_class = IntConfigSerializer
    dto_serializer_class = IntDtoSerializer
    dao_serializer_class = IntDaoSerializer

    def validate_config(self, config: IntConfig) -> None:
        """Validate integer feature configuration."""
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

    def validate_dto(self, config: IntConfig, dto: IntDto) -> None:
        """Validate integer DTO data against configuration."""
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
        if config.options and not allow_custom:
            int_options = [int(o) for o in config.options]
            if value not in int_options:
                raise FeatureValidationError(
                    f"Value must be one of: {', '.join(str(o) for o in config.options)}",
                    code=ValidationErrorCode.NOT_IN_OPTIONS,
                    ref_value=list(config.options),
                )

    def dto_to_dao(self, config: IntConfig, dto: IntDto, feature: FeatureDef) -> IntDao:
        """Convert integer DTO to DAO with metadata."""
        return IntDao(
            type=self.slug,
            value=dto.value,
            prefix=config.prefix,
            postfix=config.postfix,
            postfix1000=config.postfix1000,
            precision=config.precision if config.precision is not None else 1,
            name=feature.name,
            title=feature.show_at_title if feature.show_at_title else None,
            badge=feature.show_as_badge if feature.show_as_badge else None,
            translate=feature.translate if feature.translate != 'all' else None,
        )

    def normalize_dto(self, config: IntConfig, dto_data: Dict[str, Any]) -> IntDto:
        """Normalize integer DTO data."""
        value = dto_data.get('value')
        if value is not None:
            try:
                value = int(value)
            except (ValueError, TypeError):
                raise FeatureValidationError(
                    f"Value must be an integer, got: {type(value).__name__}",
                    code=ValidationErrorCode.INVALID_TYPE,
                )
        return IntDto(
            type=self.slug,
            value=value if value is not None else 0,
        )

    def format_value(self, config: IntConfig, dao: IntDao) -> str:
        """Format integer value for display."""
        value = dao.value
        if value is None:
            return ''

        prefix = config.prefix or ''
        postfix = config.postfix or ''
        postfix1000 = config.postfix1000 or ''
        precision = config.precision if config.precision is not None else 1

        # Format with thousands separator if postfix1000 is set
        if postfix1000 and abs(value) >= 1000:
            formatted = f"{value / 1000:.{precision}f}".rstrip('0').rstrip('.')
            postfix = postfix1000
        else:
            formatted = str(value)

        if prefix:
            formatted = f"{prefix} {formatted}"
        if postfix:
            formatted = f"{formatted} {postfix}"

        return formatted

    def get_translation_keys(self, config: IntConfig) -> List[str]:
        """Return translation keys used by this feature."""
        keys = []
        if config.prefix:
            keys.append(config.prefix)
        if config.postfix:
            keys.append(config.postfix)
        if config.postfix1000:
            keys.append(config.postfix1000)
        return keys
