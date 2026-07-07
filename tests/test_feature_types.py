"""
Tests for the polymorphic feature type system.

Port of the legacy catalog's ``categories/tests/test_feature_types.py`` (the
engine's fidelity proof). Differences from the source suite:

- size_grid / convertible_unit are marketplace-specific and are not shipped
  here (registered app-layer via the open registry) — their test classes
  stayed with the vertical;
- the Feature/Category model classes moved to stapel-categories with the
  models; their engine-level assertions are covered via the registry API.

Tests cover:
- Registry functions
- Polymorphic serializers (Config, DTO, DAO)
- Individual feature types validation
"""

import pytest
from django.core.exceptions import ValidationError

from stapel_attributes.registry import (
    get_feature_type,
    get_all_feature_types,
    get_all_type_slugs,
    validate_feature_config,
    validate_feature_dto,
)
from stapel_attributes.serializers import (
    get_feature_config_serializer_class,
    get_feature_dto_serializer_class,
    get_feature_dao_serializer_class,
)

BUILTIN_TYPES = [
    'bool', 'date', 'float', 'header', 'hex_color',
    'hierarchical_select', 'int', 'select', 'string',
]


# ============================================================================
# Registry Tests
# ============================================================================

class TestFeatureTypeRegistry:
    """Tests for the feature type registry."""

    def test_all_types_registered(self):
        """All 9 built-in feature types should be registered."""
        type_slugs = get_all_type_slugs()
        assert sorted(set(type_slugs) & set(BUILTIN_TYPES)) == sorted(BUILTIN_TYPES)

    def test_get_feature_type_valid(self):
        """get_feature_type should return type instance for valid slug."""
        int_type = get_feature_type('int')
        assert int_type.slug == 'int'
        assert int_type.name == 'Integer'

    def test_get_feature_type_invalid(self):
        """get_feature_type should raise ValueError for invalid slug."""
        with pytest.raises(ValueError) as exc_info:
            get_feature_type('invalid_type')
        assert 'Unknown feature type' in str(exc_info.value)

    def test_get_all_feature_types(self):
        """get_all_feature_types should return list of type instances."""
        types = get_all_feature_types()
        assert len(types) >= len(BUILTIN_TYPES)
        assert all(hasattr(t, 'slug') for t in types)

    def test_each_type_has_required_attributes(self):
        """Each type should have config/dto/dao serializers."""
        for ft in get_all_feature_types():
            assert hasattr(ft, 'config_serializer_class')
            assert hasattr(ft, 'dto_serializer_class')
            assert hasattr(ft, 'dao_serializer_class')
            assert hasattr(ft, 'validate_config')
            assert hasattr(ft, 'validate_dto')
            assert hasattr(ft, 'dto_to_dao')

    def test_marketplace_types_not_shipped(self):
        """size_grid / convertible_unit are app-layer registrations, not built-ins."""
        slugs = get_all_type_slugs()
        assert 'size_grid' not in slugs
        assert 'convertible_unit' not in slugs


# ============================================================================
# Polymorphic Serializer Tests
# ============================================================================

