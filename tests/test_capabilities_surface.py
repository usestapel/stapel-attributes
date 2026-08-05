"""Drift gate for the `surface` section of ``docs/capabilities.json``.

``stapel-attributes`` has no HTTP surface of its own (no models, views, urls) —
its whole reason to exist is a set of functions a product calls instead of
writing its own type dispatch, validation, normalization and display
formatting. Before this section existed, that surface was documented only in
docstrings and the module's own ``__all__`` (locked down by
``tests/test_public_api.py``); nothing in the module's *contract* could say,
machine-readably, "here is what to call instead of reinventing this" — exactly
the gap discoverability-design.md §1.2 describes: a mechanism a contract
reader cannot find is a mechanism about to be reinvented.

``surface`` names every module-level public function in the files declared as
``surface_roots`` in ``docs/capabilities.meta.json``, each with one curated
line saying when to reach for it (and, where one exists, what outside symbol
it displaces). The entry set is derived by AST — a new public function in one
of those files shows up here by itself and fails emission until somebody
explains it.

Honest boundary: the REST of this module's ``capabilities.json`` is still
hand-written (no gate registry, no ``docs/schema.json``), so only
``module``/``version``/``surface`` are gated below.
"""
import json
from pathlib import Path

import pytest

try:
    import stapel_tools  # noqa: F401  (probe: the emitter must be importable)
except ImportError as exc:  # pragma: no cover - environment failure, not a branch
    # NOT pytest.importorskip. A drift gate that skips when its emitter is
    # missing reports `1 skipped`, exits 0, and disappears among a hundred
    # green tests — exactly how an unadopted mechanism could stay unadopted
    # with nothing red anywhere to say so. A gate that cannot run has FAILED;
    # it has not passed.
    raise RuntimeError(
        "capabilities surface drift gate cannot run: stapel-tools is not "
        "importable, and it carries the capabilities emitter this gate "
        "measures drift against. Install it (workspace venv, or `pip install "
        "stapel-tools`) and re-run. This is a hard failure on purpose — a "
        "skipped drift gate is silently no gate."
    ) from exc

from stapel_tools.surface import _stable_json, load_meta, patch_capabilities  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
COMMITTED = REPO / "docs" / "capabilities.json"


def _emitted() -> dict:
    try:
        return patch_capabilities(REPO, load_meta(REPO))
    except SystemExit as exc:  # the LOUD rule — report it, don't bury it
        pytest.fail(f"capabilities emission refused: {exc}", pytrace=False)


def test_no_drift():
    assert COMMITTED.read_text() == _stable_json(_emitted()), (
        "docs/capabilities.json is stale — run `make contract` and commit it"
    )


def test_version_tracks_pyproject():
    import tomllib

    pyproject = tomllib.loads((REPO / "pyproject.toml").read_text())
    assert json.loads(COMMITTED.read_text())["version"] == (
        pyproject["project"]["version"]
    )


def test_surface_entries_have_kind_and_intent():
    surface = json.loads(COMMITTED.read_text())["surface"]
    assert surface, "expected a non-empty surface — this module is almost entirely surface"
    for entry in surface:
        assert entry["kind"] in ("gate_function", "predicate", "factory"), entry
        assert entry["intent"].strip(), entry


def test_a_new_public_function_cannot_slip_in_unexplained():
    """The set is derived, so the gate is not "did somebody remember to list
    it" but "does every public function in the declared roots have a line"."""
    from stapel_tools.surface import scan_functions

    meta = load_meta(REPO)
    declared = {e["name"] for e in json.loads(COMMITTED.read_text())["surface"]}
    for root in meta["surface_roots"]:
        assert root["select"] == "functions", root
        found = set(scan_functions(REPO / root["path"]))
        assert found <= declared, (
            f"{root['path']} exports {found - declared} with no curated intent "
            "in docs/capabilities.meta.json"
        )
