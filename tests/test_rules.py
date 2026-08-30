"""Unit coverage for the rule engine (spec §1) beyond the golden corpus.

The corpus pins *semantics* (and is shared with the TS evaluator); this file
pins the parts that have no cross-language counterpart: the grammar rejections
of :func:`parse_rules`, the exact ``stringify`` table, ``narrow_config``'s
no-mutation contract, and the warning helper.
"""
import pytest

from stapel_attributes.base import FeatureDef
from stapel_attributes.exceptions import FeatureValidationError
from stapel_attributes.results import ValidationErrorCode
from stapel_attributes.rules import (
    Cond,
    Rule,
    RuleState,
    When,
    evaluate_rules,
    narrow_config,
    parse_rules,
    rule_warnings,
    stringify,
)


def _in(feature="a", values=("x",)):
    return {"feature": feature, "op": "in", "values": list(values)}


def _rule(effect="require", conds=None, **extra):
    return {"effect": effect, "when": {"all": conds or [_in()]}, **extra}


class TestParseRules:
    def test_none_and_empty_parse_to_nothing(self):
        assert parse_rules(None) == []
        assert parse_rules([]) == []

    def test_minimal_rule_round_trips(self):
        (rule,) = parse_rules([_rule()])
        assert rule == Rule(
            effect="require",
            when=When(mode="all", conds=(Cond(feature="a", op="in", values=("x",)),)),
        )

    def test_filled_and_empty_take_no_values(self):
        (rule,) = parse_rules([_rule(conds=[{"feature": "a", "op": "filled"}])])
        assert rule.when.conds[0].values == ()

    @pytest.mark.parametrize("raw, why", [
        ("not-a-list", "rules must be a list"),
        ([[]], "a rule must be an object"),
        ([{"when": {"all": [_in()]}}], "effect is required"),
        ([{"effect": "explode", "when": {"all": [_in()]}}], "unknown effect"),
        ([{"effect": "require"}], "when is required"),
        ([{"effect": "require", "when": {}}], "no connective"),
        ([{"effect": "require", "when": {"all": [_in()], "any": [_in()]}}], "two connectives"),
        ([{"effect": "require", "when": {"all": []}}], "empty condition list"),
        ([{"effect": "require", "when": {"none": [_in()]}}], "unknown connective"),
        ([_rule(conds=[{"feature": "a", "op": "matches", "values": ["x"]}])], "unknown operator"),
        ([_rule(conds=[{"feature": "", "op": "filled"}])], "empty controlling slug"),
        ([_rule(conds=[{"feature": "a", "op": "in"}])], "in without values"),
        ([_rule(conds=[{"feature": "a", "op": "in", "values": []}])], "in with empty values"),
        ([_rule(conds=[{"feature": "a", "op": "in", "values": [1]}])], "non-string values"),
        ([_rule(conds=[{"feature": "a", "op": "filled", "values": ["x"]}])], "filled with values"),
        ([_rule(conds=[{"feature": "a", "op": "filled", "extra": 1}])], "unknown condition key"),
        ([_rule(option="post")], "option outside forbid_option"),
        ([_rule(effect="forbid_option")], "forbid_option without option"),
        ([_rule(effect="forbid_option", option="")], "forbid_option with empty option"),
        ([_rule(effect="limit")], "limit without bounds"),
        ([_rule(effect="limit", min="5")], "non-numeric limit bound"),
        ([_rule(effect="limit", min=True)], "boolean limit bound"),
        ([_rule(min=1)], "min outside limit"),
        ([_rule(max=1)], "max outside limit"),
        ([_rule(note="hi")], "unknown rule key"),
    ])
    def test_grammar_deviation_is_invalid_rules(self, raw, why):
        with pytest.raises(FeatureValidationError) as exc:
            parse_rules(raw)
        assert exc.value.error_code is ValidationErrorCode.INVALID_RULES, why


