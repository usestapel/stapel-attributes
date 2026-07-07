"""Structured validation exceptions.

Replaces the legacy catalog's ``feature_validator._extract_error_info`` (which
regex-parsed human-readable ``ValidationError`` message strings back into
error codes — a known defect). Here every validation failure raised by the
engine carries its machine code, reference value and localizable params
end-to-end; the batch validators read them off the exception directly.

``FeatureValidationError`` subclasses Django's ``ValidationError`` so all
existing ``except ValidationError`` / ``pytest.raises(ValidationError)``
call sites keep working unchanged.
"""

from typing import Any, Dict, Optional

from django.core.exceptions import ValidationError

from stapel_attributes.results import ValidationErrorCode


class FeatureValidationError(ValidationError):
    """A ``ValidationError`` carrying a structured machine code.

    Attributes:
        error_code: The :class:`ValidationErrorCode` for this failure.
        ref_value: The constraint value that was violated (e.g. the ``max``
            limit, the allowed options list), when one exists.
        error_params: Extra parameters for localizable error templates.
    """

    def __init__(
        self,
        message: str,
        code: ValidationErrorCode = ValidationErrorCode.INVALID_FORMAT,
        ref_value: Any = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.error_code = code
        self.ref_value = ref_value
        self.error_params = dict(params or {})


__all__ = ['FeatureValidationError']
