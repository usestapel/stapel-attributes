def pytest_configure(config):
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            SECRET_KEY="test-secret-key-not-for-production",
            # Library kind: stapel_attributes ships no models/apps, so it is
            # deliberately NOT in INSTALLED_APPS.
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
                "rest_framework",
            ],
            DATABASES={
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": ":memory:",
                }
            },
            DEFAULT_AUTO_FIELD="django.db.models.BigAutoField",
            USE_TZ=True,
            STATIC_URL="/static/",
        )
        import django
        django.setup()


import pytest  # noqa: E402


@pytest.fixture
def registry_snapshot():
    """Snapshot the effective type registry and restore it after the test.

    Use in any test that registers extra types (runtime or EXTRA_TYPES) so
    registrations never leak between tests.
    """
    from stapel_attributes import registry

    registry._ensure_loaded()
    types_snapshot = dict(registry._FEATURE_TYPES)
    extras_snapshot = set(registry._loaded_extra_paths)
    yield
    registry._FEATURE_TYPES.clear()
    registry._FEATURE_TYPES.update(types_snapshot)
    registry._loaded_extra_paths.clear()
    registry._loaded_extra_paths.update(extras_snapshot)
    registry._version += 1
