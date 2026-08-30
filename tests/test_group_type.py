"""The composite (``group``) type — a repeatable subform of child features.

Covers the config boundaries (depth 1, no headers, no child rules, unique
slugs, repeat bounds), per-row validation delegated to each child's own type,
the DAO shape (rows of child DAOs carrying child DaoMeta), and the pipeline
end-to-end. The worked example is Avito's ``DiscountLadderList``: "quantity
from N, discount M %", up to five rows — the shape 2 468 raw Avito fields
carry and no other kind could express.
"""
import pytest

from stapel_attributes import (
    format_feature_value,
    get_feature_type,
    parse_config,
    validate_feature_config,
)
from stapel_attributes.base import FeatureDef
from stapel_attributes.exceptions import FeatureValidationError
from stapel_attributes.results import ValidationErrorCode, ValidationStatus
from stapel_attributes.tests.fake_vocabulary import FakeVocabularyResolver
from stapel_attributes.types.group import GroupConfig, GroupDto
from stapel_attributes.validation import (
    normalize_to_dao,
    validate_configs_structured,
    validate_dto,
    validate_dto_structured,
)
from stapel_attributes.vocabularies import register_vocabulary_resolver


# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------

#: Sentinel: `repeat=None` is a meaningful value (a single-row group).
_DEFAULT_REPEAT = object()


def ladder_config(repeat=_DEFAULT_REPEAT):
    """The DiscountLadderList shape: quantity threshold + discount percent."""
    return {
        "type": "group",
        "fields": [
            {
                "slug": "wholesale_ladder_count_discount",
                "name": "Quantity for discount",
                "mandatory": True,
                "config": {"type": "int", "min": 1, "max": 10000000},
                "description": "Discount threshold",
                "example": "100",
            },
            {
                "slug": "wholesale_ladder_discount",
                "name": "Discount percent",
                "config": {"type": "int", "min": 1, "max": 30, "postfix": "%"},
                "example": "5",
            },
        ],
        "repeat": {"min": 1, "max": 5} if repeat is _DEFAULT_REPEAT else repeat,
    }


def ladder_feature(repeat=_DEFAULT_REPEAT, mandatory=False):
    return {
        "slug": "discount_ladder_list",
        "name": "Wholesale discount ladder",
        "mandatory": mandatory,
        "config": ladder_config(repeat),
    }


@pytest.fixture
def resolver():
    instance = FakeVocabularyResolver()
    register_vocabulary_resolver(instance)
    yield instance
    register_vocabulary_resolver(None)


# ---------------------------------------------------------------------------
# registration
# ---------------------------------------------------------------------------

def test_group_is_a_registered_builtin():
    from stapel_attributes import get_all_type_slugs

    assert "group" in get_all_type_slugs()
    assert get_feature_type("group").slug == "group"


def test_default_config_is_an_empty_single_row_group():
    assert get_feature_type("group").get_default_config() == {
        "type": "group",
        "fields": [],
        "repeat": None,
    }


def test_parse_config_keeps_children_verbatim():
    config = parse_config(ladder_config())
    assert isinstance(config, GroupConfig)
    assert [f["slug"] for f in config.fields] == [
        "wholesale_ladder_count_discount",
        "wholesale_ladder_discount",
    ]
    assert config.fields[0]["config"] == {"type": "int", "min": 1, "max": 10000000}
    assert config.repeat == {"min": 1, "max": 5}


def test_repeat_null_parses_and_means_one_row():
    config = validate_feature_config({**ladder_config(), "repeat": None})
    assert config.repeat is None


# ---------------------------------------------------------------------------
# config validation — the v1 boundaries
# ---------------------------------------------------------------------------

def test_valid_config_passes():
    config = validate_feature_config(ladder_config())
    assert config.type == "group"


def test_fields_cannot_be_empty():
    with pytest.raises(FeatureValidationError) as exc:
        validate_feature_config({"type": "group", "fields": []})
    assert exc.value.error_code == ValidationErrorCode.INVALID_CONFIG


def test_a_child_must_be_a_feature_definition():
    with pytest.raises(FeatureValidationError) as exc:
        validate_feature_config({"type": "group", "fields": [{"slug": "a"}]})
    assert exc.value.error_code == ValidationErrorCode.INVALID_CONFIG
    assert "requires a 'config'" in str(exc.value)


