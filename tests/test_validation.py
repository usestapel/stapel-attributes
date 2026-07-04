"""Value-validation pipeline tests (DTO -> DAO).

Port of legacy-catalog ``ads/tests/test_validators.py`` — the Category/Feature
model fixture became a list of ``FeatureDef`` structures — plus coverage of
the structured validators (``ads/feature_validator.py`` in the source) and
the structured error codes that replaced regex message parsing.
"""

import pytest
from django.core.exceptions import ValidationError

from stapel_attributes.base import FeatureDef
from stapel_attributes.errors import (
    ERR_400_FEATURE_ABOVE_MAXIMUM,
    ERR_400_FEATURE_MANDATORY_MISSING,
)
from stapel_attributes.exceptions import FeatureValidationError
from stapel_attributes.results import ValidationErrorCode, ValidationStatus
from stapel_attributes.validation import (
    build_feature_lookup,
    coerce_feature_defs,
    get_feature_slug,
    normalize_to_dao,
    validate_configs_structured,
    validate_dao_structured,
    validate_description,
    validate_dto,
    validate_dto_structured,
)


@pytest.fixture
def car_features():
    """FeatureDef equivalent of the source Category-with-features fixture."""
    mileage = FeatureDef(
        slug="mileage",
        id=1,
        config={"type": "int", "min": 0, "postfix": "km", "postfix1000": "k km"},
        mandatory=False,
    )
    condition = FeatureDef(
        slug="condition",
        id=2,
        config={"type": "bool"},
        mandatory=True,
        show_as_badge=True,
    )
    return [mileage, condition]


# ============================================================================
# Raise-style pipeline (port of ads/tests/test_validators.py)
# ============================================================================

def test_validate_ok(car_features):
    # DTO format: {slug: {type: ..., value: ...}}
    payload = {
        "mileage": {"type": "int", "value": 120000},
        "condition": {"type": "bool", "value": True},
    }

    validate_dto(car_features, payload)  # no exception
    normalized = normalize_to_dao(car_features, payload)

    assert normalized["mileage"]["type"] == "int"
    assert normalized["mileage"]["value"] == 120000
    assert normalized["mileage"]["postfix"] == "km"
    assert normalized["mileage"]["postfix1000"] == "k km"

    assert normalized["condition"]["type"] == "bool"
    assert normalized["condition"]["value"] is True
    assert normalized["condition"]["badge"] is True


def test_missing_mandatory(car_features):
    payload = {"mileage": {"type": "int", "value": 1000}}

    with pytest.raises(ValidationError) as exc:
        validate_dto(car_features, payload)

    assert any("condition" in msg for msg in exc.value.messages)


def test_unknown_slug(car_features):
    payload = {
        "unknown": {"type": "int", "value": 1},
        "condition": {"type": "bool", "value": True},
    }

    with pytest.raises(ValidationError) as exc:
        validate_dto(car_features, payload)

    assert any("unknown" in msg for msg in exc.value.messages)


def test_invalid_value_type(car_features):
    payload = {
        "mileage": {"type": "int", "value": "not a number"},
        "condition": {"type": "bool", "value": True},
    }

    with pytest.raises(ValidationError) as exc:
        validate_dto(car_features, payload)

    assert any("mileage" in msg for msg in exc.value.messages)


def test_validate_none_payload_is_ok(car_features):
    validate_dto(car_features, None)  # no exception


def test_submission_by_id(car_features):
    """Features may be submitted keyed by id as well as by slug."""
    payload = {
        "1": {"type": "int", "value": 5},
        "2": {"type": "bool", "value": True},
    }
    validate_dto(car_features, payload)
    normalized = normalize_to_dao(car_features, payload)
    assert normalized["mileage"]["value"] == 5


def test_raw_value_payload(car_features):
    """A bare value (not a DTO dict) is wrapped using the config type."""
    payload = {"mileage": 42, "condition": True}
    validate_dto(car_features, payload)
    normalized = normalize_to_dao(car_features, payload)
    assert normalized["mileage"]["value"] == 42
    assert normalized["condition"]["value"] is True


