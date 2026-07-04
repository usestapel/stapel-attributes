"""Hierarchical Select Feature Type - Type Handler."""

from typing import Any, Dict, List, Optional, Union

from stapel_attributes.base import BaseFeatureType, FeatureDef
from stapel_attributes.exceptions import FeatureValidationError
from stapel_attributes.registry import register_feature_type
from stapel_attributes.results import ValidationErrorCode
from stapel_attributes.types.hierarchical_select.config import (
    HierarchicalSelectConfig, HierarchicalOption, HierarchicalSelectConfigSerializer
)
from stapel_attributes.types.hierarchical_select.dto import (
    HierarchicalSelectDto, HierarchicalSelectDtoSerializer
)
from stapel_attributes.types.hierarchical_select.dao import (
    HierarchicalSelectDao, HierarchicalSelectDaoSerializer
)


def _get_option_value(option: Union[HierarchicalOption, Dict]) -> str:
    """Get value from option (typed or dict)."""
    return option.value if isinstance(option, HierarchicalOption) else option.get('value', '')


def _get_option_label(option: Union[HierarchicalOption, Dict]) -> str:
    """Get label from option (typed or dict)."""
    return option.label if isinstance(option, HierarchicalOption) else option.get('label', '')


def _get_option_children(option: Union[HierarchicalOption, Dict]) -> List:
    """Get children from option (typed or dict)."""
    return option.children if isinstance(option, HierarchicalOption) else option.get('children', [])


def _validate_options_recursive(
    options: List,
    path: str = '',
    seen_values: Optional[set] = None
) -> None:
    """Recursively validate options structure."""
    if seen_values is None:
        seen_values = set()

    for idx, option in enumerate(options):
        current_path = f"{path}[{idx}]" if path else f"options[{idx}]"
        option_value = _get_option_value(option)

        if not option_value:
            raise FeatureValidationError(
                f"Option at {current_path} is missing 'value'",
                code=ValidationErrorCode.INVALID_CONFIG,
            )

        # Check for duplicate values at same level
        if option_value in seen_values:
            raise FeatureValidationError(
                f"Duplicate value '{option_value}' at {current_path}",
                code=ValidationErrorCode.INVALID_CONFIG,
                ref_value=option_value,
            )
        seen_values.add(option_value)

        # Recursively validate children
        children = _get_option_children(option)
        if children:
            if not isinstance(children, list):
                raise FeatureValidationError(
                    f"Children at {current_path} must be an array",
                    code=ValidationErrorCode.INVALID_CONFIG,
                )
            _validate_options_recursive(children, f"{current_path}.children", set())


def _find_option_by_value(options: List, value: str) -> Optional[Union[HierarchicalOption, Dict]]:
    """Find option by value in options list."""
    for option in options:
        if _get_option_value(option) == value:
            return option
    return None


def _get_option_children_title(option: Union[HierarchicalOption, Dict]) -> Optional[str]:
    """Get childrenTitle from option (typed or dict)."""
    return option.childrenTitle if isinstance(option, HierarchicalOption) else option.get('childrenTitle')


def _collect_translation_keys(options: List, keys: List[str]) -> None:
    """Recursively collect translation keys from options."""
    for option in options:
        label = _get_option_label(option)
        if label:
            keys.append(label)
        children_title = _get_option_children_title(option)
        if children_title:
            keys.append(children_title)
        children = _get_option_children(option)
        if children:
            _collect_translation_keys(children, keys)


