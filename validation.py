"""The value-validation pipeline (DTO -> DAO).

Port of the legacy catalog's ``ads/validators.py`` + ``ads/feature_validator.py``,
decoupled from Django models: every function takes *configs* — an iterable of
:class:`~stapel_attributes.base.FeatureDef` (or dicts / a ``{slug: ...}``
mapping coerced via :func:`coerce_feature_defs`) — instead of a Category
model. The owning module (stapel-categories) or a comm consumer
(stapel-listings) materializes the configs and calls in.

Pipeline:
1. Input: ``{slug: DTO}`` — user submits feature values
2. Validation: check mandatory, allowed features, type constraints
3. Normalization: DTO -> validated DTO dataclass
4. Transform: DTO -> DAO with metadata from the feature definition
5. Headers: auto-inject header DAOs from configs (not user-editable)

Fixed while porting (do not reintroduce):

- ``_extract_error_info`` regex-parsed ValidationError message strings; the
  engine now raises :class:`FeatureValidationError` carrying machine codes,
  and the batch validators read them off the exception directly. Feature
  types MUST raise ``FeatureValidationError`` — a bare ``ValidationError``
  from a type plugin is a contract violation and propagates.
- ``_get_feature_slug`` / ``_build_feature_lookup`` were duplicated across
  three source files; :func:`get_feature_slug` / :func:`build_feature_lookup`
  are the single copies.
"""

from dataclasses import is_dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple, Union

from django.core.exceptions import ValidationError

from stapel_attributes.base import FeatureDef, dataclass_to_dict_no_none
from stapel_attributes.errors import ERROR_CODE_TO_KEY
from stapel_attributes.exceptions import FeatureValidationError
from stapel_attributes.registry import (
    get_feature_type,
    normalize_feature_dto,
    parse_config,
    validate_feature_dto,
)
from stapel_attributes.registry import dto_to_dao as registry_dto_to_dao
from stapel_attributes.results import (
    FeatureValidationResult,
    ValidationBatchResult,
    ValidationErrorCode,
    ValidationStatus,
)

ConfigsInput = Union[
    Iterable[Union[FeatureDef, Dict[str, Any]]],
    Mapping[str, Union[FeatureDef, Dict[str, Any]]],
]


def coerce_feature_defs(configs: ConfigsInput) -> List[FeatureDef]:
    """Coerce the accepted *configs* shapes into a list of FeatureDef.

    Accepted:
    - an iterable of ``FeatureDef`` instances,
    - an iterable of feature-def dicts (``{"slug": ..., "config": {...}, ...}``),
    - a mapping ``{slug: FeatureDef | feature-def dict | bare config dict}``
      (a bare config dict is recognized by its ``type`` discriminator).

    Order is preserved — it becomes the DAO ``order``.
    """
    defs: List[FeatureDef] = []
    if isinstance(configs, Mapping):
        for slug, value in configs.items():
            if isinstance(value, FeatureDef):
                defs.append(value)
            elif isinstance(value, dict) and 'config' in value:
                defs.append(FeatureDef.from_dict(value, slug=str(slug)))
            elif isinstance(value, dict):
                defs.append(FeatureDef(slug=str(slug), config=value))
            else:
                raise TypeError(f"Unsupported feature definition for '{slug}': {value!r}")
        return defs

    for value in configs:
        if isinstance(value, FeatureDef):
            defs.append(value)
        elif isinstance(value, dict):
            defs.append(FeatureDef.from_dict(value))
        else:
            raise TypeError(f"Unsupported feature definition: {value!r}")
    return defs


def get_feature_slug(feature: FeatureDef) -> str:
    """
    Derive the slug for a feature definition to match incoming payload keys.
    Falls back to name, then id, if no slug is available.
    """
    if feature.slug:
        return str(feature.slug)
    if feature.name:
        return str(feature.name)
    return str(feature.id)


