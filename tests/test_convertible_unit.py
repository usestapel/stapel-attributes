"""Tests for the ``convertible_unit`` built-in feature type.

Port of the legacy marketplace catalog's
``categories/tests/test_feature_types.py::TestConvertibleUnitFeatureType``,
converted from the bare-``ValidationError`` contract to the structured
``FeatureValidationError`` (error_code + ref_value) this library requires
from every type plugin, plus dedicated coverage for what the legacy type
never actually exercised: real unit -> base-unit conversion (the legacy
``normalize_dto`` silently discarded the submitted ``unit`` — see
``types/convertible_unit/type.py`` docstring), round-tripping, and
range-filtering semantics in the base unit.
"""

import pytest

from stapel_attributes.base import FeatureDef
from stapel_attributes.exceptions import FeatureValidationError
from stapel_attributes.registry import (
    dto_to_dao,
    get_feature_type,
    parse_config,
    validate_feature_config,
    validate_feature_dto,
)
from stapel_attributes.results import ValidationErrorCode
from stapel_attributes.types.convertible_unit.constants import (
    UNIT_FAMILIES,
    convert_from_base,
    convert_to_base,
)
from stapel_attributes.validation import normalize_to_dao, validate_dto_structured


LENGTH_CONFIG = {
    'type': 'convertible_unit',
    'unitType': 'length',
    'unit_m': 'cm',
    'unit_i': 'in',
}


# ============================================================================
# Config validation
# ============================================================================

class TestConvertibleUnitConfig:
    def test_valid_config(self):
        config = validate_feature_config(LENGTH_CONFIG)
        assert config.unitType == 'length'
        assert config.unit_m == 'cm'
        assert config.unit_i == 'in'

    def test_valid_config_metric_only(self):
        config = validate_feature_config({
            'type': 'convertible_unit', 'unitType': 'weight', 'unit_m': 'kg',
        })
        assert config.unit_i is None

    def test_invalid_config_no_unit_type(self):
        with pytest.raises(FeatureValidationError) as exc_info:
            validate_feature_config({'type': 'convertible_unit', 'unit_m': 'cm'})
        assert exc_info.value.error_code == ValidationErrorCode.INVALID_CONFIG

    def test_invalid_config_unknown_unit_type(self):
        with pytest.raises(FeatureValidationError) as exc_info:
            validate_feature_config({
                'type': 'convertible_unit', 'unitType': 'unknown', 'unit_m': 'x',
            })
        assert exc_info.value.error_code == ValidationErrorCode.INVALID_CONFIG

    def test_invalid_config_no_units_at_all(self):
        with pytest.raises(FeatureValidationError) as exc_info:
            validate_feature_config({'type': 'convertible_unit', 'unitType': 'length'})
        assert exc_info.value.error_code == ValidationErrorCode.INVALID_CONFIG

    def test_invalid_config_metric_unit_not_in_family(self):
        with pytest.raises(FeatureValidationError) as exc_info:
            validate_feature_config({
                'type': 'convertible_unit', 'unitType': 'length', 'unit_m': 'kg',
            })
        assert exc_info.value.error_code == ValidationErrorCode.INVALID_CONFIG

    def test_invalid_config_imperial_unit_wrong_family(self):
        # 'in' is a length unit, not a valid imperial weight unit.
        with pytest.raises(FeatureValidationError) as exc_info:
            validate_feature_config({
                'type': 'convertible_unit', 'unitType': 'weight', 'unit_i': 'in',
            })
        assert exc_info.value.error_code == ValidationErrorCode.INVALID_CONFIG

    def test_invalid_config_min_greater_than_max(self):
        with pytest.raises(FeatureValidationError) as exc_info:
            validate_feature_config({**LENGTH_CONFIG, 'min': 10, 'max': 1})
        assert exc_info.value.error_code == ValidationErrorCode.MIN_GREATER_THAN_MAX

    def test_invalid_config_negative_precision(self):
        with pytest.raises(FeatureValidationError) as exc_info:
            validate_feature_config({**LENGTH_CONFIG, 'precision': -1})
        assert exc_info.value.error_code == ValidationErrorCode.INVALID_CONFIG


# ============================================================================
# DTO validation + unit -> base normalization
# ============================================================================