class TestPolymorphicSerializers:
    """Tests for polymorphic serializers."""

    def test_config_serializer_has_all_types(self):
        """Config serializer should have mappings for all types."""
        serializer_class = get_feature_config_serializer_class()
        serializer = serializer_class()
        mapping = serializer._serializer_mapping
        assert set(BUILTIN_TYPES) <= set(mapping)
        assert 'int' in mapping
        assert 'string' in mapping
        assert 'bool' in mapping

    def test_dto_serializer_has_all_types(self):
        """DTO serializer should have mappings for all types."""
        serializer_class = get_feature_dto_serializer_class()
        serializer = serializer_class()
        mapping = serializer._serializer_mapping
        assert set(BUILTIN_TYPES) <= set(mapping)

    def test_dao_serializer_has_all_types(self):
        """DAO serializer should have mappings for all types."""
        serializer_class = get_feature_dao_serializer_class()
        serializer = serializer_class()
        mapping = serializer._serializer_mapping
        assert set(BUILTIN_TYPES) <= set(mapping)

    def test_config_serializer_int(self):
        """Config serializer should validate int config."""
        data = {'type': 'int', 'min': 0, 'max': 100}
        serializer_class = get_feature_config_serializer_class()
        serializer = serializer_class(data=data)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data['type'] == 'int'
        assert serializer.validated_data['min'] == 0
        assert serializer.validated_data['max'] == 100

    def test_config_serializer_string(self):
        """Config serializer should validate string config."""
        data = {'type': 'string', 'minLength': 1, 'maxLength': 255}
        serializer_class = get_feature_config_serializer_class()
        serializer = serializer_class(data=data)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data['type'] == 'string'

    def test_config_serializer_select(self):
        """Config serializer should validate select config."""
        data = {
            'type': 'select',
            'options': [
                {'value': 'a', 'label': 'Option A'},
                {'value': 'b', 'label': 'Option B'}
            ]
        }
        serializer_class = get_feature_config_serializer_class()
        serializer = serializer_class(data=data)
        assert serializer.is_valid(), serializer.errors
        assert len(serializer.validated_data['options']) == 2

    def test_dto_serializer_int(self):
        """DTO serializer should validate int DTO."""
        data = {'type': 'int', 'value': 42}
        serializer_class = get_feature_dto_serializer_class()
        serializer = serializer_class(data=data)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data['value'] == 42

    def test_dto_serializer_bool(self):
        """DTO serializer should validate bool DTO."""
        data = {'type': 'bool', 'value': True}
        serializer_class = get_feature_dto_serializer_class()
        serializer = serializer_class(data=data)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data['value'] is True

    def test_dto_serializer_select(self):
        """DTO serializer should validate select DTO."""
        data = {'type': 'select', 'value': ['a', 'b']}
        serializer_class = get_feature_dto_serializer_class()
        serializer = serializer_class(data=data)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data['value'] == ['a', 'b']

    def test_config_serializer_invalid_type(self):
        """Config serializer should reject invalid type."""
        data = {'type': 'invalid_type'}
        serializer_class = get_feature_config_serializer_class()
        serializer = serializer_class(data=data)
        # Invalid type should cause validation error
        try:
            serializer.is_valid(raise_exception=True)
            assert False, "Should have raised validation error"
        except Exception:
            pass  # Expected


# ============================================================================
# Integer Feature Type Tests
# ============================================================================

class TestIntFeatureType:
    """Tests for int feature type."""

    def test_valid_config_minimal(self):
        """Minimal int config should be valid."""
        config = {'type': 'int'}
        validate_feature_config(config)  # Should not raise

    def test_valid_config_full(self):
        """Full int config should be valid."""
        config = {
            'type': 'int',
            'min': 0,
            'max': 100,
            'options': [10, 20, 30],
            'allowCustom': True,
            'precision': 1,
        }
        validate_feature_config(config)  # Should not raise

    def test_invalid_config_min_greater_than_max(self):
        """Config with min > max should be invalid."""
        config = {'type': 'int', 'min': 100, 'max': 10}
        with pytest.raises(ValidationError):
            validate_feature_config(config)

    def test_invalid_config_options_not_list(self):
        """Config with options not a list should be invalid."""
        config = {'type': 'int', 'options': 'not a list'}
        with pytest.raises(ValidationError):
            validate_feature_config(config)

    def test_valid_dto(self):
        """Valid int DTOs should pass validation."""
        config = {'type': 'int', 'min': 0, 'max': 100}
        validate_feature_dto(config, {'type': 'int', 'value': 50})
        validate_feature_dto(config, {'type': 'int', 'value': 0})
        validate_feature_dto(config, {'type': 'int', 'value': 100})

    def test_invalid_dto_below_min(self):
        """Value below min should fail validation."""
        config = {'type': 'int', 'min': 10}
        with pytest.raises(ValidationError):
            validate_feature_dto(config, {'type': 'int', 'value': 5})

    def test_invalid_dto_above_max(self):
        """Value above max should fail validation."""
        config = {'type': 'int', 'max': 100}
        with pytest.raises(ValidationError):
            validate_feature_dto(config, {'type': 'int', 'value': 150})

    def test_invalid_dto_not_integer(self):
        """Non-integer value should fail validation."""
        config = {'type': 'int'}
        with pytest.raises(ValidationError):
            validate_feature_dto(config, {'type': 'int', 'value': 'abc'})

    def test_dto_options_constraint(self):
        """Value not in options with allowCustom=False should fail."""
        config = {'type': 'int', 'options': [10, 20, 30], 'allowCustom': False}
        validate_feature_dto(config, {'type': 'int', 'value': 20})  # Should not raise
        with pytest.raises(ValidationError):
            validate_feature_dto(config, {'type': 'int', 'value': 15})