def test_duplicate_child_slugs_are_rejected():
    with pytest.raises(FeatureValidationError) as exc:
        validate_feature_config({
            "type": "group",
            "fields": [
                {"slug": "a", "config": {"type": "int"}},
                {"slug": "a", "config": {"type": "string"}},
            ],
        })
    assert exc.value.error_code == ValidationErrorCode.DUPLICATE_SLUG
    assert exc.value.ref_value == "a"


def test_a_group_cannot_contain_a_group():
    nested = {
        "type": "group",
        "fields": [{
            "slug": "inner",
            "config": {"type": "group", "fields": [{"slug": "x", "config": {"type": "int"}}]},
        }],
    }
    with pytest.raises(FeatureValidationError) as exc:
        validate_feature_config(nested)
    assert exc.value.error_code == ValidationErrorCode.INVALID_CONFIG
    assert exc.value.ref_value == "group"
    assert "nesting depth is 1" in str(exc.value)


def test_a_group_cannot_contain_a_header():
    with pytest.raises(FeatureValidationError) as exc:
        validate_feature_config({
            "type": "group",
            "fields": [{"slug": "h", "config": {"type": "header", "label": "x"}}],
        })
    assert exc.value.error_code == ValidationErrorCode.INVALID_CONFIG
    assert exc.value.ref_value == "header"


def test_a_child_carrying_rules_is_rejected_loudly():
    """A rule on a child could never fire — the rule engine reads top-level
    slugs — so it is refused rather than silently ignored."""
    with pytest.raises(FeatureValidationError) as exc:
        validate_feature_config({
            "type": "group",
            "fields": [{
                "slug": "a",
                "config": {"type": "int"},
                "rules": [{"effect": "require", "when": {"all": [
                    {"feature": "b", "op": "filled"}]}}],
            }],
        })
    assert exc.value.error_code == ValidationErrorCode.INVALID_CONFIG
    assert "rules on a group child are not supported" in str(exc.value)


def test_a_childs_own_config_is_validated():
    with pytest.raises(FeatureValidationError) as exc:
        validate_feature_config({
            "type": "group",
            "fields": [{"slug": "a", "config": {"type": "int", "min": 10, "max": 1}}],
        })
    assert exc.value.error_code == ValidationErrorCode.MIN_GREATER_THAN_MAX


def test_repeat_max_below_min_is_rejected():
    with pytest.raises(FeatureValidationError) as exc:
        validate_feature_config(ladder_config(repeat={"min": 3, "max": 2}))
    assert exc.value.error_code == ValidationErrorCode.MIN_GREATER_THAN_MAX


def test_repeat_max_zero_is_rejected():
    with pytest.raises(FeatureValidationError) as exc:
        validate_feature_config(ladder_config(repeat={"min": 0, "max": 0}))
    assert exc.value.error_code == ValidationErrorCode.INVALID_CONFIG


def test_a_rule_on_the_group_itself_is_accepted():
    """Conditional behaviour for a composite lives outside it (spec §1.1)."""
    feature = {
        **ladder_feature(),
        "rules": [{"effect": "require", "when": {"all": [
            {"feature": "wholesale", "op": "in", "values": ["true"]}]}}],
    }
    result = validate_configs_structured([feature], known_slugs={"discount_ladder_list", "wholesale"})
    assert result.valid


# ---------------------------------------------------------------------------
# value validation
# ---------------------------------------------------------------------------

def rows(*values):
    return {"type": "group", "value": list(values)}


def test_valid_rows_pass():
    payload = {"discount_ladder_list": rows(
        {"wholesale_ladder_count_discount": 10, "wholesale_ladder_discount": 15},
        {"wholesale_ladder_count_discount": 20, "wholesale_ladder_discount": 25},
    )}
    result = validate_dto_structured([ladder_feature()], payload)
    assert result.valid, [r.message for r in result.results]


def test_a_child_value_is_validated_by_its_own_type_with_a_row_path():
    payload = {"discount_ladder_list": rows(
        {"wholesale_ladder_count_discount": 10, "wholesale_ladder_discount": 15},
        {"wholesale_ladder_count_discount": 20, "wholesale_ladder_discount": 99},
    )}
    result = validate_dto_structured([ladder_feature()], payload)
    assert not result.valid
    failure = result.results[0]
    assert failure.error == ValidationErrorCode.ABOVE_MAXIMUM
    assert failure.ref_value == 30
    assert failure.message.startswith("rows[1].wholesale_ladder_discount: ")


