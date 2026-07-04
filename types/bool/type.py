"""Boolean Feature Type - Type Handler."""

from typing import Any, Dict, List

from stapel_attributes.base import BaseFeatureType, FeatureDef
from stapel_attributes.exceptions import FeatureValidationError
from stapel_attributes.registry import register_feature_type
from stapel_attributes.results import ValidationErrorCode
from stapel_attributes.types.bool.config import BoolConfig, BoolConfigSerializer
from stapel_attributes.types.bool.dto import BoolDto, BoolDtoSerializer
from stapel_attributes.types.bool.dao import BoolDao, BoolDaoSerializer


TRUE_VALUES = {'true', '1', 'yes', 'on'}
FALSE_VALUES = {'false', '0', 'no', 'off'}


@register_feature_type
class BoolFeatureType(BaseFeatureType[BoolConfig, BoolDto, BoolDao]):
    """
    Boolean feature type handler.

    Config:
        - type: "bool" (required)
        - trueLabel: translation key for true label (optional)
        - falseLabel: translation key for false label (optional)

    DTO value: boolean or string "true"/"false"
    DAO value: boolean + metadata
    """

    slug = 'bool'
    name = 'Boolean'

    # Dataclass types
    config_class = BoolConfig
    dto_class = BoolDto
    dao_class = BoolDao

    # Serializer classes (auto-generated from dataclasses)
    config_serializer_class = BoolConfigSerializer
    dto_serializer_class = BoolDtoSerializer
    dao_serializer_class = BoolDaoSerializer

    def validate_config(self, config: BoolConfig) -> None:
        """Validate boolean feature configuration."""
        # No specific validation needed - dataclass already ensures correct types
        pass

    def validate_dto(self, config: BoolConfig, dto: BoolDto) -> None:
        """Validate boolean DTO data against configuration."""
        # Boolean type is already validated by dataclass
        # No additional constraints to check
        pass

    def _normalize_value(self, value: Any) -> bool:
        """Convert value to boolean."""
        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            lower_val = value.lower()
            if lower_val in TRUE_VALUES:
                return True
            elif lower_val in FALSE_VALUES:
                return False
            else:
                raise FeatureValidationError(
                    f"Invalid boolean string: '{value}'. Use true/false, yes/no, 1/0, or on/off",
                    code=ValidationErrorCode.INVALID_TYPE,
                )

        if isinstance(value, (int, float)):
            return bool(value)

        raise FeatureValidationError(
            f"Value must be a boolean, got: {type(value).__name__}",
            code=ValidationErrorCode.INVALID_TYPE,
        )

    def dto_to_dao(
        self,
        config: BoolConfig,
        dto: BoolDto,
        feature: FeatureDef
    ) -> BoolDao:
        """Convert boolean DTO to DAO with metadata."""
        return BoolDao(
            type=self.slug,
            value=dto.value,
            trueLabel=config.trueLabel,
            falseLabel=config.falseLabel,
            name=feature.name,
            title=feature.show_at_title if feature.show_at_title else None,
            badge=feature.show_as_badge if feature.show_as_badge else None,
            translate=feature.translate if feature.translate != 'all' else None,
        )

    def normalize_dto(self, config: BoolConfig, dto_data: Dict[str, Any]) -> BoolDto:
        """Normalize boolean DTO data."""
        return BoolDto(
            type=self.slug,
            value=self._normalize_value(dto_data.get('value', False)),
        )

    def format_value(self, config: BoolConfig, dao: BoolDao) -> str:
        """Format boolean value for display."""
        if dao.value:
            return config.trueLabel if config.trueLabel else 'feature.bool.true'
        else:
            return config.falseLabel if config.falseLabel else 'feature.bool.false'

    def get_translation_keys(self, config: BoolConfig) -> List[str]:
        """Return translation keys used by this feature."""
        keys = []

        if config.trueLabel:
            keys.append(config.trueLabel)
        else:
            keys.append('feature.bool.true')

        if config.falseLabel:
            keys.append(config.falseLabel)
        else:
            keys.append('feature.bool.false')

        return keys

    def get_builtin_translation_keys(self) -> List[str]:
        """Static keys used when no custom labels are configured."""
        return ['feature.bool.true', 'feature.bool.false']
