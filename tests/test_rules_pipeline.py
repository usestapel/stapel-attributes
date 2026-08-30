"""Rules inside the validation pipeline (spec §1.4), and the no-rules floor.

The last class is the anti-regression the whole slice hangs on: a schema
carrying no ``rules`` must behave EXACTLY as it did in 0.4.7 — the rule
pre-pass is additive, not a rewrite of the pipeline.
"""
import pytest
from django.core.exceptions import ValidationError

from stapel_attributes.base import FeatureDef
from stapel_attributes.results import ValidationErrorCode, ValidationStatus
from stapel_attributes.validation import (
    normalize_to_dao,
    validate_configs_structured,
    validate_dto,
    validate_dto_structured,
)

CONDITION = {
    "slug": "condition",
    "config": {"type": "select", "maxSelected": 1,
               "options": [{"value": "new", "label": "new"}, {"value": "used", "label": "used"}]},
}


def feature(slug, config, **kwargs):
    return FeatureDef.from_dict({"slug": slug, "config": config, **kwargs})


def _defs(*extra):
    return [FeatureDef.from_dict(CONDITION), *extra]


def _require_when_used():
    return [{"effect": "require",
             "when": {"all": [{"feature": "condition", "op": "in", "values": ["used"]}]}}]


def _hide_when_new():
    return [{"effect": "hide",
             "when": {"all": [{"feature": "condition", "op": "in", "values": ["new"]}]}}]


class TestRaiseStylePipeline:
    def test_rule_required_feature_blocks(self):
        defs = _defs(feature("screen", {"type": "string"}, rules=_require_when_used()))
        with pytest.raises(ValidationError) as exc:
            validate_dto(defs, {"condition": ["used"]})
        assert any("screen" in message for message in exc.value.messages)

    def test_rule_required_feature_passes_when_answered(self):
        defs = _defs(feature("screen", {"type": "string"}, rules=_require_when_used()))
        validate_dto(defs, {"condition": ["used"], "screen": "cracked"})

    def test_hidden_mandatory_feature_does_not_block(self):
        defs = _defs(feature("screen", {"type": "string"}, mandatory=True, rules=_hide_when_new()))
        validate_dto(defs, {"condition": ["new"]})

    def test_hidden_feature_value_is_not_validated(self):
        # A too-long value for a hidden field must not fail the submission.
        defs = _defs(feature("screen", {"type": "string", "maxLength": 3}, rules=_hide_when_new()))
        validate_dto(defs, {"condition": ["new"], "screen": "much too long"})

    def test_narrowed_bound_is_enforced(self):
        rules = [{"effect": "limit", "max": 10,
                  "when": {"all": [{"feature": "condition", "op": "in", "values": ["new"]}]}}]
        defs = _defs(feature("weight", {"type": "int", "min": 1, "max": 100}, rules=rules))
        with pytest.raises(ValidationError):
            validate_dto(defs, {"condition": ["new"], "weight": 42})

    def test_broken_rules_raise_invalid_rules(self):
        defs = _defs(feature("screen", {"type": "string"}, rules=[{"effect": "boom"}]))
        with pytest.raises(ValidationError) as exc:
            validate_dto(defs, {"condition": ["new"]})
        assert exc.value.error_code is ValidationErrorCode.INVALID_RULES


class TestStructuredPipeline:
    def test_broken_rules_fail_the_batch_on_root(self):
        defs = _defs(feature("screen", {"type": "string"}, rules=[{"effect": "boom"}]))
        result = validate_dto_structured(defs, {})
        assert result.valid is False
        (row,) = result.results
        assert row.slug == "_root"
        assert row.error is ValidationErrorCode.INVALID_RULES
        assert row.localizable_error == "error.400.feature_invalid_rules"

    def test_hidden_feature_reports_ok_and_is_dropped(self):
        defs = _defs(feature("screen", {"type": "string"}, mandatory=True, rules=_hide_when_new()))
        payload = {"condition": ["new"], "screen": "cracked"}
        result = validate_dto_structured(defs, payload)
        assert result.valid is True
        assert {r.slug: r.status for r in result.results}["screen"] is ValidationStatus.OK
        assert "screen" not in normalize_to_dao(defs, payload)