def test_a_mandatory_child_missing_in_a_row_fails_that_row():
    payload = {"discount_ladder_list": rows({"wholesale_ladder_discount": 15})}
    result = validate_dto_structured([ladder_feature()], payload)
    assert not result.valid
    failure = result.results[0]
    assert failure.error == ValidationErrorCode.MANDATORY_MISSING
    assert failure.message.startswith("rows[0].wholesale_ladder_count_discount: ")


def test_the_raised_error_carries_the_row_and_child_in_its_params():
    """The batch result reduces params to feature/slug, so the row coordinates
    are asserted on the exception the type raises."""
    feature_type = get_feature_type("group")
    config = parse_config(ladder_config())
    with pytest.raises(FeatureValidationError) as exc:
        feature_type.validate_dto(config, GroupDto(value=[{"wholesale_ladder_discount": 15}]))
    assert exc.value.error_params == {"row": 0, "child": "wholesale_ladder_count_discount"}


def test_an_optional_child_may_be_absent():
    payload = {"discount_ladder_list": rows({"wholesale_ladder_count_discount": 10})}
    assert validate_dto_structured([ladder_feature()], payload).valid


def test_too_many_rows():
    payload = {"discount_ladder_list": rows(
        *[{"wholesale_ladder_count_discount": n} for n in range(1, 7)]
    )}
    result = validate_dto_structured([ladder_feature()], payload)
    assert not result.valid
    assert result.results[0].error == ValidationErrorCode.ABOVE_MAXIMUM
    assert result.results[0].ref_value == 5


def test_too_few_rows():
    feature = ladder_feature(repeat={"min": 2, "max": 5})
    payload = {"discount_ladder_list": rows({"wholesale_ladder_count_discount": 10})}
    result = validate_dto_structured([feature], payload)
    assert not result.valid
    assert result.results[0].error == ValidationErrorCode.BELOW_MINIMUM
    assert result.results[0].ref_value == 2


def test_a_group_without_repeat_holds_one_row():
    feature = ladder_feature(repeat=None)
    ok = {"discount_ladder_list": rows({"wholesale_ladder_count_discount": 10})}
    assert validate_dto_structured([feature], ok).valid

    two = {"discount_ladder_list": rows(
        {"wholesale_ladder_count_discount": 10},
        {"wholesale_ladder_count_discount": 20},
    )}
    result = validate_dto_structured([feature], two)
    assert not result.valid
    assert result.results[0].error == ValidationErrorCode.ABOVE_MAXIMUM
    assert result.results[0].ref_value == 1


def test_an_unknown_child_slug_in_a_row_is_rejected():
    payload = {"discount_ladder_list": rows(
        {"wholesale_ladder_count_discount": 10, "typo_field": 1}
    )}
    result = validate_dto_structured([ladder_feature()], payload)
    assert not result.valid
    assert result.results[0].error == ValidationErrorCode.INVALID_FORMAT
    assert "typo_field" in result.results[0].message


def test_a_row_must_be_an_object():
    payload = {"discount_ladder_list": {"type": "group", "value": [[1, 2]]}}
    result = validate_dto_structured([ladder_feature()], payload)
    # normalize_dto drops non-object rows, so the payload validates as empty
    # and stores an empty table rather than a malformed one.
    assert result.valid
    dao = normalize_to_dao([ladder_feature()], payload)["discount_ladder_list"]
    assert dao["value"] == []


def test_a_non_list_value_is_rejected():
    feature_type = get_feature_type("group")
    config = parse_config(ladder_config())
    with pytest.raises(FeatureValidationError) as exc:
        feature_type.validate_dto(config, GroupDto(value={"a": 1}))
    assert exc.value.error_code == ValidationErrorCode.INVALID_TYPE


def test_an_empty_group_is_an_absent_value_not_a_row_count_violation():
    """`repeat.min` bites on a submitted table, not on an empty optional one —
    requiredness is the pipeline's business (static mandatory or a rule)."""
    payload = {"discount_ladder_list": rows()}
    assert validate_dto_structured([ladder_feature(repeat={"min": 2})], payload).valid

    result = validate_dto_structured([ladder_feature(mandatory=True)], payload)
    assert not result.valid
    assert result.results[0].error == ValidationErrorCode.MANDATORY_MISSING


def test_a_child_envelope_form_is_accepted():
    payload = {"discount_ladder_list": rows({
        "wholesale_ladder_count_discount": {"type": "int", "value": 10},
        "wholesale_ladder_discount": {"type": "int", "value": 15},
    })}
    assert validate_dto_structured([ladder_feature()], payload).valid