def build_feature_lookup(
    configs: ConfigsInput,
) -> Tuple[Dict[str, FeatureDef], List[FeatureDef]]:
    """
    Build lookup dict and ordered list of feature definitions.

    Returns:
        Tuple of (lookup dict keyed by slug and id, ordered list of FeatureDef)
    """
    allowed_features = coerce_feature_defs(configs)
    lookup: Dict[str, FeatureDef] = {}
    for feature in allowed_features:
        slug = get_feature_slug(feature)
        if feature.id is not None:
            lookup[str(feature.id)] = feature
        lookup[slug] = feature
    return lookup, allowed_features


# =============================================================================
# Raise-style pipeline (port of ads/validators.py)
# =============================================================================


def validate_dto(configs: ConfigsInput, features_dto: Optional[Dict[str, Any]]) -> None:
    """
    Validate a feature DTO payload against the feature definitions.

    Input format: ``{slug: {type: "...", value: ...}}``

    Rules:
    1) All mandatory features must have a value (except headers)
    2) No features that are not in *configs*
    3) Values must be valid per type and constraints
    4) Header features should NOT be submitted (they're auto-generated)

    Raises:
        ValidationError: with one message per offending feature.
    """
    if features_dto is None:
        return
    if not isinstance(features_dto, dict):
        raise FeatureValidationError(
            "features must be an object keyed by feature slug",
            code=ValidationErrorCode.INVALID_TYPE,
        )

    lookup, allowed_features = build_feature_lookup(configs)
    errors: Dict[str, str] = {}

    # Validate submitted features
    for key, dto_data in features_dto.items():
        feature_key = str(key)
        feature = lookup.get(feature_key)

        if not feature:
            errors[feature_key] = f"Feature '{feature_key}' is not allowed"
            continue

        # Parse config to typed dataclass
        try:
            config = parse_config(feature.config)
        except ValidationError as exc:
            errors[feature_key] = f"Feature '{feature.name}' has invalid config: {exc}"
            continue

        # Skip header check - they're auto-generated
        if config.type == 'header':
            continue

        # Validate DTO structure and value
        try:
            # Normalize DTO: always set type from config (authoritative source)
            if not isinstance(dto_data, dict):
                dto_data = {'type': config.type, 'value': dto_data}
            else:
                dto_data = {**dto_data, 'type': config.type}

            validate_feature_dto(config, dto_data)
        except ValidationError as exc:
            errors[feature_key] = exc.messages[0] if hasattr(exc, "messages") else str(exc)
        except (TypeError, KeyError, AttributeError, ValueError, IndexError) as exc:
            errors[feature_key] = f"Invalid value for feature '{feature.name}': {exc}"

    # Check mandatory features (except headers)
    for feature in allowed_features:
        # Parse config to typed dataclass
        try:
            config = parse_config(feature.config)
        except ValidationError:
            # Already reported above if feature was submitted
            continue

        # Skip header check - they're auto-generated
        if config.type == 'header':
            continue

        slug = get_feature_slug(feature)
        submitted_value = features_dto.get(slug)
        if submitted_value is None and feature.id is not None:
            submitted_value = features_dto.get(str(feature.id))
        submitted = slug in features_dto or (
            feature.id is not None and str(feature.id) in features_dto
        )
        # B4: mandatory means "present with a non-empty value". A submitted
        # empty value (null / '' / []) is treated as missing — otherwise it
        # normalizes to a valid-but-empty value and is dropped from the DAO.
        raw = submitted_value.get('value') if isinstance(submitted_value, dict) else submitted_value
        is_empty = raw is None or raw == '' or raw == []
        if feature.mandatory and (not submitted or is_empty):
            errors[slug] = f"Mandatory feature '{feature.name}' is required"

    if errors:
        # Raise as list to avoid Django trying to map to form fields
        error_messages = [f"{field}: {msg}" if isinstance(msg, str) else f"{field}: {msg[0]}"
                          for field, msg in errors.items()]
        raise ValidationError(error_messages)