class TestStringify:
    @pytest.mark.parametrize("value, expected", [
        (None, []),
        ("", []),
        ([], []),
        (True, ["true"]),
        (False, ["false"]),
        (0, ["0"]),
        (12, ["12"]),
        (-3, ["-3"]),
        (2.0, ["2"]),
        (2.5, ["2.5"]),
        (-0.125, ["-0.125"]),
        (1e-07, ["0.0000001"]),
        (1e20, ["100000000000000000000"]),
        (1.5e-9, ["0.0000000015"]),
        ("x", ["x"]),
        (" x ", [" x "]),
        (["a", "b"], ["a", "b"]),
        ([1, True, "x"], ["1", "true", "x"]),
        ([[], None, "a"], ["a"]),
        ({"type": "bool", "value": True}, ["true"]),
        ({"value": ["a", "b"]}, ["a", "b"]),
        ({"value": None}, []),
        ({"other": 1}, []),
        ({}, []),
        (object(), []),
    ])
    def test_table(self, value, expected):
        assert stringify(value) == expected

    def test_no_exponent_ever_leaks(self):
        for value in (1e-7, 1e-15, 2.5e-8, 1e21, 1.25e30):
            assert "e" not in stringify(value)[0].lower()


class TestNarrowConfig:
    def test_input_is_never_mutated(self):
        config = {"type": "select", "options": [{"value": "a"}, {"value": "b"}]}
        snapshot = {"type": "select", "options": [{"value": "a"}, {"value": "b"}]}
        narrow_config(config, RuleState(forbidden_options=frozenset({"a"})))
        assert config == snapshot

    def test_forbidden_options_are_removed(self):
        out = narrow_config(
            {"type": "select", "options": [{"value": "a"}, {"value": "b"}]},
            RuleState(forbidden_options=frozenset({"a"})),
        )
        assert out["options"] == [{"value": "b"}]

    def test_bounds_replace_declared_ones(self):
        out = narrow_config({"type": "int", "min": 1, "max": 100}, RuleState(min=5, max=10))
        assert (out["min"], out["max"]) == (5, 10)

    def test_bounds_are_not_introduced_where_the_config_declares_none(self):
        # §1.4: narrowing REPLACES a declared bound; it never invents one, so a
        # limit rule cannot silently add a constraint a type never advertised.
        out = narrow_config({"type": "int"}, RuleState(min=5))
        assert "min" not in out

    def test_untouched_config_is_returned_as_is(self):
        config = {"type": "string"}
        assert narrow_config(config, RuleState()) is config

    def test_non_dict_config_passes_through(self):
        assert narrow_config("already parsed", RuleState(min=1)) == "already parsed"

    def test_non_dict_options_are_left_alone(self):
        config = {"type": "string", "options": ["a", "b"]}
        assert narrow_config(config, RuleState(forbidden_options=frozenset({"a"}))) is config


class TestRuleWarnings:
    def test_unknown_controlling_slugs_are_reported_sorted_and_deduped(self):
        rules = parse_rules([
            _rule(conds=[_in("zulu"), _in("alpha")]),
            _rule(conds=[_in("alpha")]),
        ])
        assert rule_warnings(rules, {"known"}) == [
            "Rule condition references unknown feature slug: alpha",
            "Rule condition references unknown feature slug: zulu",
        ]

    def test_known_slugs_produce_nothing(self):
        assert rule_warnings(parse_rules([_rule(conds=[_in("a")])]), {"a"}) == []


class TestEvaluateRules:
    def test_accepts_plain_dicts_as_feature_defs(self):
        state = evaluate_rules(
            [{"slug": "a", "config": {"type": "string"}},
             {"slug": "b", "config": {"type": "string"}, "rules": [_rule(conds=[_in("a")])]}],
            {"a": "x"},
        )
        assert state["b"].required is True

    def test_already_parsed_rules_are_reused(self):
        feature = FeatureDef(slug="b", config={"type": "string"})
        feature.rules = parse_rules([_rule(conds=[_in("a")])])
        state = evaluate_rules([FeatureDef(slug="a", config={"type": "string"}), feature], {"a": "x"})
        assert state["b"].required is True

    def test_missing_values_argument_is_an_empty_payload(self):
        state = evaluate_rules([FeatureDef(slug="a", config={"type": "string"})], None)
        assert state["a"] == RuleState()

    def test_broken_rules_raise_invalid_rules(self):
        feature = FeatureDef(slug="a", config={"type": "string"}, rules=[{"effect": "boom"}])
        with pytest.raises(FeatureValidationError) as exc:
            evaluate_rules([feature], {})
        assert exc.value.error_code is ValidationErrorCode.INVALID_RULES
