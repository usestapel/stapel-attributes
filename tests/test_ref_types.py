"""The vocabulary-backed types and the resolver seam (spec §3.1-3.2)."""
import pytest

from stapel_attributes import (
    format_feature_value,
    get_feature_type,
    parse_config,
    validate_feature_config,
)
from stapel_attributes.base import FeatureDef, ValidationContext
from stapel_attributes.exceptions import FeatureValidationError
from stapel_attributes.results import ValidationErrorCode, ValidationStatus
from stapel_attributes.tests.fake_vocabulary import VOCABULARY, FakeVocabularyResolver
from stapel_attributes.validation import (
    normalize_to_dao,
    validate_configs_structured,
    validate_dto_structured,
)
from stapel_attributes.vocabularies import (
    VocabularyInfo,
    VocabularyLevel,
    get_vocabulary_resolver,
    register_vocabulary_resolver,
)


@pytest.fixture
def resolver():
    """Register the in-memory vocabulary for one test and clear it after."""
    instance = FakeVocabularyResolver()
    register_vocabulary_resolver(instance)
    yield instance
    register_vocabulary_resolver(None)


@pytest.fixture
def no_resolver():
    register_vocabulary_resolver(None)
    yield
    register_vocabulary_resolver(None)


def ref_config(level="Model", parent=None, **kwargs):
    options_ref = {"vocabulary": VOCABULARY, "level": level}
    if parent:
        options_ref["parentFeature"] = parent
    return {"type": "ref_select", "optionsRef": options_ref, **kwargs}


def chain_config(levels=("Vendor", "Model"), **kwargs):
    return {
        "type": "ref_hierarchical_select",
        "vocabulary": VOCABULARY,
        "levels": list(levels),
        **kwargs,
    }


def _validate(config, value, values=None, slug="model", parent_feature=None):
    """Run one value through the type in context and return the raised code."""
    features = [FeatureDef(slug=slug, config=config)]
    if parent_feature:
        features.insert(0, FeatureDef(slug=parent_feature, config={"type": "string"}))
    payload = dict(values or {})
    payload[slug] = value
    result = validate_dto_structured(features, payload)
    row = next(r for r in result.results if r.slug == slug)
    return row


class TestResolverRegistry:
    def test_no_resolver_by_default(self, no_resolver):
        assert get_vocabulary_resolver() is None

    def test_runtime_registration_wins_over_the_setting(self, settings, resolver):
        settings.STAPEL_ATTRIBUTES = {
            "VOCABULARY_RESOLVER": "stapel_attributes.tests.fake_vocabulary.FakeVocabularyResolver",
        }
        assert get_vocabulary_resolver() is resolver

    def test_dotted_path_class_is_instantiated_once(self, settings, no_resolver):
        settings.STAPEL_ATTRIBUTES = {
            "VOCABULARY_RESOLVER": "stapel_attributes.tests.fake_vocabulary.FakeVocabularyResolver",
        }
        first = get_vocabulary_resolver()
        assert isinstance(first, FakeVocabularyResolver)
        assert get_vocabulary_resolver() is first

    def test_vocabulary_info_finds_its_levels(self):
        info = VocabularyInfo(slug="v", levels=(VocabularyLevel("A"), VocabularyLevel("B", parent="A")))
        assert info.level("B").parent == "A"
        assert info.level("Z") is None


class TestRefSelectConfig:
    def test_without_a_resolver_the_config_is_loudly_invalid(self, no_resolver):
        with pytest.raises(FeatureValidationError) as exc:
            validate_feature_config(ref_config())
        assert exc.value.error_code is ValidationErrorCode.INVALID_CONFIG
        assert "no vocabulary resolver registered" in str(exc.value)

    def test_config_validation_is_where_the_resolver_is_demanded(self, no_resolver):
        # Parsing must stay resolver-free: reading a stored schema is not the
        # moment to demand a vocabulary source.
        assert parse_config(ref_config()).optionsRef["level"] == "Model"

    def test_valid_config_passes(self, resolver):
        config = validate_feature_config(ref_config())
        assert config.maxSelected == 1
        assert config.uiStyle == "dropdown"

    def test_unknown_vocabulary_is_invalid(self, resolver):
        with pytest.raises(FeatureValidationError) as exc:
            validate_feature_config({"type": "ref_select",
                                     "optionsRef": {"vocabulary": "nope", "level": "Model"}})
        assert exc.value.error_code is ValidationErrorCode.INVALID_CONFIG

    def test_unknown_level_is_invalid(self, resolver):
        with pytest.raises(FeatureValidationError) as exc:
            validate_feature_config(ref_config(level="Nope"))
        assert exc.value.error_code is ValidationErrorCode.INVALID_CONFIG

    def test_missing_options_ref_is_invalid(self, resolver):
        with pytest.raises(FeatureValidationError) as exc:
            validate_feature_config({"type": "ref_select"})
        assert exc.value.error_code is ValidationErrorCode.INVALID_CONFIG

    @pytest.mark.parametrize("overrides, code", [
        ({"uiStyle": "carousel"}, ValidationErrorCode.INVALID_CONFIG),
        ({"minSelected": -1}, ValidationErrorCode.INVALID_CONFIG),
        ({"maxSelected": 0}, ValidationErrorCode.INVALID_CONFIG),
        ({"minSelected": 3, "maxSelected": 2}, ValidationErrorCode.MIN_GREATER_THAN_MAX),
    ])
    def test_cardinality_and_style_are_checked(self, resolver, overrides, code):
        with pytest.raises(FeatureValidationError) as exc:
            validate_feature_config(ref_config(**overrides))
        assert exc.value.error_code is code