def test_raise_style_pipeline_reports_the_group():
    from django.core.exceptions import ValidationError

    payload = {"discount_ladder_list": rows({"wholesale_ladder_discount": 15})}
    with pytest.raises(ValidationError) as exc:
        validate_dto([ladder_feature()], payload)
    assert "rows[0].wholesale_ladder_count_discount" in str(exc.value)


# ---------------------------------------------------------------------------
# DAO
# ---------------------------------------------------------------------------

def test_dao_rows_carry_child_dao_meta():
    payload = {"discount_ladder_list": rows(
        {"wholesale_ladder_count_discount": 10, "wholesale_ladder_discount": 15},
        {"wholesale_ladder_count_discount": 20, "wholesale_ladder_discount": 25},
    )}
    dao = normalize_to_dao([ladder_feature()], payload)["discount_ladder_list"]

    assert dao["type"] == "group"
    assert dao["name"] == "Wholesale discount ladder"
    assert dao["order"] == 0
    assert len(dao["value"]) == 2

    cell = dao["value"][0]["wholesale_ladder_count_discount"]
    assert cell["type"] == "int"
    assert cell["value"] == 10
    assert cell["name"] == "Quantity for discount"
    assert cell["order"] == 0
    assert dao["value"][0]["wholesale_ladder_discount"]["order"] == 1


def test_dao_drops_empty_cells_and_empty_rows():
    payload = {"discount_ladder_list": rows(
        {"wholesale_ladder_count_discount": 10, "wholesale_ladder_discount": None},
        {},
    )}
    dao = normalize_to_dao([ladder_feature()], payload)["discount_ladder_list"]
    assert len(dao["value"]) == 1
    assert set(dao["value"][0]) == {"wholesale_ladder_count_discount"}


def test_format_value_reads_the_stored_rows():
    payload = {"discount_ladder_list": rows(
        {"wholesale_ladder_count_discount": 10, "wholesale_ladder_discount": 15},
        {"wholesale_ladder_count_discount": 20, "wholesale_ladder_discount": 25},
    )}
    dao = normalize_to_dao([ladder_feature()], payload)["discount_ladder_list"]
    text = format_feature_value(ladder_config(), dao)
    assert text == (
        "Quantity for discount: 10, Discount percent: 15 %; "
        "Quantity for discount: 20, Discount percent: 25 %"
    )


def test_format_value_of_an_empty_group_is_empty():
    from stapel_attributes.types.group import GroupDao

    assert format_feature_value(ladder_config(), GroupDao(value=[])) == ""


def test_default_value_is_an_empty_table():
    from stapel_attributes import get_default_value

    assert get_default_value(ladder_config()) == []


# ---------------------------------------------------------------------------
# translation keys
# ---------------------------------------------------------------------------

def test_translation_keys_aggregate_over_children():
    from stapel_attributes import collect_translation_keys_for_feature

    config = {
        "type": "group",
        "fields": [
            {"slug": "colour", "name": "feature.colour", "config": {
                "type": "select",
                "options": [
                    {"value": "red", "label": "option.red"},
                    {"value": "blue", "label": "option.blue"},
                ],
            }},
            {"slug": "qty", "name": "feature.qty", "config": {"type": "int"}},
        ],
    }
    assert collect_translation_keys_for_feature(config) == [
        "feature.colour", "option.red", "option.blue", "feature.qty",
    ]


def test_translation_keys_of_a_broken_group_are_empty_not_an_exception():
    from stapel_attributes import collect_translation_keys_for_feature

    broken = {"type": "group", "fields": [{"slug": "a"}]}  # a child with no config
    assert collect_translation_keys_for_feature(broken) == []


# ---------------------------------------------------------------------------
# children of every other kind
# ---------------------------------------------------------------------------

