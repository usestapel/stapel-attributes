"""Hex Color Feature Type - Type Handler."""

import re
from typing import Any, Dict, List, Optional, Union

from stapel_attributes.base import BaseFeatureType, FeatureDef
from stapel_attributes.exceptions import FeatureValidationError
from stapel_attributes.registry import register_feature_type
from stapel_attributes.results import ValidationErrorCode
from stapel_attributes.types.hex_color.constants import SIMPLE_COLORS
from stapel_attributes.types.hex_color.config import HexColorConfig, HexColorOption, HexColorConfigSerializer
from stapel_attributes.types.hex_color.dto import HexColorDto, HexColorValue, HexColorDtoSerializer
from stapel_attributes.types.hex_color.dao import HexColorDao, HexColorDaoSerializer


HEX_PATTERN = re.compile(r'^#(?:[0-9a-fA-F]{3}){1,2}$')


def _get_color_opt_hex(opt: Union[HexColorOption, Dict]) -> Optional[str]:
    """Get hex from color option (typed or dict)."""
    return opt.hex if isinstance(opt, HexColorOption) else opt.get('hex')


def _get_color_opt_label(opt: Union[HexColorOption, Dict]) -> Optional[str]:
    """Get label from color option (typed or dict)."""
    return opt.label if isinstance(opt, HexColorOption) else opt.get('label')


def _get_color_opt_simple(opt: Union[HexColorOption, Dict]) -> str:
    """Get simple from color option (typed or dict)."""
    return opt.simple if isinstance(opt, HexColorOption) else opt.get('simple', '')


