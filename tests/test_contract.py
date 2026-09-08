"""Drift gates for this library's generated contract artifacts.

Two of them: ``docs/errors.json`` (the error-key registry, emitted by
``stapel_attributes._codegen`` — see the section below) and ``docs/llms.txt``,
the fifth contract artifact (stapel_tools.llms_txt).

``docs/capabilities.json`` in this module is otherwise HAND-WRITTEN (authored
in the stapel-catalog sweep, commit 9fce193) — there is no gate registry and
no codegen step to derive axes from, so this gate does NOT cover
capabilities.json itself (that is tests/test_capabilities_surface.py's job,
for the derived ``surface`` section). It covers ``docs/llms.txt``, which IS
generated (from capabilities.json) and therefore CAN drift the moment the
hand-written source OR the derived surface changes underneath it without a
`make contract` re-run — exactly the silent-rot failure mode the fifth
artifact exists to catch.

LLMS_TXT_BUDGET matches the Makefile's ``--budget 7000`` — see its comment
there for why the 59-entry surface (this L1 library is almost entirely
surface), plus the 55-key error table 0.9.4 added, need headroom over the
generator's default 4000-token ceiling.
"""
import json
import sys
from pathlib import Path

try:
    import stapel_tools  # noqa: F401  (probe: the emitter must be importable)
except ImportError as exc:  # pragma: no cover - environment failure, not a branch
    # NOT pytest.importorskip. A drift gate that skips when its emitter is
    # missing reports `1 skipped`, exits 0, and disappears among a hundred
    # green tests — making "the tool is absent" indistinguishable from "there
    # is no drift". A gate that cannot run has FAILED; it has not passed.
    raise RuntimeError(
        "llms.txt drift gate cannot run: stapel-tools is not importable, and "
        "it carries the emitter this gate measures drift against. Install it "
        "(workspace venv, or `pip install stapel-tools`) and re-run. This is "
        "a hard failure on purpose — a skipped drift gate is silently no "
        "gate."
    ) from exc

from stapel_tools.llms_txt import load_inputs, render  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
COMMITTED = REPO / "docs" / "llms.txt"
LLMS_TXT_BUDGET = 7000


def test_llms_txt_committed():
    assert COMMITTED.is_file(), "missing docs/llms.txt — run `make contract`"


def test_llms_txt_has_no_drift():
    rendered = render(load_inputs(REPO), budget=LLMS_TXT_BUDGET)
    assert COMMITTED.read_text() == rendered, (
        "docs/llms.txt is stale — run `make contract` and commit it"
    )


def test_llms_txt_emission_is_deterministic():
    """Two independent renders are byte-identical (the drift gate is meaningful)."""
    a = render(load_inputs(REPO), budget=LLMS_TXT_BUDGET)
    b = render(load_inputs(REPO), budget=LLMS_TXT_BUDGET)
    assert a == b


# --- docs/errors.json — the error-key registry (0.9.4) -----------------------
#
# The artifact every sibling library already emits, and the one this library
# had no harness for: `translations/errors.{ru,es}.json` shipped since 0.9.3
# while nothing declared WHICH codes those files were supposed to cover, so a
# consumer that wanted the registry had to read it out of a HOST's artifact
# (stapel-listings' or stapel-categories', where these thirteen keys arrive as
# borrowed entries) or hand-author the list. `@stapel/attributes-react` did the
# second, which is why thirteen strings had two sources.
#
# Emitted by `python -m stapel_attributes._codegen`, which is the shared
# `generate_error_keys` path (stapel_tools.codegen.emit_errors) with this
# library named in STAPEL_ERROR_MODULES — core's seam for an error owner that
# is not a Django app.

ERRORS_JSON = REPO / "docs" / "errors.json"


def _declared() -> dict:
    return {entry["code"]: entry for entry in json.loads(ERRORS_JSON.read_text())}


def test_the_registry_artifact_is_committed():
    assert ERRORS_JSON.is_file(), "missing docs/errors.json — run `make contract`"


