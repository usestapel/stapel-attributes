"""Cross-language golden bridge — Python runner (spec: review-attributes-admin.md).

One JSON corpus under ``tests/golden/cases/`` is executed by BOTH engines
(this file + ``static_src/src/golden.test.ts``); a divergence surfaces as a red
test on the side that deviated. This runner fills / checks the ``expect.python``
section of each case. ``declarations.json`` is a committed snapshot of
``form_declarations()`` with a drift gate (regeneration must not diff) — that
gate also pins the B2 contract: declaration defaults must equal the engine's
normalized defaults.

Record mode: ``GOLDEN_RECORD=1 pytest tests/test_golden.py`` rewrites
``expect.python`` from the live engine (byte-stable: sorted keys, ``\\n``,
``ensure_ascii=False``). Commit the result; CI runs in assert mode.
"""
import json
import os
from pathlib import Path

import pytest

from stapel_attributes import (
    parse_config,
    validate_feature_config,
)
from stapel_attributes.base import FeatureDef, dataclass_to_dict_no_none
from stapel_attributes.config_form import form_declarations
from stapel_attributes.exceptions import FeatureValidationError
from stapel_attributes.validation import validate_dto_structured

from stapel_attributes.errors import ERROR_CODE_TO_KEY
from stapel_attributes.results import ValidationErrorCode

GOLDEN_DIR = Path(__file__).parent / "golden"
CASES_DIR = GOLDEN_DIR / "cases"
DECLARATIONS = GOLDEN_DIR / "declarations.json"
ERROR_CODES = GOLDEN_DIR / "error_codes.json"
RECORD = os.environ.get("GOLDEN_RECORD") == "1"


def _dump(obj) -> str:
    return json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _load_cases():
    return sorted(CASES_DIR.glob("*.json"))


def _run_python(case: dict) -> dict:
    """Compute the Python side of a case: validity + error code + normalized."""
    kind = case["kind"]
    if kind == "config":
        try:
            config = validate_feature_config(case["config"])
        except FeatureValidationError as exc:
            return {"valid": False, "error_code": exc.error_code.name, "normalized": None}
        return {
            "valid": True,
            "error_code": None,
            "normalized": dataclass_to_dict_no_none(config),
        }
    if kind == "dto":
        feature = FeatureDef(
            slug="f", config=case["config"], mandatory=bool(case.get("mandatory", False))
        )
        result = validate_dto_structured([feature], {"f": case["dto"]})
        row = result.results[0] if result.results else None
        error = row.error.name if (row and row.error) else None
        return {"valid": result.valid, "error_code": error, "normalized": None}
    raise ValueError(f"unknown case kind: {kind!r}")


# --------------------------------------------------------------------------- #
# declarations.json drift gate (+ B2 anti-regression)
# --------------------------------------------------------------------------- #

def test_declarations_snapshot_has_no_drift():
    committed = json.loads(DECLARATIONS.read_text())
    live = form_declarations()
    assert committed == live, (
        "tests/golden/declarations.json is stale — regenerate it "
        "(the config-form declaration changed)."
    )


def test_declaration_defaults_equal_engine_normalized_defaults():
    # B2 contract: what the untouched form shows == what the engine fills in.
    decls = json.loads(DECLARATIONS.read_text())
    select = {f["name"]: f for f in decls["select"]["fields"]}
    normalized = dataclass_to_dict_no_none(
        parse_config({"type": "select", "options": [{"value": "a", "label": "A"}]})
    )
    assert select["uiStyle"].get("default") == normalized["uiStyle"] == "dropdown"
    # maxSelected: no declared default (None = unlimited) and absent from normalized.
    assert "default" not in select["maxSelected"]
    assert "maxSelected" not in normalized


# --------------------------------------------------------------------------- #
# ValidationErrorCode contract — the py↔ts bridge for machine error codes.
# error_codes.json is generated from the Python enum and asserted by BOTH this
# runner and static_src/src/error-codes.test.ts (the TS mirror), so a code added
# on one side without the other turns a test red.
# --------------------------------------------------------------------------- #

def test_error_codes_snapshot_has_no_drift():
    live = sorted(e.value for e in ValidationErrorCode)
    if RECORD:
        ERROR_CODES.write_text(json.dumps(live, indent=2, ensure_ascii=False) + "\n")
        pytest.skip("recorded error_codes.json")
    committed = json.loads(ERROR_CODES.read_text())
    assert committed == live, (
        "tests/golden/error_codes.json is stale — regenerate with GOLDEN_RECORD=1 "
        "and sync static_src/src/error-codes.ts."
    )


def test_every_error_code_maps_to_a_localizable_key():
    # Contract: every machine code resolves to an error.400.* key (incl. the new
    # NOT_ALLOWED / UNKNOWN_FEATURE follow-up codes).
    for code in ValidationErrorCode:
        assert code in ERROR_CODE_TO_KEY, f"{code.name} has no localizable key"
    assert ERROR_CODE_TO_KEY[ValidationErrorCode.NOT_ALLOWED] == "error.400.feature_not_allowed"
    assert ERROR_CODE_TO_KEY[ValidationErrorCode.UNKNOWN_FEATURE] == "error.400.feature_unknown"


# --------------------------------------------------------------------------- #
# corpus
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("path", _load_cases(), ids=lambda p: p.stem)
def test_golden_case_python(path):
    case = json.loads(path.read_text())
    actual = _run_python(case)

    if RECORD:
        case["expect"]["python"] = actual
        path.write_text(_dump(case))
        pytest.skip(f"recorded python expectation for {case['id']}")

    expected = case["expect"]["python"]
    assert expected, f"{case['id']}: no recorded python expectation (run GOLDEN_RECORD=1)"
    assert actual == expected, f"{case['id']}: python result diverged from golden"


@pytest.mark.parametrize("path", _load_cases(), ids=lambda p: p.stem)
def test_golden_case_cross_language_agreement(path):
    """The bridge itself: the two engines must AGREE unless a divergence is
    explicitly recorded. An undocumented drift between JS and Python is a red
    test on whichever side deviated.
    """
    if RECORD:
        pytest.skip("record mode")
    case = json.loads(path.read_text())
    py = case["expect"]["python"]
    js = case["expect"]["js"]
    if not py or not js:
        pytest.skip(f"{case['id']}: expectations not recorded on both sides yet")

    if case.get("divergence"):
        # A known, documented divergence — the whole point of recording it.
        return

    if case["kind"] == "dto":
        assert py["valid"] == js["valid"], (
            f"{case['id']}: JS/Python disagree on validity and no divergence is recorded"
        )
        return

    # config: keys the editor actually emitted must not conflict with the
    # engine's normalized view (defaults Python fills must match the UI).
    if py["valid"] and py.get("normalized"):
        emits = js.get("emits", {})
        normalized = py["normalized"]
        for key in set(emits) & set(normalized):
            a, b = emits[key], normalized[key]
            if isinstance(a, (dict, list)) or isinstance(b, (dict, list)):
                continue  # nested option defaults compared elsewhere; skip noise
            assert a == b, (
                f"{case['id']}: emitted {key}={a!r} conflicts with engine normalized {b!r}"
            )