class TestRefSelectValue:
    def test_known_term_passes(self, resolver):
        assert _validate(ref_config(), ["iphone-15"]).status is ValidationStatus.OK

    def test_unknown_term_is_not_in_options(self, resolver):
        row = _validate(ref_config(), ["nokia-3310"])
        assert row.error is ValidationErrorCode.NOT_IN_OPTIONS

    def test_max_selected_is_enforced(self, resolver):
        row = _validate(ref_config(), ["iphone-15", "iphone-14"])
        assert row.error is ValidationErrorCode.ABOVE_MAXIMUM

    def test_min_selected_is_enforced(self, resolver):
        row = _validate(ref_config(minSelected=1, maxSelected=2), ["iphone-15"])
        assert row.status is ValidationStatus.OK

    def test_empty_parent_allows_the_whole_level(self, resolver):
        row = _validate(
            ref_config(parent="vendor"), ["galaxy-s24"],
            values={"vendor": ""}, parent_feature="vendor",
        )
        assert row.status is ValidationStatus.OK

    def test_filled_parent_narrows_to_its_children(self, resolver):
        row = _validate(
            ref_config(parent="vendor"), ["iphone-15"],
            values={"vendor": "apple"}, parent_feature="vendor",
        )
        assert row.status is ValidationStatus.OK

    def test_filled_parent_rejects_a_foreign_child(self, resolver):
        row = _validate(
            ref_config(parent="vendor"), ["galaxy-s24"],
            values={"vendor": "apple"}, parent_feature="vendor",
        )
        assert row.error is ValidationErrorCode.NOT_IN_OPTIONS

    def test_parent_value_is_read_through_a_dto_envelope(self, resolver):
        row = _validate(
            ref_config(parent="vendor"), ["galaxy-s24"],
            values={"vendor": {"type": "string", "value": "apple"}}, parent_feature="vendor",
        )
        assert row.error is ValidationErrorCode.NOT_IN_OPTIONS

    def test_without_a_resolver_values_are_only_shape_checked(self, no_resolver):
        # The loud failure belongs to config validation; a value path with no
        # resolver checks only shape, it does not invent a rejection.
        assert _validate(ref_config(), ["anything"]).status is ValidationStatus.OK


class TestRefSelectStorage:
    def test_dao_carries_labels_and_the_source_pointer(self, resolver):
        feature = FeatureDef(slug="model", config=ref_config(), name="Model")
        dao = normalize_to_dao([feature], {"model": ["iphone-15"]})["model"]
        assert dao["value"] == ["iphone-15"]
        assert dao["labels"] == ["iPhone 15"]
        assert (dao["vocabulary"], dao["level"]) == (VOCABULARY, "Model")

    def test_unknown_code_labels_as_itself(self, resolver):
        feature = FeatureDef(slug="model", config=ref_config())
        dao = normalize_to_dao([feature], {"model": ["ghost"]})["model"]
        assert dao["labels"] == ["ghost"]

    def test_format_value_reads_the_dao_labels_without_a_resolver(self, no_resolver):
        dao_class = get_feature_type("ref_select").dao_class
        dao = dao_class(value=["iphone-15"], labels=["iPhone 15"])
        assert format_feature_value(ref_config(), dao) == "iPhone 15"

    def test_format_value_falls_back_to_codes(self, no_resolver):
        dao_class = get_feature_type("ref_select").dao_class
        assert format_feature_value(ref_config(), dao_class(value=["x"])) == "x"

    def test_translation_keys_are_vocabulary_owned(self, resolver):
        feature_type = get_feature_type("ref_select")
        assert feature_type.get_translation_keys(parse_config(ref_config())) == []