# ============================================================================
# Float Feature Type Tests
# ============================================================================

class TestFloatFeatureType:
    """Tests for float feature type."""

    def test_valid_config_minimal(self):
        """Minimal float config should be valid."""
        config = {'type': 'float'}
        validate_feature_config(config)

    def test_valid_config_full(self):
        """Full float config should be valid."""
        config = {
            'type': 'float',
            'min': 0.0,
            'max': 100.0,
            'precision': 3,
            'options': [1.5, 2.5, 3.5],
            'allowCustom': True
        }
        validate_feature_config(config)

    def test_valid_dto(self):
        """Valid float DTOs should pass validation."""
        config = {'type': 'float', 'min': 0.0, 'max': 10.0}
        validate_feature_dto(config, {'type': 'float', 'value': 5.5})
        validate_feature_dto(config, {'type': 'float', 'value': 0.0})
        validate_feature_dto(config, {'type': 'float', 'value': 10.0})

    def test_invalid_dto_below_min(self):
        """Value below min should fail validation."""
        config = {'type': 'float', 'min': 1.5}
        with pytest.raises(ValidationError):
            validate_feature_dto(config, {'type': 'float', 'value': 1.0})

    def test_invalid_dto_not_number(self):
        """Non-numeric value should fail validation."""
        config = {'type': 'float'}
        with pytest.raises(ValidationError):
            validate_feature_dto(config, {'type': 'float', 'value': 'abc'})


# ============================================================================
# String Feature Type Tests
# ============================================================================

class TestStringFeatureType:
    """Tests for string feature type."""

    def test_valid_config_minimal(self):
        """Minimal string config should be valid."""
        config = {'type': 'string'}
        validate_feature_config(config)

    def test_valid_config_with_length(self):
        """String config with length constraints should be valid."""
        config = {'type': 'string', 'minLength': 3, 'maxLength': 50}
        validate_feature_config(config)

    def test_valid_config_with_pattern(self):
        """String config with regex pattern should be valid."""
        config = {'type': 'string', 'pattern': r'^[A-Z]{2,4}$'}
        validate_feature_config(config)

    def test_invalid_config_invalid_pattern(self):
        """String config with invalid regex should fail."""
        config = {'type': 'string', 'pattern': '[invalid('}
        with pytest.raises(ValidationError):
            validate_feature_config(config)

    def test_valid_dto(self):
        """Valid string DTOs should pass validation."""
        config = {'type': 'string', 'minLength': 2, 'maxLength': 10}
        validate_feature_dto(config, {'type': 'string', 'value': 'hello'})

    def test_invalid_dto_too_short(self):
        """String shorter than minLength should fail."""
        config = {'type': 'string', 'minLength': 5}
        with pytest.raises(ValidationError):
            validate_feature_dto(config, {'type': 'string', 'value': 'ab'})

    def test_invalid_dto_too_long(self):
        """String longer than maxLength should fail."""
        config = {'type': 'string', 'maxLength': 5}
        with pytest.raises(ValidationError):
            validate_feature_dto(config, {'type': 'string', 'value': 'too long string'})

    def test_invalid_dto_pattern_mismatch(self):
        """String not matching pattern should fail."""
        config = {'type': 'string', 'pattern': r'^[A-Z]+$'}
        with pytest.raises(ValidationError):
            validate_feature_dto(config, {'type': 'string', 'value': 'lowercase'})


# ============================================================================
# Boolean Feature Type Tests
# ============================================================================

class TestBoolFeatureType:
    """Tests for bool feature type."""

    def test_valid_config(self):
        """Bool config should be valid."""
        config = {'type': 'bool'}
        validate_feature_config(config)

    def test_valid_config_with_labels(self):
        """Bool config with custom labels should be valid."""
        config = {
            'type': 'bool',
            'trueLabel': 'feature.available',
            'falseLabel': 'feature.unavailable'
        }
        validate_feature_config(config)

    def test_valid_dto_boolean(self):
        """Boolean DTOs should pass validation."""
        config = {'type': 'bool'}
        validate_feature_dto(config, {'type': 'bool', 'value': True})
        validate_feature_dto(config, {'type': 'bool', 'value': False})

    def test_invalid_dto_string(self):
        """Invalid string should fail validation."""
        config = {'type': 'bool'}
        with pytest.raises(ValidationError):
            validate_feature_dto(config, {'type': 'bool', 'value': 'maybe'})