def test_a_row_is_its_own_value_namespace_for_a_ref_select_child(resolver):
    """A ref child narrowing by `parentFeature` reads the parent from the same
    row — the only reading that makes sense for a repeatable table."""
    config = {
        "type": "group",
        "fields": [
            {"slug": "vendor", "config": {
                "type": "ref_select",
                "optionsRef": {"vocabulary": "phones", "level": "Vendor"},
            }},
            {"slug": "model", "config": {
                "type": "ref_select",
                "optionsRef": {
                    "vocabulary": "phones", "level": "Model", "parentFeature": "vendor",
                },
            }},
        ],
        "repeat": {"min": 1, "max": 3},
    }
    feature = {"slug": "compatible", "name": "Compatible", "config": config}
    assert validate_feature_config(config).type == "group"

    good = {"compatible": rows({"vendor": ["apple"], "model": ["iphone-15"]})}
    assert validate_dto_structured([feature], good).valid, [
        r.message for r in validate_dto_structured([feature], good).results
    ]

    bad = {"compatible": rows({"vendor": ["samsung"], "model": ["iphone-15"]})}
    result = validate_dto_structured([feature], bad)
    assert not result.valid
    assert result.results[0].error == ValidationErrorCode.NOT_IN_OPTIONS
    assert result.results[0].message.startswith("rows[0].model: ")


@pytest.mark.parametrize("child_config,value", [
    ({"type": "string", "maxLength": 10}, "hello"),
    ({"type": "bool"}, True),
    ({"type": "float", "min": 0, "max": 1}, 0.5),
    ({"type": "hex_color", "options": [{"simple": "red", "hex": "#ff0000"}]},
     {"simple": "red", "hex": "#ff0000"}),
    ({"type": "select", "options": [
        {"value": "a", "label": "A"}, {"value": "b", "label": "B"}]}, ["a"]),
    ({"type": "hierarchical_select", "options": [
        {"value": "a", "children": [{"value": "b"}]}]}, ["a", "b"]),
    ({"type": "date", "precision": "date"}, 1700000000),
])
def test_every_ordinary_kind_works_as_a_child(child_config, value):
    feature = {"slug": "g", "config": {
        "type": "group",
        "fields": [{"slug": "cell", "name": "Cell", "config": child_config}],
    }}
    validate_feature_config(feature["config"])
    payload = {"g": rows({"cell": value})}
    result = validate_dto_structured([feature], payload)
    assert result.valid, [r.message for r in result.results]
    dao = normalize_to_dao([feature], payload)["g"]
    assert dao["value"][0]["cell"]["type"] == child_config["type"]


# ---------------------------------------------------------------------------
# rules on the group itself, through the pipeline
# ---------------------------------------------------------------------------

def test_a_hidden_group_is_neither_required_nor_stored():
    controller = {"slug": "wholesale", "config": {"type": "bool"}}
    group = {
        **ladder_feature(mandatory=True),
        "rules": [{"effect": "hide", "when": {"all": [
            {"feature": "wholesale", "op": "in", "values": ["false"]}]}}],
    }
    payload = {
        "wholesale": False,
        "discount_ladder_list": rows({"wholesale_ladder_count_discount": 10}),
    }
    result = validate_dto_structured([controller, group], payload)
    assert result.valid
    dao = normalize_to_dao([controller, group], payload)
    assert "discount_ladder_list" not in dao


def test_a_required_rule_makes_the_group_mandatory():
    controller = {"slug": "wholesale", "config": {"type": "bool"}}
    group = {
        **ladder_feature(),
        "rules": [{"effect": "require", "when": {"all": [
            {"feature": "wholesale", "op": "in", "values": ["true"]}]}}],
    }
    result = validate_dto_structured([controller, group], {"wholesale": True})
    assert not result.valid
    failure = [r for r in result.results if r.slug == "discount_ladder_list"][0]
    assert failure.error == ValidationErrorCode.MANDATORY_MISSING

    assert validate_dto_structured([controller, group], {"wholesale": False}).valid


# ---------------------------------------------------------------------------
# FeatureDef instances as children
# ---------------------------------------------------------------------------

def test_children_may_be_feature_def_instances():
    config = GroupConfig(fields=[
        FeatureDef(slug="qty", name="Qty", config={"type": "int", "min": 1}),
    ])
    get_feature_type("group").validate_config(config)
    dto = GroupDto(value=[{"qty": 3}])
    get_feature_type("group").validate_dto(config, dto)
    dao = get_feature_type("group").dto_to_dao(
        config, dto, FeatureDef(slug="g", config=config)
    )
    assert dao.value == [{"qty": {"name": "Qty", "type": "int", "value": 3,
                                 "precision": 1, "order": 0}}]


def test_config_validation_reports_a_bad_group_through_the_batch_validator():
    result = validate_configs_structured([
        {"slug": "g", "config": {"type": "group", "fields": []}},
    ])
    assert not result.valid
    assert result.results[0].status == ValidationStatus.VALIDATION_FAILED
    assert result.results[0].error == ValidationErrorCode.INVALID_CONFIG