class TestRefHierarchicalSelect:
    def test_valid_chain_config_passes(self, resolver):
        assert validate_feature_config(chain_config()).minDepth == 1

    def test_no_resolver_is_loud(self, no_resolver):
        with pytest.raises(FeatureValidationError) as exc:
            validate_feature_config(chain_config())
        assert "no vocabulary resolver registered" in str(exc.value)

    def test_levels_must_be_a_parent_chain(self, resolver):
        with pytest.raises(FeatureValidationError) as exc:
            validate_feature_config(chain_config(levels=("Vendor", "MemorySize")))
        assert exc.value.error_code is ValidationErrorCode.INVALID_CONFIG

    @pytest.mark.parametrize("overrides, code", [
        ({"levels": []}, ValidationErrorCode.INVALID_CONFIG),
        ({"minDepth": 0}, ValidationErrorCode.INVALID_CONFIG),
        ({"minDepth": 3}, ValidationErrorCode.INVALID_CONFIG),
        ({"maxDepth": 3}, ValidationErrorCode.INVALID_CONFIG),
        ({"minDepth": 2, "maxDepth": 1}, ValidationErrorCode.MIN_GREATER_THAN_MAX),
    ])
    def test_depth_bounds_are_checked(self, resolver, overrides, code):
        with pytest.raises(FeatureValidationError) as exc:
            validate_feature_config(chain_config(**overrides))
        assert exc.value.error_code is code

    def test_full_chain_validates(self, resolver):
        row = _validate(chain_config(("Vendor", "Model", "MemorySize")),
                        ["apple", "iphone-15", "256-gb"], slug="phone")
        assert row.status is ValidationStatus.OK

    def test_broken_chain_is_not_in_options(self, resolver):
        row = _validate(chain_config(("Vendor", "Model")), ["apple", "galaxy-s24"], slug="phone")
        assert row.error is ValidationErrorCode.NOT_IN_OPTIONS

    def test_unknown_term_is_not_in_options(self, resolver):
        row = _validate(chain_config(), ["nokia"], slug="phone")
        assert row.error is ValidationErrorCode.NOT_IN_OPTIONS

    def test_min_depth_is_enforced(self, resolver):
        row = _validate(chain_config(minDepth=2), ["apple"], slug="phone")
        assert row.error is ValidationErrorCode.BELOW_MINIMUM

    def test_max_depth_is_enforced(self, resolver):
        row = _validate(chain_config(("Vendor", "Model", "MemorySize"), maxDepth=2),
                        ["apple", "iphone-15", "256-gb"], slug="phone")
        assert row.error is ValidationErrorCode.ABOVE_MAXIMUM

    def test_a_path_longer_than_the_chain_is_rejected(self, resolver):
        row = _validate(chain_config(("Vendor", "Model")),
                        ["apple", "iphone-15", "256-gb"], slug="phone")
        assert row.error is ValidationErrorCode.ABOVE_MAXIMUM

    def test_dao_labels_one_per_level(self, resolver):
        feature = FeatureDef(slug="phone", config=chain_config())
        dao = normalize_to_dao([feature], {"phone": ["apple", "iphone-15"]})["phone"]
        assert dao["labels"] == ["Apple", "iPhone 15"]
        assert dao["levels"] == ["Vendor", "Model"]

    def test_format_value_joins_the_labels(self, no_resolver):
        dao_class = get_feature_type("ref_hierarchical_select").dao_class
        dao = dao_class(value=["apple", "iphone-15"], labels=["Apple", "iPhone 15"])
        assert format_feature_value(chain_config(), dao) == "Apple / iPhone 15"


class TestConfigWarnings:
    def test_unknown_parent_feature_is_a_warning_not_an_error(self, resolver):
        feature = FeatureDef(slug="model", config=ref_config(parent="vendor"))
        result = validate_configs_structured([feature], known_slugs={"model"})
        assert result.valid is True
        assert result.results[0].warnings == [
            "optionsRef.parentFeature references unknown feature slug: vendor"
        ]

    def test_known_parent_feature_warns_about_nothing(self, resolver):
        feature = FeatureDef(slug="model", config=ref_config(parent="vendor"))
        result = validate_configs_structured([feature], known_slugs={"model", "vendor"})
        assert result.results[0].warnings is None


class TestValidationContextHook:
    def test_default_hook_delegates_to_validate_dto(self, resolver):
        # Every host type inherits the default and notices nothing.
        feature_type = get_feature_type("int")
        config = parse_config({"type": "int", "max": 5})
        dto = feature_type.normalize_dto(config, {"type": "int", "value": 9})
        context = ValidationContext(values={}, feature_defs=[])
        with pytest.raises(FeatureValidationError) as exc:
            feature_type.validate_dto_in_context(config, dto, context)
        assert exc.value.error_code is ValidationErrorCode.ABOVE_MAXIMUM
