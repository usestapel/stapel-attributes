"""Date Feature Type - Type Handler."""

import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from stapel_attributes.base import BaseFeatureType, FeatureDef
from stapel_attributes.exceptions import FeatureValidationError
from stapel_attributes.registry import register_feature_type
from stapel_attributes.results import ValidationErrorCode
from stapel_attributes.types.date.config import DateConfig, DateConfigSerializer
from stapel_attributes.types.date.dto import DateDto, DateDtoSerializer
from stapel_attributes.types.date.dao import DateDao, DateDaoSerializer


@register_feature_type
class DateFeatureType(BaseFeatureType[DateConfig, DateDto, DateDao]):
    """
    Date feature type handler.

    Config:
        - type: "date" (required)
        - precision: 'year' | 'month' | 'date' | 'datetime' (default: 'date')
        - minDate: minimum timestamp (optional)
        - maxDate: maximum timestamp (optional)
        - allowFuture: allow future dates (default: true)
        - allowPast: allow past dates (default: true)
        - default: default timestamp (optional)
        - options: list of predefined timestamps (optional)
        - lockInput: lock user input (default: false)
        - placeholder: input placeholder

    DTO/DAO value: Unix timestamp (integer)
    """

    slug = 'date'
    name = 'Date'

    # Dataclass types
    config_class = DateConfig
    dto_class = DateDto
    dao_class = DateDao

    # Serializer classes (auto-generated from dataclasses)
    config_serializer_class = DateConfigSerializer
    dto_serializer_class = DateDtoSerializer
    dao_serializer_class = DateDaoSerializer

    def _get_current_timestamp(self) -> int:
        """Get current Unix timestamp."""
        return int(time.time())

    def _timestamp_to_datetime(self, timestamp: int) -> datetime:
        """Convert timestamp to datetime."""
        return datetime.fromtimestamp(timestamp)

    def _format_timestamp(self, timestamp: int, precision: str) -> str:
        """Format timestamp according to precision."""
        dt = self._timestamp_to_datetime(timestamp)
        if precision == 'year':
            return dt.strftime('%Y')
        elif precision == 'month':
            return dt.strftime('%Y-%m')
        elif precision == 'datetime':
            return dt.strftime('%Y-%m-%d %H:%M')
        else:  # 'date'
            return dt.strftime('%Y-%m-%d')

    def validate_config(self, config: DateConfig) -> None:
        """Validate date feature configuration."""
        if not config.allowFuture and not config.allowPast:
            raise FeatureValidationError(
                "At least one of 'allowFuture' or 'allowPast' must be true",
                code=ValidationErrorCode.INVALID_CONFIG,
            )

        if config.precision not in ('year', 'month', 'date', 'datetime'):
            raise FeatureValidationError(
                "'precision' must be one of: year, month, date, datetime",
                code=ValidationErrorCode.INVALID_CONFIG,
            )

        if config.minDate is not None:
            if not isinstance(config.minDate, int):
                raise FeatureValidationError(
                    "'minDate' must be a Unix timestamp (integer)",
                    code=ValidationErrorCode.INVALID_CONFIG,
                )

        if config.maxDate is not None:
            if not isinstance(config.maxDate, int):
                raise FeatureValidationError(
                    "'maxDate' must be a Unix timestamp (integer)",
                    code=ValidationErrorCode.INVALID_CONFIG,
                )

        if config.default is not None:
            if not isinstance(config.default, int):
                raise FeatureValidationError(
                    "'default' must be a Unix timestamp (integer)",
                    code=ValidationErrorCode.INVALID_CONFIG,
                )

        if config.minDate is not None and config.maxDate is not None:
            if config.minDate > config.maxDate:
                raise FeatureValidationError(
                    "'minDate' cannot be after 'maxDate'",
                    code=ValidationErrorCode.MIN_GREATER_THAN_MAX,
                )

        if config.default is not None:
            if config.minDate is not None and config.default < config.minDate:
                raise FeatureValidationError(
                    "'default' cannot be before 'minDate'",
                    code=ValidationErrorCode.INVALID_CONFIG,
                    ref_value=config.minDate,
                )
            if config.maxDate is not None and config.default > config.maxDate:
                raise FeatureValidationError(
                    "'default' cannot be after 'maxDate'",
                    code=ValidationErrorCode.INVALID_CONFIG,
                    ref_value=config.maxDate,
                )

        # Validate options
        if config.options:
            if not isinstance(config.options, list):
                raise FeatureValidationError(
                    "'options' must be a list of timestamps",
                    code=ValidationErrorCode.INVALID_CONFIG,
                )
            for idx, opt in enumerate(config.options):
                if not isinstance(opt, int):
                    raise FeatureValidationError(
                        f"Option at index {idx} must be a Unix timestamp (integer)",
                        code=ValidationErrorCode.INVALID_CONFIG,
                    )

    def validate_dto(self, config: DateConfig, dto: DateDto) -> None:
        """Validate date DTO data against configuration."""
        value = dto.value
        current_timestamp = self._get_current_timestamp()

        if value is None:
            return  # Allow None values

        if not isinstance(value, int):
            raise FeatureValidationError(
                "Date value must be a Unix timestamp (integer)",
                code=ValidationErrorCode.INVALID_TYPE,
            )

        if not config.allowFuture and value > current_timestamp:
            raise FeatureValidationError(
                "Future dates are not allowed",
                code=ValidationErrorCode.ABOVE_MAXIMUM,
                ref_value=current_timestamp,
            )

        if not config.allowPast and value < current_timestamp:
            raise FeatureValidationError(
                "Past dates are not allowed",
                code=ValidationErrorCode.BELOW_MINIMUM,
                ref_value=current_timestamp,
            )

        if config.minDate is not None and value < config.minDate:
            min_formatted = self._format_timestamp(config.minDate, config.precision)
            raise FeatureValidationError(
                f"Date cannot be before {min_formatted}",
                code=ValidationErrorCode.BELOW_MINIMUM,
                ref_value=config.minDate,
            )

        if config.maxDate is not None and value > config.maxDate:
            max_formatted = self._format_timestamp(config.maxDate, config.precision)
            raise FeatureValidationError(
                f"Date cannot be after {max_formatted}",
                code=ValidationErrorCode.ABOVE_MAXIMUM,
                ref_value=config.maxDate,
            )

    def dto_to_dao(
        self,
        config: DateConfig,
        dto: DateDto,
        feature: FeatureDef
    ) -> DateDao:
        """Convert date DTO to DAO with metadata."""
        return DateDao(
            type='date',
            value=dto.value,
            name=feature.name,
            title=feature.show_at_title,
            badge=feature.show_as_badge,
            translate=feature.translate if feature.translate != 'all' else None,
        )

    def normalize_dto(self, config: DateConfig, dto_data: Dict[str, Any]) -> DateDto:
        """Normalize date DTO data."""
        value = dto_data.get('value')

        if value is None:
            return DateDto(type='date', value=None)

        # Try to convert to int
        if isinstance(value, int):
            return DateDto(type='date', value=value)

        if isinstance(value, float):
            return DateDto(type='date', value=int(value))

        if isinstance(value, str):
            try:
                return DateDto(type='date', value=int(value))
            except ValueError:
                pass

        return DateDto(type='date', value=None)

    def get_default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            'type': self.slug,
            'precision': 'date',
            'allowFuture': True,
            'allowPast': True,
            'lockInput': False,
        }

    def get_default_value(self, config: DateConfig) -> Optional[int]:
        """Return default value for this config."""
        return config.default

    def format_value(self, config: DateConfig, dao: DateDao) -> str:
        """Format date value for display."""
        value = dao.value
        if value is None:
            return ''

        if isinstance(value, int):
            return self._format_timestamp(value, config.precision)

        return str(value)

    def get_translation_keys(self, config: DateConfig) -> List[str]:
        """Return translation keys used by this feature."""
        return ['feature.date.name']

    def get_builtin_translation_keys(self) -> List[str]:
        """Static keys this type always uses."""
        return ['feature.date.name']