def test_dao_order_and_headers_injected():
    configs = [
        FeatureDef(slug="specs", config={"type": "header", "style": "l"}),
        FeatureDef(slug="mileage", config={"type": "int"}),
    ]
    payload = {"mileage": {"type": "int", "value": 10}}

    normalized = normalize_to_dao(configs, payload)

    # Header injected without user input, with its position as order
    assert normalized["specs"]["type"] == "header"
    assert normalized["specs"]["order"] == 0
    assert normalized["mileage"]["order"] == 1


def test_empty_values_skipped_in_dao():
    configs = [
        FeatureDef(slug="color", config={"type": "string"}),
        FeatureDef(slug="tags", config={"type": "select", "options": [
            {"value": "a", "label": "A"},
        ]}),
    ]
    payload = {"color": {"type": "string", "value": ""}, "tags": {"type": "select", "value": []}}
    normalized = normalize_to_dao(configs, payload)
    assert normalized == {}


# ============================================================================
# Configs input coercion
# ============================================================================

class TestCoerceFeatureDefs:
    def test_mapping_of_bare_configs(self):
        defs = coerce_feature_defs({"mileage": {"type": "int", "min": 0}})
        assert len(defs) == 1
        assert defs[0].slug == "mileage"
        assert defs[0].config["type"] == "int"
        assert defs[0].name == "mileage"  # defaults to slug

    def test_mapping_of_feature_def_dicts(self):
        defs = coerce_feature_defs({
            "condition": {"config": {"type": "bool"}, "mandatory": True, "name": "feature.condition"},
        })
        assert defs[0].mandatory is True
        assert defs[0].name == "feature.condition"

    def test_sequence_of_dicts(self):
        defs = coerce_feature_defs([
            {"slug": "mileage", "config": {"type": "int"}, "id": 7},
        ])
        assert defs[0].id == 7

    def test_sequence_of_feature_defs_passthrough(self):
        fd = FeatureDef(slug="x", config={"type": "bool"})
        assert coerce_feature_defs([fd]) == [fd]

    def test_unsupported_value_raises(self):
        with pytest.raises(TypeError):
            coerce_feature_defs({"x": 42})

    def test_feature_def_dict_requires_config(self):
        with pytest.raises(ValueError):
            coerce_feature_defs([{"slug": "x"}])

    def test_lookup_contains_slug_and_id(self):
        lookup, ordered = build_feature_lookup([
            FeatureDef(slug="mileage", id=5, config={"type": "int"}),
        ])
        assert lookup["mileage"] is ordered[0]
        assert lookup["5"] is ordered[0]

    def test_get_feature_slug_fallbacks(self):
        assert get_feature_slug(FeatureDef(slug="s", config={})) == "s"


# ============================================================================
# Structured validators
# ============================================================================

