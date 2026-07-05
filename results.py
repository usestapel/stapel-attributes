"""Structured validation results — the machine-readable vocabulary.

Port of legacy-catalog ``ads/validation_result.py``. The enums here are the
shared vocabulary between the type plugins (which raise
:class:`stapel_attributes.exceptions.FeatureValidationError` carrying a
:class:`ValidationErrorCode`) and the batch validators in
``stapel_attributes.validation`` (which surface the codes in
:class:`FeatureValidationResult` rows).

- ``ValidationStatus``: OK or VALIDATION_FAILED
- ``ValidationErrorCode``: machine codes for every validation failure class
- ``FeatureValidationResult``: result for a single feature
- ``ValidationBatchResult``: aggregated result for multiple features
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from rest_framework import serializers


class ValidationStatus(str, Enum):
    """Status of a feature validation."""
    OK = 'ok'
    VALIDATION_FAILED = 'validation_failed'


class ValidationErrorCode(str, Enum):
    """Specific error codes for validation failures."""
    # Value constraints
    BELOW_MINIMUM = 'below_minimum'
    ABOVE_MAXIMUM = 'above_maximum'
    NOT_IN_OPTIONS = 'not_in_options'
    INVALID_TYPE = 'invalid_type'
    INVALID_FORMAT = 'invalid_format'

    # Feature constraints
    MANDATORY_MISSING = 'mandatory_missing'
    DUPLICATE_SLUG = 'duplicate_slug'
    UNKNOWN_FEATURE_TYPE = 'unknown_feature_type'
    # A referenced feature slug is not permitted for its owner (e.g. a listing
    # submits a feature its category does not allow). Canonical replacement for
    # the temporary listing-local key; reused by listings/categories.
    NOT_ALLOWED = 'not_allowed'
    # A referenced feature slug is unknown / undefined — distinct from
    # UNKNOWN_FEATURE_TYPE, which is an unregistered config ``type``.
    UNKNOWN_FEATURE = 'unknown_feature'

    # Description constraints
    DESCRIPTION_TOO_SHORT = 'description_too_short'
    DESCRIPTION_TOO_LONG = 'description_too_long'

    # Config validation (used in validate_configs)
    INVALID_CONFIG = 'invalid_config'
    MIN_GREATER_THAN_MAX = 'min_greater_than_max'
    EMPTY_OPTIONS = 'empty_options'


@dataclass
class FeatureValidationResult:
    """
    Result of validating a single feature.

    Attributes:
        id: Feature identifier (None for missing mandatory features)
        slug: Feature slug identifier
        status: OK or VALIDATION_FAILED
        error: Error code if validation failed
        ref_value: Reference value that was violated (e.g., max limit) - can be str, int, float, or list
        message: Human-readable error message
        localizable_error: Translation key for localized error (e.g., 'error.400.feature_below_minimum')
        params: Parameters for the localizable error template
    """
    slug: str
    status: ValidationStatus
    id: Optional[Union[int, str]] = None
    error: Optional[ValidationErrorCode] = None
    ref_value: Optional[Union[str, int, float, list]] = None
    message: Optional[str] = None
    localizable_error: Optional[str] = None
    params: Optional[Dict[str, Any]] = field(default_factory=dict)


class FeatureValidationResultSerializer(serializers.Serializer):
    """Serializer for FeatureValidationResult."""
    id = serializers.JSONField(required=False, allow_null=True)
    slug = serializers.CharField()
    status = serializers.ChoiceField(choices=[s.value for s in ValidationStatus])
    error = serializers.ChoiceField(
        choices=[e.value for e in ValidationErrorCode],
        required=False,
        allow_null=True
    )
    ref_value = serializers.JSONField(required=False, allow_null=True)
    message = serializers.CharField(required=False, allow_null=True)
    localizable_error = serializers.CharField(required=False, allow_null=True)
    params = serializers.DictField(required=False, allow_null=True)


@dataclass
class ValidationBatchResult:
    """
    Batch validation result for multiple features.

    Attributes:
        valid: True if all features passed validation
        results: List of individual feature validation results
    """
    valid: bool
    results: List[FeatureValidationResult]


class ValidationBatchResultSerializer(serializers.Serializer):
    """Serializer for ValidationBatchResult."""
    valid = serializers.BooleanField()
    results = FeatureValidationResultSerializer(many=True)


__all__ = [
    'ValidationStatus',
    'ValidationErrorCode',
    'FeatureValidationResult',
    'FeatureValidationResultSerializer',
    'ValidationBatchResult',
    'ValidationBatchResultSerializer',
]