def test_every_key_this_library_owns_is_declared():
    """Registry -> artifact, with the OWNER, which is the half that matters.

    A key attributed to anyone else here is a key whose translations a host
    would look for in the wrong wheel — and, on the frontend, a key the pair's
    generator would leave out of its locale bundles as somebody else's.
    """
    from stapel_attributes.errors import ATTRIBUTES_ERRORS

    declared = _declared()
    assert ATTRIBUTES_ERRORS, "the attributes registry came back empty"
    for code, text in ATTRIBUTES_ERRORS.items():
        assert code in declared, f"{code} missing from docs/errors.json"
        assert declared[code]["owner"] == "stapel_attributes"
        assert declared[code]["en"] == text


def test_the_artifact_declares_only_this_library_and_core():
    """No third owner can appear: this library imports no sibling's errors.

    The emission instance installs core's app and names this library in
    STAPEL_ERROR_MODULES and nothing else. A new owner in the artifact means
    the harness grew a dependency nobody declared — which would put a sibling's
    keys into `@stapel/attributes-react`'s bundles under this library's name.
    """
    owners = {entry["owner"] for entry in _declared().values()}
    assert owners == {"stapel_attributes", "stapel_core"}, sorted(owners)


def test_the_shipped_catalogues_cover_exactly_the_owned_keys():
    """The two halves of the contract, read off the artifact rather than a list.

    ``check_registry_catalog_pairing`` already refuses to EMIT an artifact
    whose declared codes an owner's catalogue misses. This is the other
    direction: a translated key the artifact does not declare is a string no
    consumer can ever reach, and the generator would fail on it rather than
    quietly drop it.
    """
    owned = {
        code
        for code, entry in _declared().items()
        if entry["owner"] == "stapel_attributes"
    }
    for lang in ("ru", "es"):
        path = REPO / "translations" / f"errors.{lang}.json"
        catalogue = json.loads(path.read_text(encoding="utf-8"))
        assert set(catalogue) == owned, (
            f"translations/errors.{lang}.json and docs/errors.json disagree: "
            f"only in catalogue {sorted(set(catalogue) - owned)}, "
            f"only in artifact {sorted(owned - set(catalogue))}"
        )


def test_the_registry_artifact_has_no_drift(tmp_path):
    """Re-emit and diff — the gate `make contract-check` runs, in the matrix.

    A subprocess because Django settings are process-global: this suite's
    ``conftest.py`` deliberately configures an instance with no stapel app,
    and the emission needs core's. Not pinned to a Python minor either, unlike
    the pair-backends' schema emission — the registry renders identically on
    every interpreter, which is what lets this run on all four.
    """
    import subprocess

    result = subprocess.run(
        [sys.executable, "-m", "stapel_attributes._codegen", "--out", str(tmp_path)],
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "errors.json").read_text() == ERRORS_JSON.read_text(), (
        "docs/errors.json is stale — run `make contract` and commit it"
    )


# --- README.md — the sixth artifact (tracker #257) ---------------------------
#
# README.md is assembled by ``stapel_tools.readme`` from docs/readme.md (the
# human half: what this L1 library is and how to think about it) plus the
# contract documents above (badges, version, surface counts, doc links).
# Two facts (HTTP operations, documented flows) are legitimately absent for
# this L1 library — stapel_tools.readme omits zero-valued rows rather than
# printing 0, so their absence here is not a bug. The error-code row is no
# longer one of them: docs/errors.json exists as of 0.9.4, and the badge row
# carries its 55.

def test_readme_is_assembled_and_has_no_drift():
    from stapel_tools.readme import load_inputs, render, static_languages

    inputs = load_inputs(REPO)
    languages = static_languages(REPO)
    assert languages == ["en"], "expected exactly the English static body docs/readme.md"
    committed = (REPO / "README.md").read_text()
    assert committed == render(REPO, inputs, "en", languages), (
        "README.md drifted — run `make contract` and commit README.md "
        "(edit prose in docs/readme.md, never README.md itself)"
    )


def test_readme_version_matches_the_package():
    """The #226 gate, at the point where the number is published."""
    import tomllib

    from stapel_tools.readme import load_inputs, resolve_version

    pyproject = tomllib.loads((REPO / "pyproject.toml").read_text())
    assert resolve_version(load_inputs(REPO)) == pyproject["project"]["version"]