class TestConvertibleUnitDto:
    def test_valid_dto_with_unit_converts_to_base(self):
        config = parse_config(LENGTH_CONFIG)
        dto = validate_feature_dto(config, {'type': 'convertible_unit', 'value': 100.0, 'unit': 'cm'})
        # 100 cm -> 1.0 m (base unit for 'length' is 'm')
        assert dto.value == pytest.approx(1.0)

    def test_valid_dto_without_unit_treated_as_already_base(self):
        config = parse_config(LENGTH_CONFIG)
        dto = validate_feature_dto(config, {'type': 'convertible_unit', 'value': 2.5})
        assert dto.value == pytest.approx(2.5)

    def test_dto_imperial_unit_converts_to_base(self):
        # precision=4 so the 0.0254 m/in factor isn't rounded away (default
        # precision is 2, which would flatten it to 0.03 — see the
        # precision-rounding test below for that default behavior).
        config = parse_config({**LENGTH_CONFIG, 'precision': 4})
        dto = validate_feature_dto(config, {'type': 'convertible_unit', 'value': 1.0, 'unit': 'in'})
        assert dto.value == pytest.approx(0.0254)

    def test_dto_rounds_to_configured_precision(self):
        config = parse_config(LENGTH_CONFIG)  # default precision=2
        dto = validate_feature_dto(config, {'type': 'convertible_unit', 'value': 1.0, 'unit': 'in'})
        assert dto.value == pytest.approx(0.03)

    def test_invalid_dto_not_a_number(self):
        config = parse_config(LENGTH_CONFIG)
        with pytest.raises(FeatureValidationError) as exc_info:
            validate_feature_dto(config, {'type': 'convertible_unit', 'value': 'abc'})
        assert exc_info.value.error_code == ValidationErrorCode.INVALID_TYPE

    def test_invalid_dto_unit_not_offered_by_config(self):
        # 'km' is a valid 'length' unit but this config only offers cm/in.
        config = parse_config(LENGTH_CONFIG)
        with pytest.raises(FeatureValidationError) as exc_info:
            validate_feature_dto(config, {'type': 'convertible_unit', 'value': 1.0, 'unit': 'km'})
        assert exc_info.value.error_code == ValidationErrorCode.NOT_IN_OPTIONS
        assert set(exc_info.value.ref_value) == {'cm', 'in'}

    def test_dto_below_minimum_in_base_unit(self):
        config = parse_config({**LENGTH_CONFIG, 'min': 1.0})
        with pytest.raises(FeatureValidationError) as exc_info:
            # 50 cm = 0.5 m, below the 1.0 m minimum.
            validate_feature_dto(config, {'type': 'convertible_unit', 'value': 50.0, 'unit': 'cm'})
        assert exc_info.value.error_code == ValidationErrorCode.BELOW_MINIMUM
        assert exc_info.value.ref_value == 1.0

    def test_dto_above_maximum_in_base_unit(self):
        config = parse_config({**LENGTH_CONFIG, 'max': 1.0})
        with pytest.raises(FeatureValidationError) as exc_info:
            validate_feature_dto(config, {'type': 'convertible_unit', 'value': 200.0, 'unit': 'cm'})
        assert exc_info.value.error_code == ValidationErrorCode.ABOVE_MAXIMUM

    def test_missing_value_defaults_to_zero(self):
        # Mirrors int/float: normalize_dto never leaves value as None.
        config = parse_config(LENGTH_CONFIG)
        dto = validate_feature_dto(config, {'type': 'convertible_unit'})
        assert dto.value == 0.0


# ============================================================================
# Temperature family (affine conversion)
# ============================================================================

class TestConvertibleUnitTemperature:
    TEMP_CONFIG = {
        'type': 'convertible_unit', 'unitType': 'temperature', 'unit_m': 'c', 'unit_i': 'f',
    }

    def test_fahrenheit_converts_to_celsius_base(self):
        config = parse_config(self.TEMP_CONFIG)
        dto = validate_feature_dto(config, {'type': 'convertible_unit', 'value': 32.0, 'unit': 'f'})
        assert dto.value == pytest.approx(0.0)

    def test_celsius_is_identity(self):
        config = parse_config(self.TEMP_CONFIG)
        dto = validate_feature_dto(config, {'type': 'convertible_unit', 'value': 100.0, 'unit': 'c'})
        assert dto.value == pytest.approx(100.0)

    def test_kelvin_round_trip(self):
        base = convert_to_base(300.0, 'k', 'temperature')
        back = convert_from_base(base, 'k', 'temperature')
        assert back == pytest.approx(300.0)