# ============================================================================
# Hex Color Feature Type Tests
# ============================================================================

class TestHexColorFeatureType:
    """Tests for hex_color feature type."""

    def test_valid_config(self):
        """Hex color config should be valid."""
        config = {'type': 'hex_color'}
        validate_feature_config(config)

    def test_valid_config_with_options(self):
        """Hex color config with options should be valid."""
        config = {
            'type': 'hex_color',
            'options': [
                {'hex': '#FF0000', 'simple': 'red', 'label': 'color.red'},
                {'hex': '#00FF00', 'simple': 'green', 'label': 'color.green'}
            ],
            'allowCustom': False
        }
        validate_feature_config(config)

    def test_valid_dto_with_hex(self):
        """DTO with hex color should pass validation."""
        config = {'type': 'hex_color'}
        validate_feature_dto(config, {
            'type': 'hex_color',
            'value': {'hex': '#FF5500', 'simple': 'orange'}
        })

    def test_valid_dto_simple_only(self):
        """DTO with simple color only should pass validation."""
        config = {'type': 'hex_color'}
        validate_feature_dto(config, {
            'type': 'hex_color',
            'value': {'simple': 'red'}
        })

    def test_invalid_dto_invalid_hex(self):
        """DTO with invalid hex color should fail."""
        config = {'type': 'hex_color'}
        with pytest.raises(ValidationError):
            validate_feature_dto(config, {
                'type': 'hex_color',
                'value': {'hex': '#GGGGGG', 'simple': 'invalid'}
            })

    def test_invalid_dto_invalid_simple(self):
        """DTO with invalid simple color should fail."""
        config = {'type': 'hex_color'}
        with pytest.raises(ValidationError):
            validate_feature_dto(config, {
                'type': 'hex_color',
                'value': {'simple': 'not_a_color'}
            })


# ============================================================================
# Select Feature Type Tests
# ============================================================================

class TestSelectFeatureType:
    """Tests for select feature type."""

    def test_valid_config_single(self):
        """Single select config should be valid."""
        config = {
            'type': 'select',
            'options': [
                {'value': 'a', 'label': 'Option A'},
                {'value': 'b', 'label': 'Option B'}
            ]
        }
        validate_feature_config(config)

    def test_valid_config_with_ui_style(self):
        """Config with uiStyle should be valid."""
        config = {
            'type': 'select',
            'options': [
                {'value': 'a', 'label': 'Option A'},
                {'value': 'b', 'label': 'Option B'}
            ],
            'uiStyle': 'checkboxes',
            'minSelected': 1,
            'maxSelected': 2
        }
        validate_feature_config(config)

    def test_invalid_config_no_options(self):
        """Config without options should fail."""
        config = {'type': 'select'}
        with pytest.raises(ValidationError):
            validate_feature_config(config)

    def test_invalid_config_empty_options(self):
        """Config with empty options should fail."""
        config = {'type': 'select', 'options': []}
        with pytest.raises(ValidationError):
            validate_feature_config(config)

    def test_invalid_config_duplicate_values(self):
        """Config with duplicate option values should fail."""
        config = {
            'type': 'select',
            'options': [
                {'value': 'a', 'label': 'Option A'},
                {'value': 'a', 'label': 'Option A2'}  # Duplicate
            ]
        }
        with pytest.raises(ValidationError):
            validate_feature_config(config)

    def test_valid_dto_single_value(self):
        """Valid single select DTO should pass."""
        config = {
            'type': 'select',
            'options': [
                {'value': 'a', 'label': 'Option A'},
                {'value': 'b', 'label': 'Option B'}
            ]
        }
        validate_feature_dto(config, {'type': 'select', 'value': ['a']})

    def test_valid_dto_multiple_values(self):
        """Valid multiple select DTO should pass."""
        config = {
            'type': 'select',
            'options': [
                {'value': 'a', 'label': 'Option A'},
                {'value': 'b', 'label': 'Option B'}
            ]
        }
        validate_feature_dto(config, {'type': 'select', 'value': ['a', 'b']})

    def test_invalid_dto_not_in_options(self):
        """Value not in options should fail."""
        config = {
            'type': 'select',
            'options': [{'value': 'a', 'label': 'A'}]
        }
        with pytest.raises(ValidationError):
            validate_feature_dto(config, {'type': 'select', 'value': ['x']})

    def test_invalid_dto_too_few_selected(self):
        """Fewer than minSelected should fail."""
        config = {
            'type': 'select',
            'options': [
                {'value': 'a', 'label': 'A'},
                {'value': 'b', 'label': 'B'}
            ],
            'minSelected': 2
        }
        with pytest.raises(ValidationError):
            validate_feature_dto(config, {'type': 'select', 'value': ['a']})

    def test_invalid_dto_too_many_selected(self):
        """More than maxSelected should fail."""
        config = {
            'type': 'select',
            'options': [
                {'value': 'a', 'label': 'A'},
                {'value': 'b', 'label': 'B'},
                {'value': 'c', 'label': 'C'}
            ],
            'maxSelected': 1
        }
        with pytest.raises(ValidationError):
            validate_feature_dto(config, {'type': 'select', 'value': ['a', 'b']})


