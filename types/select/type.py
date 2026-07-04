"""Select Feature Type - Type Handler."""

from typing import Any, Dict, List, Union

from stapel_attributes.base import BaseFeatureType, FeatureDef
from stapel_attributes.exceptions import FeatureValidationError
from stapel_attributes.registry import register_feature_type
from stapel_attributes.results import ValidationErrorCode
from stapel_attributes.types.select.constants import UI_STYLES
from stapel_attributes.types.select.config import SelectConfig, SelectOption, SelectConfigSerializer
from stapel_attributes.types.select.dto import SelectDto, SelectDtoSerializer
from stapel_attributes.types.select.dao import SelectDao, SelectDaoSerializer


def _get_option_value(opt: Union[SelectOption, Dict]) -> str:
    """Get value from option (typed or dict)."""
    return opt.value if isinstance(opt, SelectOption) else opt.get('value', '')


def _get_option_label(opt: Union[SelectOption, Dict]) -> str:
    """Get label from option (typed or dict)."""
    return opt.label if isinstance(opt, SelectOption) else opt.get('label', '')


def _get_option_default(opt: Union[SelectOption, Dict]) -> bool:
    """Get default from option (typed or dict)."""
    return opt.default if isinstance(opt, SelectOption) else opt.get('default', False)


@register_feature_type
class SelectFeatureType(BaseFeatureType[SelectConfig, SelectDto, SelectDao]):
    """
    Select feature type handler.

    Config:
        - type: "select" (required)
        - options: list of option objects (required)
        - uiStyle: 'dropdown', 'checkboxes', or 'chips' (default: 'dropdown')
        - minSelected: minimum selections (default: 0)
        - maxSelected: maximum selections (default: null = unlimited, use 1 for single select)
        - lockUserInput: lock user input (default: false)

    Option object:
        - value: string value to store
        - label: translation key for display
        - icon: optional icon reference
        - default: default selected state (default: false)

    DTO value: list of selected values (always array)
    DAO value: list + metadata
    """

    slug = 'select'
    name = 'Select'

    # Dataclass types
    config_class = SelectConfig
    dto_class = SelectDto
    dao_class = SelectDao

    # Serializer classes (auto-generated from dataclasses)
    config_serializer_class = SelectConfigSerializer
    dto_serializer_class = SelectDtoSerializer
    dao_serializer_class = SelectDaoSerializer

    def validate_config(self, config: SelectConfig) -> None:
        """Validate select feature configuration."""
        if not config.options:
            raise FeatureValidationError(
                "'options' cannot be empty",
                code=ValidationErrorCode.EMPTY_OPTIONS,
            )

        if config.uiStyle not in UI_STYLES:
            raise FeatureValidationError(
                f"'uiStyle' must be one of: {', '.join(UI_STYLES)}",
                code=ValidationErrorCode.INVALID_CONFIG,
                ref_value=list(UI_STYLES),
            )

        seen_values = set()
        default_count = 0
        for i, option in enumerate(config.options):
            opt_value = _get_option_value(option)
            opt_label = _get_option_label(option)
            opt_default = _get_option_default(option)

            if not opt_value:
                raise FeatureValidationError(
                    f"Option at index {i} must have a 'value' field",
                    code=ValidationErrorCode.INVALID_CONFIG,
                )

            if not opt_label:
                raise FeatureValidationError(
                    f"Option at index {i} must have a 'label' field",
                    code=ValidationErrorCode.INVALID_CONFIG,
                )

            if opt_value in seen_values:
                raise FeatureValidationError(
                    f"Duplicate option value: {opt_value}",
                    code=ValidationErrorCode.INVALID_CONFIG,
                    ref_value=opt_value,
                )
            seen_values.add(opt_value)

            if opt_default:
                default_count += 1

        if config.minSelected < 0:
            raise FeatureValidationError(
                "'minSelected' must be a non-negative integer",
                code=ValidationErrorCode.INVALID_CONFIG,
            )

        if config.maxSelected is not None:
            if config.maxSelected < 1:
                raise FeatureValidationError(
                    "'maxSelected' must be a positive integer",
                    code=ValidationErrorCode.INVALID_CONFIG,
                )

            if config.minSelected > config.maxSelected:
                raise FeatureValidationError(
                    "'minSelected' cannot be greater than 'maxSelected'",
                    code=ValidationErrorCode.MIN_GREATER_THAN_MAX,
                )

            if default_count > config.maxSelected:
                raise FeatureValidationError(
                    f"Number of default options ({default_count}) exceeds maxSelected ({config.maxSelected})",
                    code=ValidationErrorCode.INVALID_CONFIG,
                    ref_value=config.maxSelected,
                )

    def validate_dto(self, config: SelectConfig, dto: SelectDto) -> None:
        """Validate select DTO data against configuration."""
        value = dto.value
        valid_values = {_get_option_value(opt) for opt in config.options}

        if not isinstance(value, list):
            raise FeatureValidationError(
                "Value must be a list of selected options",
                code=ValidationErrorCode.INVALID_TYPE,
            )

        if len(value) < config.minSelected:
            raise FeatureValidationError(
                f"Select at least {config.minSelected} options",
                code=ValidationErrorCode.BELOW_MINIMUM,
                ref_value=config.minSelected,
            )

        if config.maxSelected is not None and len(value) > config.maxSelected:
            raise FeatureValidationError(
                f"Select at most {config.maxSelected} options",
                code=ValidationErrorCode.ABOVE_MAXIMUM,
                ref_value=config.maxSelected,
            )

        if len(value) != len(set(value)):
            raise FeatureValidationError(
                "Duplicate selections are not allowed",
                code=ValidationErrorCode.INVALID_FORMAT,
            )

        for item in value:
            if not isinstance(item, str):
                raise FeatureValidationError(
                    "All selected values must be strings",
                    code=ValidationErrorCode.INVALID_TYPE,
                )

            if item not in valid_values:
                raise FeatureValidationError(
                    f"Invalid option: {item}",
                    code=ValidationErrorCode.NOT_IN_OPTIONS,
                    ref_value=sorted(valid_values),
                )

    def dto_to_dao(
        self,
        config: SelectConfig,
        dto: SelectDto,
        feature: FeatureDef
    ) -> SelectDao:
        """Convert select DTO to DAO with metadata."""
        value = dto.value

        # Deduplicate while preserving order
        seen = set()
        normalized_value = []
        for v in value:
            s = str(v)
            if s not in seen:
                seen.add(s)
                normalized_value.append(s)

        return SelectDao(
            type=self.slug,
            value=normalized_value,
            uiStyle=config.uiStyle,
            maxSelected=config.maxSelected,
            name=feature.name,
            title=feature.show_at_title,
            badge=feature.show_as_badge,
            translate=feature.translate if feature.translate != 'all' else None,
        )

    def normalize_dto(self, config: SelectConfig, dto_data: Dict[str, Any]) -> SelectDto:
        """Normalize select DTO data."""
        value = dto_data.get('value')

        if isinstance(value, list):
            seen = set()
            result = []
            for v in value:
                s = str(v)
                if s not in seen:
                    seen.add(s)
                    result.append(s)
            return SelectDto(type=self.slug, value=result)
        elif value is None:
            return SelectDto(type=self.slug, value=[])
        else:
            return SelectDto(type=self.slug, value=[str(value)])

    def get_default_value(self, config: SelectConfig) -> List[str]:
        """Return list of default values from options with default=true."""
        return [_get_option_value(opt) for opt in config.options if _get_option_default(opt)]

    def is_user_editable(self, config: SelectConfig) -> bool:
        """Check if user can edit this feature's value."""
        return not config.lockUserInput

    def format_value(self, config: SelectConfig, dao: SelectDao) -> str:
        """Format select value for display."""
        label_map = {_get_option_value(opt): _get_option_label(opt) for opt in config.options}
        value = dao.value

        if not isinstance(value, list):
            value = [value] if value else []

        labels = [label_map.get(v, v) for v in value]
        return ', '.join(labels)

    def get_translation_keys(self, config: SelectConfig) -> List[str]:
        """Return translation keys used by this feature."""
        keys = []
        for opt in config.options:
            label = _get_option_label(opt)
            if label:
                keys.append(label)
        return keys

    def is_single_select(self, config: SelectConfig) -> bool:
        """Check if this is configured as single selection."""
        return config.maxSelected == 1
