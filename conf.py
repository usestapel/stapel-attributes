"""Settings namespace for stapel-attributes.

All configuration is read through ``attributes_settings`` (lazily, at call
time) — never via module-level ``os.getenv`` (values would freeze at import).
Resolution order per key: ``settings.STAPEL_ATTRIBUTES`` dict -> flat Django
setting of the same name -> environment variable -> default below.
"""
from stapel_core.conf import AppSettings

attributes_settings = AppSettings(
    "STAPEL_ATTRIBUTES",
    defaults={
        # Extra feature types MERGED over the built-ins (open registry).
        # Each entry is a dotted path to either a BaseFeatureType subclass
        # or a module whose import registers types via @register_feature_type.
        # Loaded lazily on first registry access; loading is additive.
        "EXTRA_TYPES": [],
    },
    import_strings=(),
)

__all__ = ["attributes_settings"]
