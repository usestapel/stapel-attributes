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
        # ---- Admin UI seams (docs/attributes-admin-ui.md §4) ----
        # Extra/override admin locales, MERGED over built-in en+ru. Each entry
        # maps a language code to a static path or an inline {key: text} dict;
        # a partial dict supplements the en base (no fork).
        "ADMIN_LOCALES": {},
        # Override the Django config widget per use, MERGED (dotted paths):
        # {"<name>": "myapp.widgets.MyConfigEditorWidget"}. Empty -> the builtin.
        "ADMIN_WIDGETS": {},
        # Extra assets appended to the widget Media (host restyle/behaviour).
        "ADMIN_EXTRA_CSS": [],
        "ADMIN_EXTRA_JS": [],
    },
    import_strings=(),
)

__all__ = ["attributes_settings"]