# ============================================================================
# Header Feature Type Tests
# ============================================================================

class TestHeaderFeatureType:
    """Tests for header feature type.

    Note: Header uses the feature definition's name for the title.
    """

    def test_valid_config_minimal(self):
        """Header config with just type should be valid."""
        config = {'type': 'header'}
        validate_feature_config(config)

    def test_valid_config_with_style(self):
        """Header config with style should be valid."""
        config = {
            'type': 'header',
            'style': 'l'
        }
        validate_feature_config(config)

    def test_valid_config_all_styles(self):
        """Header config should accept l, m styles."""
        for style in ['l', 'm']:
            config = {'type': 'header', 'style': style}
            validate_feature_config(config)

    def test_invalid_config_invalid_style(self):
        """Config with invalid style should fail."""
        config = {
            'type': 'header',
            'style': 'invalid_style'
        }
        with pytest.raises(ValidationError):
            validate_feature_config(config)

    def test_dto_always_valid(self):
        """Header DTO should always be valid (no user input)."""
        config = {'type': 'header'}
        validate_feature_dto(config, {'type': 'header', 'value': None})


# ============================================================================
# Hierarchical Select Feature Type Tests (Recursive Tree)
# ============================================================================

class TestHierarchicalSelectFeatureType:
    """Tests for hierarchical_select feature type with recursive tree structure."""

    def test_valid_config_simple(self):
        """Simple hierarchical select config should be valid."""
        config = {
            'type': 'hierarchical_select',
            'options': [
                {'value': 'electronics', 'label': 'cat.electronics'},
                {'value': 'clothing', 'label': 'cat.clothing'}
            ]
        }
        validate_feature_config(config)

    def test_valid_config_nested(self):
        """Nested hierarchical select config should be valid."""
        config = {
            'type': 'hierarchical_select',
            'options': [
                {
                    'value': 'electronics',
                    'label': 'cat.electronics',
                    'children': [
                        {
                            'value': 'phones',
                            'label': 'cat.phones',
                            'children': [
                                {'value': 'smartphones', 'label': 'cat.smartphones'},
                                {'value': 'feature_phones', 'label': 'cat.feature_phones'}
                            ]
                        },
                        {'value': 'laptops', 'label': 'cat.laptops'}
                    ]
                }
            ]
        }
        validate_feature_config(config)

    def test_invalid_config_no_options(self):
        """Config without options should fail."""
        config = {'type': 'hierarchical_select'}
        with pytest.raises(ValidationError):
            validate_feature_config(config)

    def test_invalid_config_empty_options(self):
        """Config with empty options should fail."""
        config = {'type': 'hierarchical_select', 'options': []}
        with pytest.raises(ValidationError):
            validate_feature_config(config)

    def test_invalid_config_duplicate_values(self):
        """Config with duplicate values at same level should fail."""
        config = {
            'type': 'hierarchical_select',
            'options': [
                {'value': 'a', 'label': 'A'},
                {'value': 'a', 'label': 'A2'}  # Duplicate
            ]
        }
        with pytest.raises(ValidationError):
            validate_feature_config(config)

    def test_invalid_config_missing_value(self):
        """Config with missing value should fail."""
        config = {
            'type': 'hierarchical_select',
            'options': [
                {'label': 'A'}  # Missing value
            ]
        }
        with pytest.raises(ValidationError):
            validate_feature_config(config)

    def test_valid_config_missing_label(self):
        """Config with missing label is valid — label defaults to value."""
        config = {
            'type': 'hierarchical_select',
            'options': [
                {'value': 'a'}  # Label is optional, defaults to value
            ]
        }
        validate_feature_config(config)  # Should not raise

    def test_valid_dto_single_level(self):
        """Valid single level selection should pass."""
        config = {
            'type': 'hierarchical_select',
            'options': [
                {'value': 'electronics', 'label': 'cat.electronics'},
                {'value': 'clothing', 'label': 'cat.clothing'}
            ]
        }
        validate_feature_dto(config, {
            'type': 'hierarchical_select',
            'value': ['electronics']
        })

    def test_valid_dto_multi_level(self):
        """Valid multi level selection should pass."""
        config = {
            'type': 'hierarchical_select',
            'options': [
                {
                    'value': 'electronics',
                    'label': 'cat.electronics',
                    'children': [
                        {
                            'value': 'phones',
                            'label': 'cat.phones',
                            'children': [
                                {'value': 'smartphones', 'label': 'cat.smartphones'}
                            ]
                        }
                    ]
                }
            ]
        }
        validate_feature_dto(config, {
            'type': 'hierarchical_select',
            'value': ['electronics', 'phones', 'smartphones']
        })

    def test_invalid_dto_unknown_value(self):
        """DTO with unknown value should fail."""
        config = {
            'type': 'hierarchical_select',
            'options': [
                {'value': 'electronics', 'label': 'cat.electronics'}
            ]
        }
        with pytest.raises(ValidationError):
            validate_feature_dto(config, {
                'type': 'hierarchical_select',
                'value': ['unknown']
            })

    def test_invalid_dto_path_continues_without_children(self):
        """DTO with path continuing past leaf should fail."""
        config = {
            'type': 'hierarchical_select',
            'options': [
                {'value': 'electronics', 'label': 'cat.electronics'}  # No children
            ]
        }
        with pytest.raises(ValidationError):
            validate_feature_dto(config, {
                'type': 'hierarchical_select',
                'value': ['electronics', 'phones']  # Trying to go deeper
            })

    def test_invalid_dto_below_min_depth(self):
        """DTO below minDepth should fail."""
        config = {
            'type': 'hierarchical_select',
            'options': [
                {
                    'value': 'electronics',
                    'label': 'cat.electronics',
                    'children': [{'value': 'phones', 'label': 'cat.phones'}]
                }
            ],
            'minDepth': 2
        }
        with pytest.raises(ValidationError):
            validate_feature_dto(config, {
                'type': 'hierarchical_select',
                'value': ['electronics']  # Only 1 level, needs 2
            })

    def test_invalid_dto_above_max_depth(self):
        """DTO above maxDepth should fail."""
        config = {
            'type': 'hierarchical_select',
            'options': [
                {
                    'value': 'a',
                    'label': 'A',
                    'children': [
                        {
                            'value': 'b',
                            'label': 'B',
                            'children': [{'value': 'c', 'label': 'C'}]
                        }
                    ]
                }
            ],
            'maxDepth': 2
        }
        with pytest.raises(ValidationError):
            validate_feature_dto(config, {
                'type': 'hierarchical_select',
                'value': ['a', 'b', 'c']  # 3 levels, max is 2
            })

    @pytest.mark.skip(reason="allowCustom feature not yet implemented in hierarchical_select")
    def test_custom_value_allowed(self):
        """Custom value should be allowed when allowCustom=True."""
        config = {
            'type': 'hierarchical_select',
            'options': [
                {'value': 'electronics', 'label': 'cat.electronics'}
            ],
            'allowCustom': True
        }
        validate_feature_dto(config, {
            'type': 'hierarchical_select',
            'value': ['custom_category']
        })

    def test_empty_value_allowed_when_not_required(self):
        """Empty value should be allowed when required=False."""
        config = {
            'type': 'hierarchical_select',
            'options': [
                {'value': 'electronics', 'label': 'cat.electronics'}
            ],
            'required': False
        }
        validate_feature_dto(config, {
            'type': 'hierarchical_select',
            'value': []
        })

    def test_empty_value_fails_when_required(self):
        """Empty value should fail when required=True."""
        config = {
            'type': 'hierarchical_select',
            'options': [
                {'value': 'electronics', 'label': 'cat.electronics'}
            ],
            'required': True
        }
        with pytest.raises(ValidationError):
            validate_feature_dto(config, {
                'type': 'hierarchical_select',
                'value': []
            })


