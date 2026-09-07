"""Localized error catalogs (``translations/errors.<lang>.json``) — the parity gate.

This module registers thirteen ``error.*`` keys and, since 0.9.3, ships their
``ru``/``es`` catalogs. It has no Django app: a host never lists it in
INSTALLED_APPS, it enters the deployment's error canon purely by import, and
until stapel-core 0.60.8 the loader had no way to find a catalog it shipped.
0.60.8 walks the package directory of every registered error owner, so the
catalogs beside this file are discovered with no per-host configuration — and
until this release there were none to discover, which is why every one of
these codes rendered as its English registry literal on a localized host.

The gate is parity in both directions, per shipped language: the loader
resolves this package as the owner of exactly the registry's keys, every one
of them is translated, nothing but them is, every text keeps the canon's
``{param}`` slots, and the shipped catalog set is exactly the gated one. The
files are written in the ``dump_catalog`` byte-stable format so a
regeneration is a no-op diff.

Wording is authored here, not seeded: the stapel-translate builtin corpus
carries no ``feature_*`` key, and a module owns the strings for the keys it
registers.
"""
import json
from pathlib import Path

import pytest
from stapel_core.i18n import (
    catalog_search_dirs,
    dump_catalog,
    owned_keys,
    owner_of_dir,
    source_owners,
    source_texts,
)
from stapel_core.i18n.domains import params_of

from stapel_attributes.errors import ATTRIBUTES_ERRORS

REPO = Path(__file__).resolve().parent.parent
TRANSLATIONS = REPO / "translations"
#: The languages this module ships error catalogs in; en is the registry literal.
TARGET_LANGUAGES = ["ru", "es"]


def _catalog(lang: str) -> dict[str, str]:
    path = TRANSLATIONS / f"errors.{lang}.json"
    assert path.is_file(), f"{path.name} is missing"
    return json.loads(path.read_text(encoding="utf-8"))


def test_the_loader_finds_this_package_without_installed_apps():
    """The discovery path this release depends on, asserted rather than assumed.

    This package has no AppConfig, so INSTALLED_APPS can never reach it. If
    ``catalog_search_dirs`` stops including error-owner roots, the catalogs
    below go invisible again and every other assertion here still passes.
    """
    roots = {d.resolve() for d in catalog_search_dirs()}
    assert REPO.resolve() in roots, (
        "this package is not a catalog search root — stapel-core >= 0.60.8 "
        f"discovers error owners; got {sorted(str(r) for r in roots)}"
    )
    assert owner_of_dir(TRANSLATIONS) == "stapel_attributes"


def test_the_owned_key_set_is_the_registry():
    """What the loader thinks this package owns == what ``errors.py`` registers."""
    owned = owned_keys(
        source_texts("errors"), source_owners("errors"), owner_of_dir(TRANSLATIONS),
    )
    assert set(owned) == set(ATTRIBUTES_ERRORS)


@pytest.mark.parametrize("lang", TARGET_LANGUAGES)
def test_every_owned_key_is_translated(lang):
    catalog = _catalog(lang)
    missing = sorted(k for k in ATTRIBUTES_ERRORS if k not in catalog)
    assert not missing, f"{lang} catalog missing {len(missing)} key(s): {missing}"
    empty = sorted(k for k, v in catalog.items() if not (v or "").strip())
    assert not empty, f"{lang}: empty translations: {empty}"


@pytest.mark.parametrize("lang", TARGET_LANGUAGES)
def test_this_module_translates_only_its_own_keys(lang):
    """No fleet-wide copies: a reader resolves a foreign key from its owner."""
    stray = sorted(k for k in _catalog(lang) if k not in ATTRIBUTES_ERRORS)
    assert not stray, f"{lang}: not this module's keys: {stray}"


@pytest.mark.parametrize("lang", TARGET_LANGUAGES)
def test_translations_preserve_placeholders(lang):
    for key, text in _catalog(lang).items():
        if key not in ATTRIBUTES_ERRORS:  # a foreign key is the other test's failure
            continue
        assert set(params_of(text)) == set(params_of(ATTRIBUTES_ERRORS[key])), \
            f"{lang}: {key}"


@pytest.mark.parametrize("lang", TARGET_LANGUAGES)
def test_catalogs_are_byte_stable(lang):
    """Sorted keys, 2-space indent, non-ASCII kept, one trailing newline."""
    path = TRANSLATIONS / f"errors.{lang}.json"
    assert path.read_text(encoding="utf-8") == dump_catalog(_catalog(lang))


def test_every_shipped_catalog_is_a_target_language():
    """A catalog dropped in for a language this gate does not divide by is
    a catalog nothing keeps complete."""
    shipped = {p.name for p in TRANSLATIONS.glob("errors.*.json")}
    assert shipped == {f"errors.{lang}.json" for lang in TARGET_LANGUAGES}


def test_the_wheel_ships_the_catalogs():
    """package-data must carry ``translations/*.json``.

    Both siblings that did this work shipped a wheel without its catalogs
    first: the files are in git, the gate is green, and the host installs a
    package with an empty ``translations/``.
    """
    import tomllib

    pyproject = tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))
    patterns = pyproject["tool"]["setuptools"]["package-data"]["stapel_attributes"]
    assert "translations/*.json" in patterns
