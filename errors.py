"""Localizable error keys for attribute validation failures.

Human-readable strings are translations, not response literals; API layers
surface only the ``error.<code>.<slug>`` keys plus params. The mapping from
:class:`~stapel_attributes.results.ValidationErrorCode` to these keys lives
here so every consumer (categories, listings) reports identical keys.
"""

from stapel_core.django.api.errors import register_service_errors

from stapel_attributes.results import ValidationErrorCode

ERR_400_FEATURE_BELOW_MINIMUM = "error.400.feature_below_minimum"
ERR_400_FEATURE_ABOVE_MAXIMUM = "error.400.feature_above_maximum"
ERR_400_FEATURE_NOT_IN_OPTIONS = "error.400.feature_not_in_options"
ERR_400_FEATURE_INVALID_TYPE = "error.400.feature_invalid_type"
ERR_400_FEATURE_INVALID_FORMAT = "error.400.feature_invalid_format"
ERR_400_FEATURE_MANDATORY_MISSING = "error.400.feature_mandatory_missing"
ERR_400_FEATURE_UNKNOWN_TYPE = "error.400.feature_unknown_type"
ERR_400_FEATURE_INVALID_CONFIG = "error.400.feature_invalid_config"

ERR_400_DESCRIPTION_TOO_SHORT = "error.400.description_too_short"
ERR_400_DESCRIPTION_TOO_LONG = "error.400.description_too_long"

ATTRIBUTES_ERRORS = {
    ERR_400_FEATURE_BELOW_MINIMUM: "Value is below minimum for {feature}",
    ERR_400_FEATURE_ABOVE_MAXIMUM: "Value is above maximum for {feature}",
    ERR_400_FEATURE_NOT_IN_OPTIONS: "Value is not in allowed options for {feature}",
    ERR_400_FEATURE_INVALID_TYPE: "Invalid type for {feature}",
    ERR_400_FEATURE_INVALID_FORMAT: "Invalid format for {feature}",
    ERR_400_FEATURE_MANDATORY_MISSING: "Mandatory feature {feature} is required",
    ERR_400_FEATURE_UNKNOWN_TYPE: "Unknown feature type for {feature}",
    ERR_400_FEATURE_INVALID_CONFIG: "Invalid config for {feature}",
    ERR_400_DESCRIPTION_TOO_SHORT: "Description must be at least {min_length} characters",
    ERR_400_DESCRIPTION_TOO_LONG: "Description must be at most {max_length} characters",
}

register_service_errors(ATTRIBUTES_ERRORS)

# ValidationErrorCode -> localizable error key
ERROR_CODE_TO_KEY = {
    ValidationErrorCode.BELOW_MINIMUM: ERR_400_FEATURE_BELOW_MINIMUM,
    ValidationErrorCode.ABOVE_MAXIMUM: ERR_400_FEATURE_ABOVE_MAXIMUM,
    ValidationErrorCode.NOT_IN_OPTIONS: ERR_400_FEATURE_NOT_IN_OPTIONS,
    ValidationErrorCode.INVALID_TYPE: ERR_400_FEATURE_INVALID_TYPE,
    ValidationErrorCode.INVALID_FORMAT: ERR_400_FEATURE_INVALID_FORMAT,
    ValidationErrorCode.MANDATORY_MISSING: ERR_400_FEATURE_MANDATORY_MISSING,
    ValidationErrorCode.DUPLICATE_SLUG: ERR_400_FEATURE_UNKNOWN_TYPE,
    ValidationErrorCode.UNKNOWN_FEATURE_TYPE: ERR_400_FEATURE_UNKNOWN_TYPE,
    ValidationErrorCode.INVALID_CONFIG: ERR_400_FEATURE_INVALID_CONFIG,
    ValidationErrorCode.MIN_GREATER_THAN_MAX: ERR_400_FEATURE_INVALID_CONFIG,
    ValidationErrorCode.EMPTY_OPTIONS: ERR_400_FEATURE_INVALID_CONFIG,
    ValidationErrorCode.DESCRIPTION_TOO_SHORT: ERR_400_DESCRIPTION_TOO_SHORT,
    ValidationErrorCode.DESCRIPTION_TOO_LONG: ERR_400_DESCRIPTION_TOO_LONG,
}

__all__ = [
    "ATTRIBUTES_ERRORS",
    "ERROR_CODE_TO_KEY",
    "ERR_400_FEATURE_BELOW_MINIMUM",
    "ERR_400_FEATURE_ABOVE_MAXIMUM",
    "ERR_400_FEATURE_NOT_IN_OPTIONS",
    "ERR_400_FEATURE_INVALID_TYPE",
    "ERR_400_FEATURE_INVALID_FORMAT",
    "ERR_400_FEATURE_MANDATORY_MISSING",
    "ERR_400_FEATURE_UNKNOWN_TYPE",
    "ERR_400_FEATURE_INVALID_CONFIG",
    "ERR_400_DESCRIPTION_TOO_SHORT",
    "ERR_400_DESCRIPTION_TOO_LONG",
]
