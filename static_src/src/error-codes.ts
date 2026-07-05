// TS mirror of stapel_attributes.results.ValidationErrorCode (py). Kept in sync
// with the engine so the npm lib (and @stapel/attributes-react on top) can map a
// structured `error` code from a FeatureValidationResult to an i18n key without
// hardcoding strings. The list is drift-gated against a committed snapshot
// generated from the Python enum: tests/golden/error_codes.json (py writes it,
// error-codes.test.ts asserts this mirror matches it exactly).
export const ValidationErrorCode = {
  // Value constraints
  BELOW_MINIMUM: "below_minimum",
  ABOVE_MAXIMUM: "above_maximum",
  NOT_IN_OPTIONS: "not_in_options",
  INVALID_TYPE: "invalid_type",
  INVALID_FORMAT: "invalid_format",

  // Feature constraints
  MANDATORY_MISSING: "mandatory_missing",
  DUPLICATE_SLUG: "duplicate_slug",
  UNKNOWN_FEATURE_TYPE: "unknown_feature_type",
  // A referenced feature slug is not permitted for this owner (e.g. a listing
  // submits a feature its category does not allow). Reused by listings/categories
  // in place of the temporary listing-local key (see follow-up: fix-catalog).
  NOT_ALLOWED: "not_allowed",
  // A referenced feature slug is unknown / undefined (distinct from
  // UNKNOWN_FEATURE_TYPE, which is an unregistered config `type`).
  UNKNOWN_FEATURE: "unknown_feature",

  // Description constraints
  DESCRIPTION_TOO_SHORT: "description_too_short",
  DESCRIPTION_TOO_LONG: "description_too_long",

  // Config validation
  INVALID_CONFIG: "invalid_config",
  MIN_GREATER_THAN_MAX: "min_greater_than_max",
  EMPTY_OPTIONS: "empty_options",
} as const;

/** A machine validation-error code emitted by the engine. */
export type ValidationErrorCode = (typeof ValidationErrorCode)[keyof typeof ValidationErrorCode];

/** All codes as a sorted array (for the py↔ts drift assertion). */
export const VALIDATION_ERROR_CODES: readonly ValidationErrorCode[] = Object.freeze(
  Object.values(ValidationErrorCode).slice().sort(),
);
