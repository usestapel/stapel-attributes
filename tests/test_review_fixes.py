"""Regression tests for the attributes-admin code-review findings (B2–B7).

Each test pins one finding from tasks/fable/done/review-attributes-admin.md so a
future change can't silently reopen it. B1 (JS config-widget registry) and the
cross-language golden bridge live on the JS/vitest + tests/golden sides.
"""
import pytest
from django.core.exceptions import ValidationError

from stapel_attributes import (
    parse_config,
    validate_feature_dto,
)
from stapel_attributes.base import BaseFeatureType, FeatureDef
from stapel_attributes.exceptions import FeatureValidationError
from stapel_attributes.results import ValidationErrorCode
from stapel_attributes.validation import validate_dto, validate_dto_structured


# --------------------------------------------------------------------------- #
# B2 — select untouched defaults round-trip (declaration == engine dataclass)
# --------------------------------------------------------------------------- #

def test_b2_select_untouched_config_parses_to_declaration_defaults():
    # A select saved without touching uiStyle/maxSelected: JS omits both keys.
    # The engine must fill exactly what the untouched declaration displayed
    # (dropdown / unlimited) — no reinterpretation on the round-trip.
    from stapel_attributes.config_form import BUILTIN_FORMS

    by_name = {f.name: f for f in BUILTIN_FORMS["select"]()}
    config = parse_config({
        "type": "select",
        "options": [{"value": "a", "label": "A"}],
    })
    assert config.uiStyle == by_name["uiStyle"].default == "dropdown"
    # maxSelected: declaration carries no default (None = unlimited) == engine.
    assert by_name["maxSelected"].default is None
    assert config.maxSelected is None


# --------------------------------------------------------------------------- #
# B3 — a host runtime override of a built-in slug survives the lazy built-in load
# --------------------------------------------------------------------------- #

def test_b3_runtime_override_survives_lazy_builtin_load():
    from stapel_attributes import registry
    from stapel_attributes.types.int.config import IntConfig, IntConfigSerializer
    from stapel_attributes.types.int.dto import IntDto, IntDtoSerializer
    from stapel_attributes.types.int.dao import IntDao, IntDaoSerializer

    class HostInt(BaseFeatureType):
        slug = "int"
        name = "HostInt"
        config_class = IntConfig
        dto_class = IntDto
        dao_class = IntDao
        config_serializer_class = IntConfigSerializer
        dto_serializer_class = IntDtoSerializer
        dao_serializer_class = IntDaoSerializer

        def validate_config(self, config): ...
        def validate_dto(self, config, dto): ...
        def dto_to_dao(self, config, dto, feature): ...

    # Save + reset the loader state so we can reproduce the "host registers in
    # AppConfig.ready() before the registry is first touched" ordering.
    saved_types = dict(registry._FEATURE_TYPES)
    saved_builtins = registry._builtins_loaded
    saved_extras = set(registry._loaded_extra_paths)
    try:
        registry._FEATURE_TYPES.clear()
        registry._builtins_loaded = False
        registry._loaded_extra_paths.clear()

        # Host override registered BEFORE the built-ins are lazily loaded.
        registry.register_feature_type(HostInt)
        # First real access triggers the built-in import (int decorator fires).
        _ = registry.registered_types()

        assert isinstance(registry.get_feature_type("int"), HostInt), \
            "built-in lazy load clobbered the host override"
    finally:
        registry._FEATURE_TYPES.clear()
        registry._FEATURE_TYPES.update(saved_types)
        registry._builtins_loaded = saved_builtins
        registry._loaded_extra_paths.clear()
        registry._loaded_extra_paths.update(saved_extras)
        registry._version += 1


# --------------------------------------------------------------------------- #
# B4 — mandatory feature with an empty value is MANDATORY_MISSING, not valid
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("slug,empty", [
    ("int", None), ("float", None), ("string", None), ("string", ""),
    ("select", []), ("date", None),
])
def test_b4_structured_mandatory_empty_value_is_missing(slug, empty):
    config = {"type": slug}
    if slug == "select":
        config["options"] = [{"value": "a", "label": "A"}]
    feature = FeatureDef(slug="f", config=config, mandatory=True)
    result = validate_dto_structured([feature], {"f": {"type": slug, "value": empty}})
    assert not result.valid
    assert result.results[0].error == ValidationErrorCode.MANDATORY_MISSING


def test_b4_raise_style_mandatory_empty_value_rejected():
    feature = FeatureDef(slug="n", config={"type": "int"}, mandatory=True)
    with pytest.raises(ValidationError):
        validate_dto([feature], {"n": {"type": "int", "value": None}})


def test_b4_optional_empty_value_still_ok():
    feature = FeatureDef(slug="n", config={"type": "int"}, mandatory=False)
    result = validate_dto_structured([feature], {"n": {"type": "int", "value": None}})
    assert result.valid


# --------------------------------------------------------------------------- #
# B5 — unicode length (codepoints) + regex anchor (fullmatch)
# --------------------------------------------------------------------------- #

def test_b5_pattern_is_fullmatch_not_prefix():
    config = {"type": "string", "pattern": "[A-Z]+"}
    # fullmatch: a prefix-only match must be rejected (re.match would pass it).
    with pytest.raises(ValidationError):
        validate_feature_dto(config, {"type": "string", "value": "ABCdef"})
    # a whole-value match still passes.
    validate_feature_dto(config, {"type": "string", "value": "ABC"})


def test_b5_length_counts_codepoints():
    two_emoji = "😀😀"  # 2 code points, 4 UTF-16 units
    # minLength=3 rejects (2 code points < 3).
    with pytest.raises(ValidationError):
        validate_feature_dto({"type": "string", "minLength": 3},
                             {"type": "string", "value": two_emoji})
    # maxLength=2 accepts (2 code points).
    validate_feature_dto({"type": "string", "maxLength": 2},
                         {"type": "string", "value": two_emoji})


# --------------------------------------------------------------------------- #
# B6 — invalid config yields a localizable envelope, not a raw ErrorDetail dump
# --------------------------------------------------------------------------- #

def test_b6_invalid_config_carries_structured_field_errors():
    # A select option with a blank label (JS latch LN-C03 lets this through).
    with pytest.raises(FeatureValidationError) as exc_info:
        parse_config({
            "type": "select",
            "options": [{"value": "a", "label": ""}],
        })
    err = exc_info.value
    assert err.error_code == ValidationErrorCode.INVALID_CONFIG
    # Structured, per-field, JSON-serializable — no ErrorDetail repr in message.
    field_errors = err.error_params.get("config_errors")
    assert isinstance(field_errors, dict) and field_errors
    assert any("label" in k for k in field_errors)
    assert "ErrorDetail" not in err.messages[0]


# --------------------------------------------------------------------------- #
# B7 — header declares no `label` field (text comes from feature.name)
# --------------------------------------------------------------------------- #

def test_b7_header_form_has_no_label():
    from stapel_attributes.config_form import BUILTIN_FORMS

    names = [f.name for f in BUILTIN_FORMS["header"]()]
    assert names == ["style"]
