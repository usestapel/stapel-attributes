"""Golden corpus for the rule engine — the py↔ts contract for §1.

Two JSON sets under ``tests/golden/rules/``:

- ``cases/`` — pure :func:`evaluate_rules` semantics: every effect, operator
  and connective, the whole ``stringify`` table, unknown controlling slugs,
  headers, empty payloads. attributes-react runs the SAME files through its
  ``evaluateRules``, so a divergence between the two evaluators is a red test
  on whichever side deviated instead of a silent split-brain in production.
- ``pipeline/`` — the end-to-end effect of those states through
  ``validate_dto_structured`` + ``normalize_to_dao``: hidden features dropped,
  forbidden options rejected as ``not_in_options``, narrowed bounds reported
  as ``above_maximum`` / ``below_minimum``.

Record mode: ``GOLDEN_RECORD=1 pytest tests/test_rules_golden.py`` rewrites
``expect`` from the live engine (byte-stable: sorted keys, ``\\n``,
``ensure_ascii=False``). Commit the result; CI runs in assert mode.
"""
import json
import os
from pathlib import Path

import pytest

from stapel_attributes.base import FeatureDef
from stapel_attributes.rules import evaluate_rules
from stapel_attributes.validation import normalize_to_dao, validate_dto_structured

RULES_DIR = Path(__file__).parent / "golden" / "rules"
CASES_DIR = RULES_DIR / "cases"
PIPELINE_DIR = RULES_DIR / "pipeline"
RECORD = os.environ.get("GOLDEN_RECORD") == "1"


def _dump(obj) -> str:
    return json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _features(case: dict):
    return [FeatureDef.from_dict(f) for f in case["features"]]


def _run_state(case: dict) -> dict:
    state = evaluate_rules(_features(case), case["values"])
    return {slug: rule_state.to_dict() for slug, rule_state in state.items()}


def _run_pipeline(case: dict) -> dict:
    features = _features(case)
    result = validate_dto_structured(features, case["values"])
    dao = normalize_to_dao(features, case["values"])
    return {
        "valid": result.valid,
        "results": {
            row.slug: {
                "status": row.status.value,
                "error": row.error.value if row.error else None,
            }
            for row in result.results
        },
        "dao": sorted(dao),
    }


def _check(path: Path, actual: dict) -> None:
    case = json.loads(path.read_text())
    if RECORD:
        case["expect"] = actual
        path.write_text(_dump(case))
        pytest.skip(f"recorded {case['id']}")
    expected = case["expect"]
    assert expected, f"{case['id']}: nothing recorded (run GOLDEN_RECORD=1)"
    assert actual == expected, f"{case['id']}: diverged from the golden corpus"


def _paths(directory: Path):
    return sorted(directory.glob("*.json"))


def test_corpus_is_not_empty():
    # The corpus is the contract; an empty directory would make every
    # parametrized test below vacuously green.
    assert len(_paths(CASES_DIR)) >= 40
    assert _paths(PIPELINE_DIR)


@pytest.mark.parametrize("path", _paths(CASES_DIR), ids=lambda p: p.stem)
def test_rule_state_case(path):
    _check(path, _run_state(json.loads(path.read_text())))


@pytest.mark.parametrize("path", _paths(PIPELINE_DIR), ids=lambda p: p.stem)
def test_rule_pipeline_case(path):
    _check(path, _run_pipeline(json.loads(path.read_text())))


def test_every_case_id_matches_its_filename():
    for path in _paths(CASES_DIR) + _paths(PIPELINE_DIR):
        assert json.loads(path.read_text())["id"] == path.stem