class TestValidateDtoStructured:
    def test_all_valid(self, car_features):
        payload = {
            "mileage": {"type": "int", "value": 100},
            "condition": {"type": "bool", "value": False},
        }
        result = validate_dto_structured(car_features, payload)
        assert result.valid is True
        assert all(r.status == ValidationStatus.OK for r in result.results)

    def test_root_not_a_dict(self, car_features):
        result = validate_dto_structured(car_features, "nope")
        assert result.valid is False
        assert result.results[0].slug == "_root"
        assert result.results[0].error == ValidationErrorCode.INVALID_TYPE

    def test_unknown_features_are_ignored(self, car_features):
        payload = {
            "unknown": {"type": "int", "value": 1},
            "condition": {"type": "bool", "value": True},
            "mileage": {"type": "int", "value": 1},
        }
        result = validate_dto_structured(car_features, payload)
        assert result.valid is True
        assert {r.slug for r in result.results} == {"mileage", "condition"}

    def test_mandatory_missing(self, car_features):
        result = validate_dto_structured(car_features, {"mileage": {"type": "int", "value": 1}})
        assert result.valid is False
        failed = [r for r in result.results if r.status == ValidationStatus.VALIDATION_FAILED]
        assert len(failed) == 1
        assert failed[0].slug == "condition"
        assert failed[0].error == ValidationErrorCode.MANDATORY_MISSING
        assert failed[0].localizable_error == ERR_400_FEATURE_MANDATORY_MISSING

    def test_optional_empty_value_is_ok(self, car_features):
        payload = {
            "mileage": {"type": "int", "value": None},
            "condition": {"type": "bool", "value": True},
        }
        result = validate_dto_structured(car_features, payload)
        assert result.valid is True

    def test_structured_code_below_minimum(self):
        configs = [FeatureDef(slug="mileage", id=1, config={"type": "int", "min": 10})]
        result = validate_dto_structured(configs, {"mileage": {"type": "int", "value": 5}})
        assert result.valid is False
        row = result.results[0]
        assert row.error == ValidationErrorCode.BELOW_MINIMUM
        assert row.ref_value == 10
        assert row.params == {"feature": "mileage", "slug": "mileage"}

    def test_structured_code_above_maximum(self):
        configs = [FeatureDef(slug="mileage", config={"type": "int", "max": 100})]
        result = validate_dto_structured(configs, {"mileage": {"type": "int", "value": 200}})
        row = result.results[0]
        assert row.error == ValidationErrorCode.ABOVE_MAXIMUM
        assert row.ref_value == 100
        assert row.localizable_error == ERR_400_FEATURE_ABOVE_MAXIMUM

    def test_structured_code_not_in_options(self):
        configs = [FeatureDef(slug="doors", config={
            "type": "int", "options": [2, 4], "allowCustom": False,
        })]
        result = validate_dto_structured(configs, {"doors": {"type": "int", "value": 3}})
        row = result.results[0]
        assert row.error == ValidationErrorCode.NOT_IN_OPTIONS
        assert row.ref_value == [2, 4]

    def test_structured_code_invalid_type(self):
        configs = [FeatureDef(slug="mileage", config={"type": "int"})]
        result = validate_dto_structured(configs, {"mileage": {"type": "int", "value": "abc"}})
        row = result.results[0]
        assert row.error == ValidationErrorCode.INVALID_TYPE

    def test_structured_code_string_length(self):
        configs = [FeatureDef(slug="vin", config={"type": "string", "minLength": 5, "maxLength": 10})]
        result = validate_dto_structured(configs, {"vin": {"type": "string", "value": "abc"}})
        row = result.results[0]
        assert row.error == ValidationErrorCode.BELOW_MINIMUM
        assert row.ref_value == 5

    def test_structured_code_select_bounds(self):
        configs = [FeatureDef(slug="extras", config={
            "type": "select",
            "options": [{"value": "a", "label": "A"}, {"value": "b", "label": "B"}],
            "maxSelected": 1,
        })]
        result = validate_dto_structured(configs, {"extras": {"type": "select", "value": ["a", "b"]}})
        row = result.results[0]
        assert row.error == ValidationErrorCode.ABOVE_MAXIMUM
        assert row.ref_value == 1

    def test_plain_validation_error_degrades_to_invalid_format(self, registry_snapshot):
        """A third-party type raising a bare ValidationError still reports."""
        from stapel_attributes.tests.sample_types import LegacyFeatureType
        from stapel_attributes.registry import register_feature_type

        register_feature_type(LegacyFeatureType)

        legacy_configs = [FeatureDef(slug="x", config={"type": "legacy"})]
        result = validate_dto_structured(legacy_configs, {"x": {"value": "v"}})
        row = result.results[0]
        assert row.status == ValidationStatus.VALIDATION_FAILED
        assert row.error == ValidationErrorCode.INVALID_FORMAT
        assert row.message == "legacy message"