def normalize_to_dao(
    configs: ConfigsInput,
    features_dto: Optional[Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    """
    Transform DTO input to DAO output with headers injected.

    Pipeline:
    1. Normalize each submitted DTO
    2. Convert DTO -> DAO with metadata from the feature definition
    3. Inject header DAOs from configs (with order)

    Input: ``{slug: {type: "...", value: ...}}``
    Output: ``{slug: {type: "...", value: ..., order: N, title: bool, badge: bool, ...}}``

    Headers are injected based on their position in the configs list.
    """
    if not features_dto:
        features_dto = {}

    lookup, allowed_features = build_feature_lookup(configs)
    result: Dict[str, Dict[str, Any]] = {}

    # Process features in configs order to maintain proper ordering
    for order, feature in enumerate(allowed_features):
        slug = get_feature_slug(feature)
        # Parse config to typed dataclass
        try:
            config = parse_config(feature.config)
        except ValidationError:
            # Skip features with invalid config (should have been caught in validation)
            continue

        # Handle headers - auto-generate from config
        if config.type == 'header':
            feature_type = get_feature_type('header')
            # Create DAO directly from config (no user input)
            header_dto = feature_type.dto_class(type='header', value=None)
            dao = feature_type.dto_to_dao(config, header_dto, feature)
            dao_dict = _dao_to_dict(dao)
            dao_dict['order'] = order
            result[slug] = dao_dict
            continue

        # Find submitted DTO for this feature
        dto_data = features_dto.get(slug)
        if dto_data is None and feature.id is not None:
            dto_data = features_dto.get(str(feature.id))

        if dto_data is None:
            # Feature not submitted - skip (mandatory check done in validation)
            continue

        # Normalize DTO: always set type from config (authoritative source)
        if not isinstance(dto_data, dict):
            dto_data = {'type': config.type, 'value': dto_data}
        else:
            dto_data = {**dto_data, 'type': config.type}

        # Skip features without value - only include features with actual values in DAO
        # Also skip empty values (empty string, empty list, None)
        value = dto_data.get('value')
        if value is None or value == '' or value == []:
            continue

        # Normalize DTO (returns typed dataclass)
        try:
            normalized_dto = normalize_feature_dto(config, dto_data)

            # Convert to DAO (uses typed config and DTO)
            dao = registry_dto_to_dao(config, normalized_dto, feature)
            dao_dict = _dao_to_dict(dao)
            dao_dict['order'] = order

            result[slug] = dao_dict
        except (ValidationError, TypeError, KeyError, AttributeError, ValueError, IndexError):
            # Skip features that fail normalization (should have been caught in validation)
            continue

    return result


def _dao_to_dict(dao: Any) -> Dict[str, Any]:
    """Convert DAO (dataclass or dict) to dict, excluding None values."""
    if isinstance(dao, dict):
        return {k: v for k, v in dao.items() if v is not None}
    if is_dataclass(dao) and not isinstance(dao, type):
        return dataclass_to_dict_no_none(dao)
    return dao


# =============================================================================
# Structured pipeline (port of ads/feature_validator.py)
# =============================================================================


def validate_dto_structured(
    configs: ConfigsInput,
    features_dto: Optional[Dict[str, Any]],
) -> ValidationBatchResult:
    """
    Validate a features DTO payload with structured output.

    Behavior:
    - Validates each submitted feature against its config
    - Checks all mandatory features are present
    - Ignores features not in *configs* (no error, just skip)

    Args:
        configs: Feature definitions (see :func:`coerce_feature_defs`)
        features_dto: ``{slug: {type, value, ...}}``

    Returns:
        ValidationBatchResult with individual feature results
    """
    if features_dto is None:
        features_dto = {}

    if not isinstance(features_dto, dict):
        return ValidationBatchResult(
            valid=False,
            results=[
                FeatureValidationResult(
                    slug='_root',
                    status=ValidationStatus.VALIDATION_FAILED,
                    error=ValidationErrorCode.INVALID_TYPE,
                    localizable_error=ERROR_CODE_TO_KEY[ValidationErrorCode.INVALID_TYPE],
                    params={'feature': '_root'},
                    message="features must be an object keyed by feature slug"
                )
            ]
        )

    lookup, allowed_features = build_feature_lookup(configs)
    results: List[FeatureValidationResult] = []
    all_valid = True

    # Track which features were submitted
    submitted_slugs = set()

    # Validate submitted features
    for key, dto_data in features_dto.items():
        feature_key = str(key)
        feature = lookup.get(feature_key)

        # Ignore unknown features (not an error per requirements)
        if not feature:
            continue

        slug = get_feature_slug(feature)
        submitted_slugs.add(slug)
        if feature.id is not None:
            submitted_slugs.add(str(feature.id))

        # Parse config to typed dataclass
        try:
            config = parse_config(feature.config)
        except ValidationError as exc:
            results.append(FeatureValidationResult(
                id=feature.id,
                slug=slug,
                status=ValidationStatus.VALIDATION_FAILED,
                error=ValidationErrorCode.INVALID_CONFIG,
                localizable_error=ERROR_CODE_TO_KEY[ValidationErrorCode.INVALID_CONFIG],
                params={'feature': feature.name, 'slug': slug},
                message=f"Feature '{feature.name}' has invalid config: {exc}"
            ))
            all_valid = False
            continue

        # Skip header - they're auto-generated
        if config.type == 'header':
            continue

        # B4: a mandatory feature submitted with an empty value (null / '' / [])
        # is *missing*, not valid. Without this, normalization coerces the empty
        # value into a valid one (int None->0, string None->'', select None->[],
        # date None allowed) so validation passes, yet normalize_to_dao then
        # drops the empty value — the mandatory feature silently vanishes from
        # the DAO. JS is not the source of truth (docs §4), so reject here.
        raw_value = dto_data.get('value') if isinstance(dto_data, dict) else dto_data
        is_empty = raw_value is None or raw_value == '' or raw_value == []
        if not feature.mandatory and is_empty:
            results.append(FeatureValidationResult(
                id=feature.id,
                slug=slug,
                status=ValidationStatus.OK
            ))
            continue
        if feature.mandatory and is_empty:
            results.append(FeatureValidationResult(
                id=feature.id,
                slug=slug,
                status=ValidationStatus.VALIDATION_FAILED,
                error=ValidationErrorCode.MANDATORY_MISSING,
                localizable_error=ERROR_CODE_TO_KEY[ValidationErrorCode.MANDATORY_MISSING],
                params={'feature': feature.name, 'slug': slug},
                message=f"Mandatory feature '{feature.name}' is required"
            ))
            all_valid = False
            continue

        # Validate DTO structure and value
        try:
            # Normalize DTO: always set type from config (authoritative source)
            if not isinstance(dto_data, dict):
                dto_data = {'type': config.type, 'value': dto_data}
            else:
                dto_data = {**dto_data, 'type': config.type}

            # Get feature type for validation
            feature_type = get_feature_type(config.type)

            # Normalize DTO
            dto = feature_type.normalize_dto(config, dto_data)

            # Validate DTO
            feature_type.validate_dto(config, dto)

            # Success
            results.append(FeatureValidationResult(
                id=feature.id,
                slug=slug,
                status=ValidationStatus.OK
            ))

        except FeatureValidationError as exc:
            results.append(FeatureValidationResult(
                id=feature.id,
                slug=slug,
                status=ValidationStatus.VALIDATION_FAILED,
                error=exc.error_code,
                ref_value=exc.ref_value,
                localizable_error=ERROR_CODE_TO_KEY.get(exc.error_code),
                params={'feature': feature.name, 'slug': slug},
                message=exc.messages[0] if exc.messages else str(exc)
            ))
            all_valid = False

        except (TypeError, KeyError, AttributeError, ValueError, IndexError) as exc:
            results.append(FeatureValidationResult(
                id=feature.id,
                slug=slug,
                status=ValidationStatus.VALIDATION_FAILED,
                error=ValidationErrorCode.INVALID_TYPE,
                localizable_error=ERROR_CODE_TO_KEY[ValidationErrorCode.INVALID_TYPE],
                params={'feature': feature.name, 'slug': slug},
                message=f"Invalid value for feature '{feature.name}': {exc}"
            ))
            all_valid = False

    # Check mandatory features (except headers)
    for feature in allowed_features:
        slug = get_feature_slug(feature)

        # Skip if already validated
        if slug in submitted_slugs or (feature.id is not None and str(feature.id) in submitted_slugs):
            continue

        # Parse config to typed dataclass
        try:
            config = parse_config(feature.config)
        except ValidationError:
            # Already reported above if feature was submitted
            continue

        # Skip header - they're auto-generated
        if config.type == 'header':
            continue

        # Check if mandatory
        if feature.mandatory:
            results.append(FeatureValidationResult(
                id=feature.id,
                slug=slug,
                status=ValidationStatus.VALIDATION_FAILED,
                error=ValidationErrorCode.MANDATORY_MISSING,
                localizable_error=ERROR_CODE_TO_KEY[ValidationErrorCode.MANDATORY_MISSING],
                params={'feature': feature.name, 'slug': slug},
                message=f"Mandatory feature '{feature.name}' is required"
            ))
            all_valid = False

    return ValidationBatchResult(valid=all_valid, results=results)


def validate_configs_structured(configs: ConfigsInput) -> ValidationBatchResult:
    """
    Validate all feature configs in a set of feature definitions.

    Used when saving the owning entity (e.g. a category) to ensure configs
    are valid.

    Args:
        configs: Feature definitions (see :func:`coerce_feature_defs`)

    Returns:
        ValidationBatchResult with individual feature results
    """
    _, allowed_features = build_feature_lookup(configs)
    results: List[FeatureValidationResult] = []
    all_valid = True

    for feature in allowed_features:
        slug = get_feature_slug(feature)

        try:
            config = parse_config(feature.config)

            # Get feature type and validate config
            feature_type = get_feature_type(config.type)
            feature_type.validate_config(config)

            results.append(FeatureValidationResult(
                id=feature.id,
                slug=slug,
                status=ValidationStatus.OK
            ))

        except FeatureValidationError as exc:
            results.append(FeatureValidationResult(
                id=feature.id,
                slug=slug,
                status=ValidationStatus.VALIDATION_FAILED,
                error=exc.error_code,
                ref_value=exc.ref_value,
                localizable_error=ERROR_CODE_TO_KEY.get(exc.error_code),
                params={'feature': feature.name, 'slug': slug},
                message=exc.messages[0] if exc.messages else str(exc)
            ))
            all_valid = False

        except ValueError as exc:
            # Unknown feature type
            results.append(FeatureValidationResult(
                id=feature.id,
                slug=slug,
                status=ValidationStatus.VALIDATION_FAILED,
                error=ValidationErrorCode.UNKNOWN_FEATURE_TYPE,
                localizable_error=ERROR_CODE_TO_KEY[ValidationErrorCode.UNKNOWN_FEATURE_TYPE],
                params={'feature': feature.name, 'slug': slug},
                message=str(exc)
            ))
            all_valid = False

    return ValidationBatchResult(valid=all_valid, results=results)


def validate_dao_structured(
    configs: ConfigsInput,
    features_dao: Optional[Dict[str, Any]],
) -> ValidationBatchResult:
    """
    Validate stored DAO data integrity.

    Used for integrity checks on stored data.

    Args:
        configs: Feature definitions (see :func:`coerce_feature_defs`)
        features_dao: ``{slug: {type, value, ...}}``

    Returns:
        ValidationBatchResult with individual feature results
    """
    if features_dao is None:
        features_dao = {}

    if not isinstance(features_dao, dict):
        return ValidationBatchResult(
            valid=False,
            results=[
                FeatureValidationResult(
                    slug='_root',
                    status=ValidationStatus.VALIDATION_FAILED,
                    error=ValidationErrorCode.INVALID_TYPE,
                    localizable_error=ERROR_CODE_TO_KEY[ValidationErrorCode.INVALID_TYPE],
                    params={'feature': '_root'},
                    message="features must be an object keyed by feature slug"
                )
            ]
        )

    lookup, allowed_features = build_feature_lookup(configs)
    results: List[FeatureValidationResult] = []
    all_valid = True

    # Validate stored features
    for key, dao_data in features_dao.items():
        feature_key = str(key)
        feature = lookup.get(feature_key)

        if not feature:
            # Feature in DAO but not in configs - might be removed
            results.append(FeatureValidationResult(
                id=None,
                slug=feature_key,
                status=ValidationStatus.VALIDATION_FAILED,
                error=ValidationErrorCode.UNKNOWN_FEATURE_TYPE,
                localizable_error=ERROR_CODE_TO_KEY[ValidationErrorCode.UNKNOWN_FEATURE_TYPE],
                params={'feature': feature_key},
                message=f"Feature '{feature_key}' not found in configs"
            ))
            all_valid = False
            continue

        slug = get_feature_slug(feature)

        # Check DAO has type
        if not isinstance(dao_data, dict) or 'type' not in dao_data:
            results.append(FeatureValidationResult(
                id=feature.id,
                slug=slug,
                status=ValidationStatus.VALIDATION_FAILED,
                error=ValidationErrorCode.INVALID_FORMAT,
                localizable_error=ERROR_CODE_TO_KEY[ValidationErrorCode.INVALID_FORMAT],
                params={'feature': feature.name, 'slug': slug},
                message="DAO must have a 'type' field"
            ))
            all_valid = False
            continue

        # Verify type matches config
        try:
            config = parse_config(feature.config)
            if dao_data['type'] != config.type:
                results.append(FeatureValidationResult(
                    id=feature.id,
                    slug=slug,
                    status=ValidationStatus.VALIDATION_FAILED,
                    error=ValidationErrorCode.INVALID_TYPE,
                    localizable_error=ERROR_CODE_TO_KEY[ValidationErrorCode.INVALID_TYPE],
                    params={'feature': feature.name, 'slug': slug},
                    message=f"DAO type '{dao_data['type']}' doesn't match config type '{config.type}'"
                ))
                all_valid = False
                continue

            results.append(FeatureValidationResult(
                id=feature.id,
                slug=slug,
                status=ValidationStatus.OK
            ))

        except ValidationError as exc:
            results.append(FeatureValidationResult(
                id=feature.id,
                slug=slug,
                status=ValidationStatus.VALIDATION_FAILED,
                error=ValidationErrorCode.INVALID_CONFIG,
                localizable_error=ERROR_CODE_TO_KEY[ValidationErrorCode.INVALID_CONFIG],
                params={'feature': feature.name, 'slug': slug},
                message=str(exc)
            ))
            all_valid = False

    return ValidationBatchResult(valid=all_valid, results=results)


# =============================================================================
# Generic text-length validator (port of validate_description)
# =============================================================================

DESCRIPTION_MIN_LENGTH = 4
DESCRIPTION_MAX_LENGTH = 500


def validate_description(
    description: Optional[str],
    min_length: int = DESCRIPTION_MIN_LENGTH,
    max_length: int = DESCRIPTION_MAX_LENGTH,
    slug: str = 'description',
) -> Optional[FeatureValidationResult]:
    """
    Validate free-text length (default 4-500 characters).

    Returns a FeatureValidationResult if validation fails, None if OK.
    """
    text = (description or '').strip()
    length = len(text)

    if length < min_length:
        return FeatureValidationResult(
            slug=slug,
            status=ValidationStatus.VALIDATION_FAILED,
            error=ValidationErrorCode.DESCRIPTION_TOO_SHORT,
            ref_value=min_length,
            localizable_error=ERROR_CODE_TO_KEY[ValidationErrorCode.DESCRIPTION_TOO_SHORT],
            params={'min_length': min_length, 'current_length': length},
            message=f"Description must be at least {min_length} characters (currently {length})",
        )

    if length > max_length:
        return FeatureValidationResult(
            slug=slug,
            status=ValidationStatus.VALIDATION_FAILED,
            error=ValidationErrorCode.DESCRIPTION_TOO_LONG,
            ref_value=max_length,
            localizable_error=ERROR_CODE_TO_KEY[ValidationErrorCode.DESCRIPTION_TOO_LONG],
            params={'max_length': max_length, 'current_length': length},
            message=f"Description must be at most {max_length} characters (currently {length})",
        )

    return None


__all__ = [
    'coerce_feature_defs',
    'get_feature_slug',
    'build_feature_lookup',
    'validate_dto',
    'normalize_to_dao',
    'validate_dto_structured',
    'validate_configs_structured',
    'validate_dao_structured',
    'validate_description',
    'DESCRIPTION_MIN_LENGTH',
    'DESCRIPTION_MAX_LENGTH',
]