@register_feature_type
class HexColorFeatureType(BaseFeatureType[HexColorConfig, HexColorDto, HexColorDao]):
    """
    Hex color feature type handler.

    Config:
        - type: "hex_color" (required)
        - options: list of color option objects (optional)
        - allowCustom: allow custom colors (default: false)

    Option object:
        - hex: hex color code (#RRGGBB or #RGB) - optional
        - label: translation key for display (optional)
        - simple: simple color category (required, e.g., "black", "pink")

    DTO value object:
        - hex: selected hex color code (optional)
        - label: label translation key (optional)
        - simple: simple color category (required)

    DAO value: same as DTO + metadata
    """

    slug = 'hex_color'
    name = 'HexColor'

    # Dataclass types
    config_class = HexColorConfig
    dto_class = HexColorDto
    dao_class = HexColorDao

    # Serializer classes (auto-generated from dataclasses)
    config_serializer_class = HexColorConfigSerializer
    dto_serializer_class = HexColorDtoSerializer
    dao_serializer_class = HexColorDaoSerializer

    def _normalize_hex(self, hex_color: str) -> str:
        """Normalize hex color to uppercase #RRGGBB format."""
        hex_color = hex_color.upper()
        if len(hex_color) == 4:  # #RGB -> #RRGGBB
            return f"#{hex_color[1]*2}{hex_color[2]*2}{hex_color[3]*2}"
        return hex_color

    def validate_config(self, config: HexColorConfig) -> None:
        """Validate hex color feature configuration."""
        if config.options is None:
            return

        if not isinstance(config.options, list):
            raise FeatureValidationError(
                "'options' must be a list",
                code=ValidationErrorCode.INVALID_CONFIG,
            )

        seen_hex = set()
        for i, option in enumerate(config.options):
            opt_hex = _get_color_opt_hex(option)
            opt_label = _get_color_opt_label(option)
            opt_simple = _get_color_opt_simple(option)

            # Validate hex (optional - None or empty string allowed)
            if opt_hex:
                if not isinstance(opt_hex, str) or not HEX_PATTERN.match(opt_hex):
                    raise FeatureValidationError(
                        f"Invalid hex at index {i}: {opt_hex}. Must be #RGB or #RRGGBB",
                        code=ValidationErrorCode.INVALID_CONFIG,
                    )

                normalized_hex = self._normalize_hex(opt_hex)
                if normalized_hex in seen_hex:
                    raise FeatureValidationError(
                        f"Duplicate hex color: {opt_hex}",
                        code=ValidationErrorCode.INVALID_CONFIG,
                    )
                seen_hex.add(normalized_hex)

            # Validate label (optional)
            if opt_label is not None and not isinstance(opt_label, str):
                raise FeatureValidationError(
                    f"Label at index {i} must be a string",
                    code=ValidationErrorCode.INVALID_CONFIG,
                )

            # Validate simple (required)
            if not opt_simple:
                raise FeatureValidationError(
                    f"Option at index {i} must have a 'simple' field",
                    code=ValidationErrorCode.INVALID_CONFIG,
                )
            if not isinstance(opt_simple, str):
                raise FeatureValidationError(
                    f"Simple at index {i} must be a string",
                    code=ValidationErrorCode.INVALID_CONFIG,
                )
            if opt_simple not in SIMPLE_COLORS:
                raise FeatureValidationError(
                    f"Invalid simple color at index {i}: {opt_simple}. "
                    f"Must be one of: {', '.join(SIMPLE_COLORS)}",
                    code=ValidationErrorCode.INVALID_CONFIG,
                    ref_value=list(SIMPLE_COLORS),
                )

    def validate_dto(self, config: HexColorConfig, dto: HexColorDto) -> None:
        """Validate hex color DTO data against configuration."""
        if not isinstance(dto.value, HexColorValue):
            raise FeatureValidationError(
                f"Value must be a HexColorValue object, got: {type(dto.value).__name__}",
                code=ValidationErrorCode.INVALID_TYPE,
            )

        value = dto.value
        hex_value = value.hex
        simple_value = value.simple

        # Validate hex (optional)
        if hex_value is not None:
            if not isinstance(hex_value, str):
                raise FeatureValidationError(
                    "'hex' must be a string",
                    code=ValidationErrorCode.INVALID_TYPE,
                )
            hex_value = hex_value.strip()
            if hex_value and not HEX_PATTERN.match(hex_value):
                raise FeatureValidationError(
                    f"Invalid hex color: {hex_value}. Must be #RGB or #RRGGBB format",
                    code=ValidationErrorCode.INVALID_FORMAT,
                )

        # Validate simple (required)
        if not simple_value:
            raise FeatureValidationError(
                "Value must have a 'simple' field",
                code=ValidationErrorCode.INVALID_FORMAT,
            )
        if not isinstance(simple_value, str):
            raise FeatureValidationError(
                "'simple' must be a string",
                code=ValidationErrorCode.INVALID_TYPE,
            )
        if simple_value not in SIMPLE_COLORS:
            raise FeatureValidationError(
                f"Invalid simple color: {simple_value}. "
                f"Must be one of: {', '.join(SIMPLE_COLORS)}",
                code=ValidationErrorCode.NOT_IN_OPTIONS,
                ref_value=list(SIMPLE_COLORS),
            )

        if config.options and not config.allowCustom:
            normalized_hex = self._normalize_hex(hex_value) if hex_value else None
            matched = False

            # First try exact match by hex
            if hex_value:
                for opt in config.options:
                    opt_hex = _get_color_opt_hex(opt)
                    if opt_hex and self._normalize_hex(opt_hex) == normalized_hex:
                        opt_simple = _get_color_opt_simple(opt)
                        if simple_value != opt_simple:
                            raise FeatureValidationError(
                                f"Simple color '{simple_value}' doesn't match expected '{opt_simple}' for hex '{hex_value}'",
                                code=ValidationErrorCode.INVALID_FORMAT,
                                ref_value=opt_simple,
                            )
                        matched = True
                        break

            # Fallback: match by simple color
            if not matched:
                for opt in config.options:
                    if _get_color_opt_simple(opt) == simple_value:
                        matched = True
                        break

            if not matched:
                valid_simples = [_get_color_opt_simple(opt) for opt in config.options]
                raise FeatureValidationError(
                    f"Simple color must be one of: {', '.join(valid_simples)}",
                    code=ValidationErrorCode.NOT_IN_OPTIONS,
                    ref_value=valid_simples,
                )

    def dto_to_dao(
        self,
        config: HexColorConfig,
        dto: HexColorDto,
        feature: FeatureDef
    ) -> HexColorDao:
        """Convert hex color DTO to DAO with metadata."""
        value = dto.value
        if value is None:
            raise FeatureValidationError(
                "Hex color value is required",
                code=ValidationErrorCode.INVALID_FORMAT,
            )
        hex_val = value.hex
        label = value.label

        return HexColorDao(
            type=self.slug,
            simple=str(value.simple).strip().lower(),
            hex=self._normalize_hex(str(hex_val).strip()) if hex_val else None,
            label=label if label else None,
            name=feature.name,
            title=feature.show_at_title,
            badge=feature.show_as_badge,
            translate=feature.translate if feature.translate != 'all' else None,
        )

    def normalize_dto(self, config: HexColorConfig, dto_data: Dict[str, Any]) -> HexColorDto:
        """Normalize hex color DTO data."""
        value = dto_data.get('value', {})

        if isinstance(value, dict):
            hex_val = value.get('hex')
            return HexColorDto(
                type=self.slug,
                value=HexColorValue(
                    simple=str(value.get('simple', '')).strip().lower(),
                    hex=self._normalize_hex(str(hex_val).strip()) if hex_val else None,
                    label=value.get('label'),
                )
            )

        return HexColorDto(type=self.slug, value=HexColorValue(simple=''))

    def format_value(self, config: HexColorConfig, dao: HexColorDao) -> str:
        """Format hex color value for display."""
        hex_value = dao.hex
        simple_value = dao.simple

        # Find matching option to get label
        if hex_value and config.options is not None:
            normalized_hex = self._normalize_hex(hex_value)
            for opt in config.options:
                opt_hex = _get_color_opt_hex(opt)
                if opt_hex and self._normalize_hex(opt_hex) == normalized_hex:
                    return _get_color_opt_label(opt) or _get_color_opt_simple(opt) or normalized_hex
            return normalized_hex

        # No hex - try to match by simple
        if config.options is not None:
            for opt in config.options:
                if _get_color_opt_simple(opt) == simple_value:
                    return _get_color_opt_label(opt) or simple_value

        return simple_value

    def get_translation_keys(self, config: HexColorConfig) -> List[str]:
        """Return translation keys used by this feature."""
        keys = []
        if config.options is not None:
            for opt in config.options:
                label = _get_color_opt_label(opt)
                if label:
                    keys.append(label)
        return keys

    @staticmethod
    def get_simple_colors() -> List[str]:
        """Return available simple color categories."""
        return SIMPLE_COLORS.copy()