# ============================================================================
# Date Feature Type Tests (Timestamp-based)
# ============================================================================

class TestDateFeatureType:
    """Tests for date feature type with Unix timestamp values."""

    def test_valid_config_minimal(self):
        """Minimal date config should be valid."""
        config = {'type': 'date'}
        validate_feature_config(config)

    def test_valid_config_full(self):
        """Full date config should be valid."""
        config = {
            'type': 'date',
            'precision': 'datetime',
            'minDate': 1609459200,  # 2021-01-01
            'maxDate': 1735689600,  # 2025-01-01
            'allowFuture': True,
            'allowPast': True,
            'default': 1640995200,  # 2022-01-01
            'options': [1609459200, 1640995200, 1672531200],
        }
        validate_feature_config(config)

    def test_valid_config_precision_values(self):
        """All precision values should be valid."""
        for precision in ['year', 'month', 'date', 'datetime']:
            config = {'type': 'date', 'precision': precision}
            validate_feature_config(config)

    def test_invalid_config_min_greater_than_max(self):
        """Config with minDate > maxDate should fail."""
        config = {
            'type': 'date',
            'minDate': 1735689600,  # 2025-01-01
            'maxDate': 1609459200,  # 2021-01-01
        }
        with pytest.raises(ValidationError):
            validate_feature_config(config)

    def test_invalid_config_default_before_min(self):
        """Config with default before minDate should fail."""
        config = {
            'type': 'date',
            'minDate': 1640995200,  # 2022-01-01
            'default': 1609459200,  # 2021-01-01
        }
        with pytest.raises(ValidationError):
            validate_feature_config(config)

    def test_invalid_config_default_after_max(self):
        """Config with default after maxDate should fail."""
        config = {
            'type': 'date',
            'maxDate': 1609459200,  # 2021-01-01
            'default': 1640995200,  # 2022-01-01
        }
        with pytest.raises(ValidationError):
            validate_feature_config(config)

    def test_invalid_config_both_allow_false(self):
        """Config with both allowFuture and allowPast false should fail."""
        config = {
            'type': 'date',
            'allowFuture': False,
            'allowPast': False,
        }
        with pytest.raises(ValidationError):
            validate_feature_config(config)

    def test_valid_dto(self):
        """Valid date DTO with timestamp should pass."""
        config = {'type': 'date'}
        validate_feature_dto(config, {
            'type': 'date',
            'value': 1640995200  # 2022-01-01
        })

    def test_valid_dto_none(self):
        """None value should be valid."""
        config = {'type': 'date'}
        validate_feature_dto(config, {
            'type': 'date',
            'value': None
        })

    def test_invalid_dto_below_min(self):
        """Timestamp below minDate should fail."""
        config = {
            'type': 'date',
            'minDate': 1640995200,  # 2022-01-01
        }
        with pytest.raises(ValidationError):
            validate_feature_dto(config, {
                'type': 'date',
                'value': 1609459200  # 2021-01-01
            })

    def test_invalid_dto_above_max(self):
        """Timestamp above maxDate should fail."""
        config = {
            'type': 'date',
            'maxDate': 1609459200,  # 2021-01-01
        }
        with pytest.raises(ValidationError):
            validate_feature_dto(config, {
                'type': 'date',
                'value': 1640995200  # 2022-01-01
            })

    def test_dto_string_normalized_to_none(self):
        """Non-integer string value is normalized to None (accepted)."""
        config = {'type': 'date'}
        # String values are normalized to None by normalize_dto
        validate_feature_dto(config, {
            'type': 'date',
            'value': 'not-a-timestamp'
        })

    def test_dto_string_integer_normalized(self):
        """String integer is normalized to int."""
        config = {'type': 'date'}
        validate_feature_dto(config, {
            'type': 'date',
            'value': '1640995200'  # String but valid int
        })