class TestValidateConfigsStructured:
    def test_all_valid(self, car_features):
        result = validate_configs_structured(car_features)
        assert result.valid is True

    def test_min_greater_than_max_code(self):
        configs = [FeatureDef(slug="mileage", config={"type": "int", "min": 10, "max": 1})]
        result = validate_configs_structured(configs)
        assert result.valid is False
        assert result.results[0].error == ValidationErrorCode.MIN_GREATER_THAN_MAX

    def test_empty_options_code(self):
        configs = [FeatureDef(slug="extras", config={"type": "select", "options": []})]
        result = validate_configs_structured(configs)
        assert result.results[0].error == ValidationErrorCode.EMPTY_OPTIONS

    def test_unknown_type_code(self):
        configs = [FeatureDef(slug="x", config={"type": "no_such_type"})]
        result = validate_configs_structured(configs)
        assert result.valid is False
        assert result.results[0].error == ValidationErrorCode.UNKNOWN_FEATURE_TYPE

    def test_invalid_config_shape(self):
        configs = [FeatureDef(slug="x", config={"min": 1})]  # no 'type'
        result = validate_configs_structured(configs)
        assert result.results[0].error == ValidationErrorCode.INVALID_CONFIG


class TestValidateDaoStructured:
    def test_valid_dao(self, car_features):
        dao = {
            "mileage": {"type": "int", "value": 100, "order": 0},
            "condition": {"type": "bool", "value": True, "order": 1},
        }
        result = validate_dao_structured(car_features, dao)
        assert result.valid is True

    def test_unknown_feature_in_dao(self, car_features):
        result = validate_dao_structured(car_features, {"ghost": {"type": "int", "value": 1}})
        assert result.valid is False
        assert result.results[0].error == ValidationErrorCode.UNKNOWN_FEATURE_TYPE

    def test_dao_without_type(self, car_features):
        result = validate_dao_structured(car_features, {"mileage": {"value": 1}})
        assert result.valid is False
        assert result.results[0].error == ValidationErrorCode.INVALID_FORMAT

    def test_dao_type_mismatch(self, car_features):
        result = validate_dao_structured(car_features, {"mileage": {"type": "bool", "value": True}})
        assert result.valid is False
        assert result.results[0].error == ValidationErrorCode.INVALID_TYPE

    def test_root_not_a_dict(self, car_features):
        result = validate_dao_structured(car_features, [1, 2])
        assert result.valid is False
        assert result.results[0].slug == "_root"


# ============================================================================
# Structured exceptions carry codes end-to-end (the fixed defect)
# ============================================================================

class TestStructuredExceptions:
    def test_engine_raises_feature_validation_error(self):
        from stapel_attributes.registry import validate_feature_dto

        with pytest.raises(FeatureValidationError) as exc:
            validate_feature_dto({"type": "int", "min": 10}, {"type": "int", "value": 5})
        assert exc.value.error_code == ValidationErrorCode.BELOW_MINIMUM
        assert exc.value.ref_value == 10

    def test_feature_validation_error_is_validation_error(self):
        err = FeatureValidationError("boom", code=ValidationErrorCode.INVALID_TYPE)
        assert isinstance(err, ValidationError)
        assert err.messages == ["boom"]

    def test_unknown_type_in_config_parse(self):
        from stapel_attributes.registry import parse_config

        with pytest.raises(FeatureValidationError) as exc:
            parse_config({"type": "nope"})
        assert exc.value.error_code == ValidationErrorCode.UNKNOWN_FEATURE_TYPE
        assert exc.value.ref_value == "nope"

    def test_no_regex_parsing_left(self):
        """The regex-based message parser must not be reintroduced."""
        import inspect

        import stapel_attributes.validation as validation

        source = inspect.getsource(validation)
        assert "def _extract_error_info" not in source
        assert "re.search(" not in source
        assert "import re" not in source


# ============================================================================
# Description validator
# ============================================================================

class TestValidateDescription:
    def test_ok(self):
        assert validate_description("A fine description") is None

    def test_too_short(self):
        result = validate_description("ab")
        assert result is not None
        assert result.error == ValidationErrorCode.DESCRIPTION_TOO_SHORT
        assert result.ref_value == 4
        assert result.params == {"min_length": 4, "current_length": 2}

    def test_too_long(self):
        result = validate_description("x" * 501)
        assert result is not None
        assert result.error == ValidationErrorCode.DESCRIPTION_TOO_LONG
        assert result.ref_value == 500

    def test_custom_bounds(self):
        assert validate_description("ab", min_length=2, max_length=5) is None
        result = validate_description("abcdef", min_length=2, max_length=5, slug="title")
        assert result is not None
        assert result.slug == "title"