@register_feature_type
class HierarchicalSelectFeatureType(BaseFeatureType[HierarchicalSelectConfig, HierarchicalSelectDto, HierarchicalSelectDao]):
    """
    Hierarchical select feature type handler.

    Supports recursive tree structure where each option can have nested children.
    User navigates through the tree and selected path is stored as array of values.

    Config:
        - type: "hierarchical_select" (required)
        - options: recursive tree of options with value, label, icon, children
        - required: whether selection is required (default: true)
        - minDepth: minimum selection depth required (default: 1)
        - maxDepth: maximum depth allowed (None = unlimited)

    DTO/DAO value: path - array of values from root to leaf
        Example: ['electronics', 'phones', 'smartphones']
    """

    slug = 'hierarchical_select'
    name = 'Hierarchical Select'

    # Dataclass types
    config_class = HierarchicalSelectConfig
    dto_class = HierarchicalSelectDto
    dao_class = HierarchicalSelectDao

    # Serializer classes (auto-generated from dataclasses)
    config_serializer_class = HierarchicalSelectConfigSerializer
    dto_serializer_class = HierarchicalSelectDtoSerializer
    dao_serializer_class = HierarchicalSelectDaoSerializer

    def validate_config(self, config: HierarchicalSelectConfig) -> None:
        """Validate hierarchical select configuration."""
        if not config.options:
            raise FeatureValidationError(
                "'options' is required for hierarchical_select type",
                code=ValidationErrorCode.EMPTY_OPTIONS,
            )
        if not isinstance(config.options, list):
            raise FeatureValidationError(
                "'options' must be an array",
                code=ValidationErrorCode.INVALID_CONFIG,
            )
        if len(config.options) == 0:
            raise FeatureValidationError(
                "'options' cannot be empty",
                code=ValidationErrorCode.EMPTY_OPTIONS,
            )

        _validate_options_recursive(config.options)

        if config.minDepth < 1:
            raise FeatureValidationError(
                "'minDepth' must be at least 1",
                code=ValidationErrorCode.INVALID_CONFIG,
            )

        if config.maxDepth is not None and config.maxDepth < config.minDepth:
            raise FeatureValidationError(
                "'maxDepth' cannot be less than 'minDepth'",
                code=ValidationErrorCode.MIN_GREATER_THAN_MAX,
            )

    def validate_dto(self, config: HierarchicalSelectConfig, dto: HierarchicalSelectDto) -> None:
        """Validate hierarchical select DTO data."""
        path = dto.value

        if not isinstance(path, list):
            raise FeatureValidationError(
                "'value' must be an array of values",
                code=ValidationErrorCode.INVALID_TYPE,
            )

        if len(path) == 0:
            if config.required:
                raise FeatureValidationError(
                    "Selection is required",
                    code=ValidationErrorCode.MANDATORY_MISSING,
                )
            return

        # Validate path depth
        if len(path) < config.minDepth:
            raise FeatureValidationError(
                f"Selection must have at least {config.minDepth} level(s)",
                code=ValidationErrorCode.BELOW_MINIMUM,
                ref_value=config.minDepth,
            )

        if config.maxDepth is not None and len(path) > config.maxDepth:
            raise FeatureValidationError(
                f"Selection cannot exceed {config.maxDepth} level(s)",
                code=ValidationErrorCode.ABOVE_MAXIMUM,
                ref_value=config.maxDepth,
            )

        # Validate path values exist in tree
        current_options = config.options
        for depth, value in enumerate(path):
            if not isinstance(value, str):
                raise FeatureValidationError(
                    f"Value at depth {depth} must be a string",
                    code=ValidationErrorCode.INVALID_TYPE,
                )

            option = _find_option_by_value(current_options, value)
            if option is None:
                valid_values = [_get_option_value(o) for o in current_options]
                raise FeatureValidationError(
                    f"Invalid value '{value}' at depth {depth}. "
                    f"Valid values: {', '.join(valid_values)}",
                    code=ValidationErrorCode.NOT_IN_OPTIONS,
                    ref_value=valid_values,
                )

            # Move to children for next iteration
            current_options = _get_option_children(option) or []

            # If we have more path values but no children, it's an error
            if depth < len(path) - 1 and not current_options:
                raise FeatureValidationError(
                    f"Value '{value}' at depth {depth} has no children, "
                    f"but path continues with '{path[depth + 1]}'",
                    code=ValidationErrorCode.INVALID_FORMAT,
                )

    def dto_to_dao(
        self,
        config: HierarchicalSelectConfig,
        dto: HierarchicalSelectDto,
        feature: FeatureDef
    ) -> HierarchicalSelectDao:
        """Convert hierarchical select DTO to DAO with metadata."""
        return HierarchicalSelectDao(
            type='hierarchical_select',
            value=dto.value,
            name=feature.name,
            title=feature.show_at_title,
            badge=feature.show_as_badge,
            translate=feature.translate if feature.translate != 'all' else None,
        )

    def normalize_dto(self, config: HierarchicalSelectConfig, dto_data: Dict[str, Any]) -> HierarchicalSelectDto:
        """Normalize hierarchical select DTO data."""
        value = dto_data.get('value', [])

        if not isinstance(value, list):
            value = []

        # Ensure all values are strings
        normalized_value = [str(v) for v in value if v]

        return HierarchicalSelectDto(type='hierarchical_select', value=normalized_value)

    def get_default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            'type': self.slug,
            'options': [],
            'required': True,
            'minDepth': 1,
            'maxDepth': None,
        }

    def get_default_value(self, config: HierarchicalSelectConfig) -> List[str]:
        """Hierarchical select has no default value."""
        return []

    def format_value(self, config: HierarchicalSelectConfig, dao: HierarchicalSelectDao) -> str:
        """Format value for display."""
        path = dao.value

        if not path:
            return ''

        # Build display path with labels
        labels = []
        current_options = config.options

        for value in path:
            option = _find_option_by_value(current_options, value)
            if option:
                labels.append(_get_option_label(option) or value)
                current_options = _get_option_children(option) or []
            else:
                labels.append(value)
                current_options = []

        return ' / '.join(labels)

    def get_translation_keys(self, config: HierarchicalSelectConfig) -> List[str]:
        """Return translation keys used by this feature."""
        keys: List[str] = []
        _collect_translation_keys(config.options, keys)
        return keys
