"""Open-registry semantics: built-ins + EXTRA_TYPES + runtime registration.

These are the extension-point tests the library standard mandates: registry
merge, dotted-path loading (module and class flavors), runtime
``register_feature_type``, introspection via ``registered_types()``, and
serializer-factory rebuild after late registrations.
"""

import sys

import pytest
from django.test import override_settings

from stapel_attributes import registry
from stapel_attributes.registry import (
    collect_all_builtin_translation_keys,
    get_all_type_slugs,
    get_feature_type,
    register_feature_type,
    registered_types,
    validate_feature_dto,
)
from stapel_attributes.serializers import (
    get_feature_dto_serializer_class,
)
from stapel_attributes.tests.sample_types import RatingFeatureType

pytestmark = pytest.mark.usefixtures("registry_snapshot")


class TestRuntimeRegistration:
    def test_register_feature_type_runtime(self):
        register_feature_type(RatingFeatureType)
        ft = get_feature_type('rating')
        assert ft.slug == 'rating'
        assert 'rating' in get_all_type_slugs()

    def test_registered_types_introspection(self):
        register_feature_type(RatingFeatureType)
        types = registered_types()
        assert 'rating' in types
        assert 'int' in types  # built-ins still present

    def test_registered_types_returns_copy(self):
        types = registered_types()
        types.pop('int')
        assert 'int' in registered_types()

    def test_reregistering_slug_overrides(self):
        register_feature_type(RatingFeatureType)

        class RatingV2(RatingFeatureType):
            name = 'Rating v2'

        register_feature_type(RatingV2)
        assert get_feature_type('rating').name == 'Rating v2'

    def test_custom_type_flows_through_pipeline(self):
        register_feature_type(RatingFeatureType)
        # Config parse + DTO validation against the custom type
        validate_feature_dto({'type': 'rating', 'max': 5}, {'type': 'rating', 'value': 3})
        from stapel_attributes.exceptions import FeatureValidationError
        with pytest.raises(FeatureValidationError) as exc:
            validate_feature_dto({'type': 'rating', 'max': 5}, {'type': 'rating', 'value': 9})
        assert exc.value.ref_value == 5

    def test_builtin_translation_keys_include_registered_types(self):
        keys = collect_all_builtin_translation_keys()
        assert 'feature.bool.true' in keys
        assert 'feature.bool.false' in keys
        assert 'feature.date.name' in keys
        assert 'feature.rating.name' not in keys

        register_feature_type(RatingFeatureType)
        assert 'feature.rating.name' in collect_all_builtin_translation_keys()


class TestExtraTypesSetting:
    def test_class_path_entry(self):
        with override_settings(STAPEL_ATTRIBUTES={
            "EXTRA_TYPES": ["stapel_attributes.tests.sample_types.RatingFeatureType"],
        }):
            assert 'rating' in get_all_type_slugs()
            assert get_feature_type('rating').name == 'Rating'

    def test_module_path_entry(self):
        sys.modules.pop("stapel_attributes.tests.sample_types_module", None)
        try:
            with override_settings(STAPEL_ATTRIBUTES={
                "EXTRA_TYPES": ["stapel_attributes.tests.sample_types_module"],
            }):
                assert 'sticker' in get_all_type_slugs()
        finally:
            sys.modules.pop("stapel_attributes.tests.sample_types_module", None)

    def test_merge_over_builtins(self):
        with override_settings(STAPEL_ATTRIBUTES={
            "EXTRA_TYPES": ["stapel_attributes.tests.sample_types.RatingFeatureType"],
        }):
            slugs = get_all_type_slugs()
            # Adding an extra type never removes the built-ins
            for builtin in ['bool', 'date', 'float', 'header', 'hex_color',
                            'hierarchical_select', 'int', 'select', 'string']:
                assert builtin in slugs

    def test_empty_entries_ignored(self):
        with override_settings(STAPEL_ATTRIBUTES={"EXTRA_TYPES": ["", None]}):
            assert 'int' in get_all_type_slugs()  # no crash

    def test_bad_path_raises_import_error(self):
        with override_settings(STAPEL_ATTRIBUTES={
            "EXTRA_TYPES": ["no.such.module.NoSuchType"],
        }):
            with pytest.raises(ImportError) as exc:
                get_all_type_slugs()
            assert "no.such.module.NoSuchType" in str(exc.value)

    def test_non_feature_type_class_raises(self):
        with override_settings(STAPEL_ATTRIBUTES={
            "EXTRA_TYPES": ["stapel_attributes.tests.sample_types.RatingConfig"],
        }):
            with pytest.raises(ImportError) as exc:
                get_all_type_slugs()
            assert "BaseFeatureType" in str(exc.value)

    def test_loading_is_idempotent(self):
        with override_settings(STAPEL_ATTRIBUTES={
            "EXTRA_TYPES": ["stapel_attributes.tests.sample_types.RatingFeatureType"],
        }):
            v1 = None
            assert 'rating' in get_all_type_slugs()
            v1 = registry._version
            assert 'rating' in get_all_type_slugs()  # second access: no re-registration
            assert registry._version == v1


class TestSerializerFactoriesFollowRegistry:
    def test_dto_serializer_mapping_includes_late_registration(self):
        before = get_feature_dto_serializer_class()
        assert 'rating' not in before().serializer_mapping

        register_feature_type(RatingFeatureType)

        after = get_feature_dto_serializer_class()
        assert 'rating' in after().serializer_mapping

        # And the new class validates the custom payload
        serializer = after(data={'type': 'rating', 'value': 4})
        assert serializer.is_valid(), serializer.errors

    def test_serializer_class_is_cached_between_calls(self):
        a = get_feature_dto_serializer_class()
        b = get_feature_dto_serializer_class()
        assert a is b

    def test_proxy_serializers_rebuild(self):
        from stapel_attributes.serializers import get_feature_config_proxy_serializer

        before = get_feature_config_proxy_serializer()
        register_feature_type(RatingFeatureType)
        after = get_feature_config_proxy_serializer()
        assert after is not before
