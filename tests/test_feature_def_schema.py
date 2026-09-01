"""``docs/feature-def.schema.json`` is the canon — this is its gate.

One schema, several emitters (attributes-react generates its TS types from it,
stapel-categories checks its ResolvedFeature payload against it), so the
schema drifting from the Python dataclass would silently split the contract
across three repos. Everything below compares the two directly.

The rule corpus is validated against ``$defs.Rule`` with ``jsonschema`` when it
is installed (it is, in CI and in the workspace venv); without it the test
falls back to a structural check so the gate still says something rather than
skipping.
"""
import json
from dataclasses import fields
from pathlib import Path

import pytest

from stapel_attributes.base import FeatureDef
from stapel_attributes.exceptions import FeatureValidationError
from stapel_attributes.rules import parse_rules
from stapel_attributes.types.ref_hierarchical_select.config import RefHierarchicalSelectConfig
from stapel_attributes.types.ref_select.config import OptionsRef, RefSelectConfig

REPO = Path(__file__).resolve().parent.parent
SCHEMA_PATH = REPO / "docs" / "feature-def.schema.json"
RULES_DIR = REPO / "tests" / "golden" / "rules"

SCHEMA = json.loads(SCHEMA_PATH.read_text())
DEFS = SCHEMA["$defs"]

try:
    import jsonschema
except ImportError:  # pragma: no cover - exercised only without the test dep
    jsonschema = None


def _corpus_rules():
    """Every rule authored anywhere in the golden corpus, with its case id."""
    for path in sorted(RULES_DIR.rglob("*.json")):
        loaded = json.loads(path.read_text())
        # cases/ and pipeline/ hold one case per file; imported/ holds an array.
        cases = loaded if isinstance(loaded, list) else [loaded]
        for case in cases:
            for feature in case["features"]:
                for rule in feature.get("rules", []):
                    yield f"{path.stem}:{case['id']}:{feature['slug']}", rule


def _validate_rule(rule: dict) -> None:
    if jsonschema is not None:
        jsonschema.validate(rule, {**SCHEMA, "$ref": "#/$defs/Rule"})
        return
    # Structural fallback: shape only, no conditional keywords.
    assert rule["effect"] in DEFS["Rule"]["properties"]["effect"]["enum"]
    when = rule["when"]
    assert len(when) == 1 and set(when) <= {"all", "any"}
    for cond in next(iter(when.values())):
        assert set(cond) <= set(DEFS["Cond"]["properties"])
        assert cond["op"] in DEFS["Cond"]["properties"]["op"]["enum"]


def test_schema_properties_match_the_dataclass():
    assert set(DEFS["FeatureDef"]["properties"]) == {f.name for f in fields(FeatureDef)}


def test_only_slug_and_config_are_required():
    assert DEFS["FeatureDef"]["required"] == ["slug", "config"]


def test_root_points_at_the_feature_def_definition():
    assert SCHEMA["$ref"] == "#/$defs/FeatureDef"


@pytest.mark.parametrize("definition, dataclass", [
    ("OptionsRef", OptionsRef),
    ("RefSelectConfig", RefSelectConfig),
    ("RefHierarchicalSelectConfig", RefHierarchicalSelectConfig),
])
def test_ref_config_definitions_match_their_dataclasses(definition, dataclass):
    assert set(DEFS[definition]["properties"]) == {f.name for f in fields(dataclass)}


def test_the_corpus_is_reachable():
    assert list(_corpus_rules()), "no rules found in the golden corpus"


def test_every_corpus_rule_validates_against_the_canon():
    for case_id, rule in _corpus_rules():
        try:
            _validate_rule(rule)
        except Exception as exc:  # noqa: BLE001 - report which case broke
            pytest.fail(f"{case_id}: rule is invalid per $defs.Rule: {exc}", pytrace=False)


@pytest.mark.skipif(jsonschema is None, reason="jsonschema is not installed")
@pytest.mark.parametrize("rule", [
    {"effect": "boom", "when": {"all": [{"feature": "a", "op": "filled"}]}},
    {"effect": "require"},
    {"effect": "require", "when": {"all": []}},
    {"effect": "require", "when": {"all": [{"feature": "a", "op": "filled"}], "any": []}},
    {"effect": "require", "when": {"all": [{"feature": "a", "op": "in"}]}},
    {"effect": "require", "when": {"all": [{"feature": "a", "op": "filled", "values": ["x"]}]}},
    {"effect": "require", "when": {"all": [{"feature": "a", "op": "filled"}]}, "option": "x"},
    {"effect": "forbid_option", "when": {"all": [{"feature": "a", "op": "filled"}]}},
    {"effect": "limit", "when": {"all": [{"feature": "a", "op": "filled"}]}},
    {"effect": "require", "when": {"all": [{"feature": "a", "op": "filled"}]}, "min": 1},
    {"effect": "require", "when": {"all": [{"feature": "a", "op": "filled"}]}, "note": "x"},
])
def test_the_schema_is_exactly_as_closed_as_the_parser(rule):
    # Both gates must reject the same thing, or one of the two evaluators
    # would accept rules the other refuses.
    with pytest.raises(jsonschema.ValidationError):
        _validate_rule(rule)
    with pytest.raises(FeatureValidationError):
        parse_rules([rule])