class TestConfigValidation:
    def test_broken_rules_fail_the_feature(self):
        result = validate_configs_structured(
            [feature("screen", {"type": "string"}, rules=[{"effect": "require"}])]
        )
        assert result.valid is False
        assert result.results[0].error is ValidationErrorCode.INVALID_RULES

    def test_unknown_controlling_slug_is_a_warning(self):
        defs = [feature("screen", {"type": "string"}, rules=_require_when_used())]
        result = validate_configs_structured(defs, known_slugs={"screen"})
        assert result.valid is True
        assert result.results[0].warnings == [
            "Rule condition references unknown feature slug: condition"
        ]

    def test_no_known_slugs_means_no_such_warning(self):
        defs = [feature("screen", {"type": "string"}, rules=_require_when_used())]
        assert validate_configs_structured(defs).results[0].warnings is None

    def test_known_controlling_slug_is_silent(self):
        defs = _defs(feature("screen", {"type": "string"}, rules=_require_when_used()))
        result = validate_configs_structured(defs, known_slugs={"condition", "screen"})
        assert all(row.warnings is None for row in result.results)

    def test_unknown_config_key_warning_still_works(self):
        result = validate_configs_structured(
            [feature("note", {"type": "string", "minLenght": 5})], known_slugs={"note"}
        )
        assert result.results[0].warnings == ["Unknown config key(s) ignored: minLenght"]


class TestNoRulesIsUnchanged:
    """0.4.7 parity: without ``rules`` every entry point answers as before."""

    SCHEMA = [
        {"slug": "title", "config": {"type": "string", "maxLength": 5}, "mandatory": True},
        {"slug": "weight", "config": {"type": "int", "min": 1, "max": 10}},
        {"slug": "section", "config": {"type": "header"}},
        {"slug": "colour", "config": {
            "type": "select", "maxSelected": 1,
            "options": [{"value": "red", "label": "red"}, {"value": "blue", "label": "blue"}]}},
    ]

    def defs(self):
        return [FeatureDef.from_dict(f) for f in self.SCHEMA]

    def test_mandatory_still_blocks(self):
        with pytest.raises(ValidationError):
            validate_dto(self.defs(), {"weight": 5})

    def test_constraints_still_apply(self):
        result = validate_dto_structured(self.defs(), {"title": "ok", "weight": 99})
        assert {r.slug: r.error for r in result.results}["weight"] is ValidationErrorCode.ABOVE_MAXIMUM

    def test_options_still_apply(self):
        result = validate_dto_structured(self.defs(), {"title": "ok", "colour": ["green"]})
        assert {r.slug: r.error for r in result.results}["colour"] is ValidationErrorCode.NOT_IN_OPTIONS

    def test_a_valid_payload_is_valid(self):
        result = validate_dto_structured(self.defs(), {"title": "ok", "weight": 5, "colour": ["red"]})
        assert result.valid is True

    def test_dao_keeps_headers_order_and_empty_dropping(self):
        dao = normalize_to_dao(self.defs(), {"title": "ok", "weight": 5, "colour": []})
        assert sorted(dao) == ["section", "title", "weight"]
        assert dao["section"]["order"] == 2
        assert dao["title"]["value"] == "ok"

    def test_an_explicit_empty_rules_list_changes_nothing(self):
        with_empty = [FeatureDef.from_dict({**f, "rules": []}) for f in self.SCHEMA]
        payload = {"title": "ok", "weight": 5, "colour": ["red"]}
        assert normalize_to_dao(with_empty, payload) == normalize_to_dao(self.defs(), payload)
        assert validate_dto_structured(with_empty, payload).valid is True