# ============================================================================
# Conversion round-trips across every shipped family
# ============================================================================

class TestConversionRoundTrip:
    @pytest.mark.parametrize('unit_type', sorted(UNIT_FAMILIES))
    def test_every_unit_round_trips_through_base(self, unit_type):
        for unit in UNIT_FAMILIES[unit_type]['units']:
            base = convert_to_base(10.0, unit, unit_type)
            back = convert_from_base(base, unit, unit_type)
            assert back == pytest.approx(10.0), f"{unit_type}.{unit} did not round-trip"

    def test_base_unit_is_identity(self):
        for unit_type, family in UNIT_FAMILIES.items():
            base_unit = family['base_unit']
            assert convert_to_base(5.0, base_unit, unit_type) == pytest.approx(5.0)


# ============================================================================
# DAO / dto_to_dao — storage is always in the base unit
# ============================================================================

class TestConvertibleUnitDao:
    def test_dto_to_dao_stores_base_unit_value(self):
        config = parse_config(LENGTH_CONFIG)
        feature = FeatureDef(slug='length', config=LENGTH_CONFIG, name='Length')
        dto = validate_feature_dto(config, {'type': 'convertible_unit', 'value': 250.0, 'unit': 'cm'})
        dao = dto_to_dao(config, dto, feature)
        assert dao.value == pytest.approx(2.5)
        assert dao.unitType == 'length'
        assert dao.unit_m == 'cm'
        assert dao.unit_i == 'in'

    def test_format_value_converts_base_to_display_unit(self):
        ft = get_feature_type('convertible_unit')
        config = parse_config(LENGTH_CONFIG)
        feature = FeatureDef(slug='length', config=LENGTH_CONFIG, name='Length')
        dto = validate_feature_dto(config, {'type': 'convertible_unit', 'value': 2.5})
        dao = dto_to_dao(config, dto, feature)
        # base 2.5 m -> display in unit_m ('cm') = 250 cm
        assert ft.format_value(config, dao) == '250 cm'


# ============================================================================
# Range filtering — the DAO value is canonical, so filtering is a plain
# numeric comparison once the query bounds are converted to the base unit.
# ============================================================================

class TestRangeFiltering:
    def test_query_bounds_convert_to_base_for_a_plain_range_check(self):
        # "give me listings between 50cm and 150cm" -> base-unit bounds.
        low = convert_to_base(50.0, 'cm', 'length')
        high = convert_to_base(150.0, 'cm', 'length')
        stored_values_m = [0.3, 0.75, 1.2, 2.0]  # already-normalized DAO values
        in_range = [v for v in stored_values_m if low <= v <= high]
        assert in_range == [0.75, 1.2]

    def test_feature_type_exposes_to_base_from_base_helpers(self):
        ft = get_feature_type('convertible_unit')
        assert ft.to_base(100.0, 'cm', 'length') == pytest.approx(1.0)
        assert ft.from_base(1.0, 'cm', 'length') == pytest.approx(100.0)


# ============================================================================
# Full pipeline (validate_dto_structured / normalize_to_dao)
# ============================================================================

class TestConvertibleUnitPipeline:
    def test_normalize_to_dao_end_to_end(self):
        features = [FeatureDef(slug='length', config=LENGTH_CONFIG, name='Length')]
        result = normalize_to_dao(features, {'length': {'type': 'convertible_unit', 'value': 100.0, 'unit': 'cm'}})
        assert result['length']['value'] == pytest.approx(1.0)
        assert result['length']['unitType'] == 'length'

    def test_validate_dto_structured_reports_ok(self):
        features = [FeatureDef(slug='length', config=LENGTH_CONFIG, name='Length')]
        result = validate_dto_structured(features, {'length': {'type': 'convertible_unit', 'value': 100.0, 'unit': 'cm'}})
        assert result.valid is True

    def test_validate_dto_structured_reports_below_minimum(self):
        config = {**LENGTH_CONFIG, 'min': 1.0}
        features = [FeatureDef(slug='length', config=config, name='Length')]
        result = validate_dto_structured(features, {'length': {'type': 'convertible_unit', 'value': 10.0, 'unit': 'cm'}})
        assert result.valid is False
        assert result.results[0].error == ValidationErrorCode.BELOW_MINIMUM
