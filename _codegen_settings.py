"""Django settings for the stapel-attributes contract-emission harness.

This L1 library has no Django app, no models and no HTTP surface of its own,
so there is no ``docs/schema.json`` and no ``docs/flows.json`` to emit. The one
machine artifact it does have is ``docs/errors.json`` — the error-key registry
(``generate_error_keys``), which every sibling library already emits and which
``@stapel/attributes-react`` generates its error bundles from.

Why a settings module of its own rather than ``conftest.py``'s:

* ``conftest.py`` deliberately installs no stapel app — the suite exercises the
  typed-attribute engine, which needs neither. Emission does: core's Django app
  is what ``autodiscover_modules('errors')`` walks, and the artifact must
  describe the registry a HOST resolves rather than the subset a library-only
  process happens to have imported.
* ``stapel_attributes`` is not in ``INSTALLED_APPS`` and cannot be — it is a
  library, not an app — so autodiscovery can never reach its ``errors`` module.
  ``STAPEL_ERROR_MODULES`` is core's declared seam for exactly that case, and
  naming this module there is what makes the emission deterministic instead of
  a side effect of whichever serializer was imported first.

Unlike the pair-backends' harnesses this one is NOT pinned to a Python minor:
the errors artifact is rendered from the registry, not by drf-spectacular, so
it is byte-identical on every interpreter — which is what lets the drift gate
run across the whole test matrix instead of only in the release loop.
"""
from __future__ import annotations


def settings_kwargs() -> dict:
    """The ``settings.configure(**kwargs)`` for the emission instance."""
    from stapel_core.testing import BASE_REST_FRAMEWORK

    return dict(
        SECRET_KEY="test-secret-key-not-for-production",
        INSTALLED_APPS=[
            "django.contrib.contenttypes",
            "django.contrib.auth",
            # Core's app carries the cross-cutting error registry and the
            # catalogue loader the emission's pairing gate reads.
            "stapel_core.django.apps.CommonDjangoConfig",
            "rest_framework",
        ],
        STATIC_URL="/static/",
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:",
            }
        },
        DEFAULT_AUTO_FIELD="django.db.models.BigAutoField",
        USE_TZ=True,
        REST_FRAMEWORK={
            "EXCEPTION_HANDLER": BASE_REST_FRAMEWORK["EXCEPTION_HANDLER"],
        },
        # The seam for an error owner outside INSTALLED_APPS. Without it the
        # thirteen keys this library owns enter the registry only if something
        # else imported its serializers first, and the artifact would carry
        # them or not depending on import order.
        STAPEL_ERROR_MODULES=["stapel_attributes.errors"],
    )
