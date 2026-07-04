"""Package-level public API (PEP 562 lazy exports) and import hygiene."""
import os
import subprocess
import sys

import stapel_attributes


class TestLazyExports:
    def test_all_declares_public_api(self):
        assert stapel_attributes.__all__ == [
            # Settings
            "attributes_settings",
            # Base abstractions
            "BaseFeatureType",
            "DaoMeta",
            "DictDataclassSerializer",
            "FeatureDef",
            "dataclass_to_dict_no_none",
            # Structured errors & results
            "FeatureValidationError",
            "FeatureValidationResult",
            "ValidationBatchResult",
            "ValidationErrorCode",
            "ValidationStatus",
            # Registry
            "register_feature_type",
            "registered_types",
            "get_feature_type",
            "get_all_feature_types",
            "get_all_type_slugs",
            # Parse / convert
            "parse_config",
            "parse_dto",
            "dao_to_dict",
            "validate_feature_config",
            "validate_feature_dto",
            "dto_to_dao",
            "normalize_feature_dto",
            "get_default_value",
            "format_feature_value",
            "collect_translation_keys_for_feature",
            "collect_all_builtin_translation_keys",
            # Validation pipeline (configs -> DTO -> DAO)
            "coerce_feature_defs",
            "get_feature_slug",
            "build_feature_lookup",
            "validate_dto",
            "normalize_to_dao",
            "validate_dto_structured",
            "validate_configs_structured",
            "validate_dao_structured",
            "validate_description",
            # Polymorphic serializer factories
            "get_feature_config_serializer_class",
            "get_feature_dto_serializer_class",
            "get_feature_dao_serializer_class",
            "get_feature_config_proxy_serializer",
            "get_feature_dto_proxy_serializer",
            "get_feature_dao_proxy_serializer",
        ]

    def test_settings_resolve(self):
        from stapel_attributes.conf import attributes_settings

        assert stapel_attributes.attributes_settings is attributes_settings

    def test_every_export_resolves(self):
        for name in stapel_attributes.__all__:
            assert getattr(stapel_attributes, name) is not None

    def test_unknown_attribute_raises(self):
        try:
            stapel_attributes.nonexistent_export
        except AttributeError as exc:
            assert "nonexistent_export" in str(exc)
        else:
            raise AssertionError("expected AttributeError")


class TestImportWithoutDjangoSettings:
    def test_package_import_is_django_free(self):
        """`import stapel_attributes` must not import Django nor require settings."""
        env = {k: v for k, v in os.environ.items() if k != "DJANGO_SETTINGS_MODULE"}
        code = (
            "import sys\n"
            "import stapel_attributes\n"
            'polluted = [m for m in sys.modules if m == "django" or m.startswith("django.")]\n'
            'assert not polluted, f"django imported at package import time: {polluted}"\n'
        )
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            env=env,
            cwd=os.path.dirname(sys.executable),
        )
        assert result.returncode == 0, result.stderr
