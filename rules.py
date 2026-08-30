"""Conditional feature rules — the closed, type-independent grammar.

A rule is a sibling of ``mandatory`` on :class:`~stapel_attributes.base.FeatureDef`,
never part of ``config``: ``config`` is parsed by a strict per-type serializer,
while a rule speaks only about *other* features' submitted values. The grammar
is closed on purpose — five effects, four operators, two connectives, no
nesting — so the same semantics are provable in two languages (this module and
``static_src``/attributes-react's ``evaluateRules``) against one shared corpus
(``tests/golden/rules/``).

Evaluation is a **single pass** over the raw submitted values: a controlling
feature's own visibility is not consulted and there is no fixed point, so
cycles are impossible by construction and the result is deterministic.

Import-time purity: this module imports neither Django nor DRF. ``stringify``,
``evaluate_rules`` and ``narrow_config`` are usable from a plain script; only
the error path of :func:`parse_rules` reaches for
``FeatureValidationError`` (imported lazily inside the function).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, FrozenSet, Iterable, List, Mapping, Optional, Sequence, Tuple

EFFECTS: Tuple[str, ...] = ('require', 'show', 'hide', 'forbid_option', 'limit')
OPERATORS: Tuple[str, ...] = ('in', 'not_in', 'filled', 'empty')
CONNECTIVES: Tuple[str, ...] = ('all', 'any')

_VALUE_OPS = ('in', 'not_in')
_RULE_KEYS = frozenset({'effect', 'when', 'option', 'min', 'max'})
_COND_KEYS = frozenset({'feature', 'op', 'values'})


# --------------------------------------------------------------------------- #
# Grammar (§1.1)
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class Cond:
    """One condition on a controlling feature's submitted value."""

    feature: str
    op: str
    values: Tuple[str, ...] = ()


@dataclass(frozen=True)
class When:
    """The single connective of a rule: ``all`` (conjunction) or ``any``."""

    mode: str
    conds: Tuple[Cond, ...]


@dataclass(frozen=True)
class Rule:
    """One parsed rule. ``option`` belongs to ``forbid_option`` only,
    ``min``/``max`` to ``limit`` only."""

    effect: str
    when: When
    option: Optional[str] = None
    min: Optional[float] = None
    max: Optional[float] = None


@dataclass(frozen=True)
class RuleState:
    """The effect of every matching rule on one feature."""

    visible: bool = True
    required: bool = False
    forbidden_options: FrozenSet[str] = frozenset()
    min: Optional[float] = None
    max: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """JSON-comparable snapshot (the golden-corpus shape)."""
        return {
            'visible': self.visible,
            'required': self.required,
            'forbidden_options': sorted(self.forbidden_options),
            'min': self.min,
            'max': self.max,
        }


def _invalid(message: str):
    from stapel_attributes.exceptions import FeatureValidationError
    from stapel_attributes.results import ValidationErrorCode

    return FeatureValidationError(message, code=ValidationErrorCode.INVALID_RULES)


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _parse_cond(raw: Any, where: str) -> Cond:
    if not isinstance(raw, dict):
        raise _invalid(f"{where}: condition must be an object")
    unknown = sorted(set(raw) - _COND_KEYS)
    if unknown:
        raise _invalid(f"{where}: unknown condition key(s): {', '.join(unknown)}")

    feature = raw.get('feature')
    if not isinstance(feature, str) or not feature:
        raise _invalid(f"{where}: condition needs a non-empty 'feature' slug")

    op = raw.get('op')
    if op not in OPERATORS:
        raise _invalid(f"{where}: 'op' must be one of {', '.join(OPERATORS)}")

    if op in _VALUE_OPS:
        values = raw.get('values')
        if not isinstance(values, list) or not values:
            raise _invalid(f"{where}: '{op}' needs a non-empty 'values' list")
        if not all(isinstance(v, str) for v in values):
            raise _invalid(f"{where}: 'values' must be strings")
        return Cond(feature=feature, op=op, values=tuple(values))

    if 'values' in raw:
        raise _invalid(f"{where}: '{op}' takes no 'values'")
    return Cond(feature=feature, op=op)


def _parse_when(raw: Any, where: str) -> When:
    if not isinstance(raw, dict):
        raise _invalid(f"{where}: 'when' must be an object")
    modes = [m for m in CONNECTIVES if m in raw]
    unknown = sorted(set(raw) - set(CONNECTIVES))
    if unknown:
        raise _invalid(f"{where}: unknown 'when' key(s): {', '.join(unknown)}")
    if len(modes) != 1:
        raise _invalid(f"{where}: 'when' must have exactly one of 'all' / 'any'")
    mode = modes[0]
    conds = raw[mode]
    if not isinstance(conds, list) or not conds:
        raise _invalid(f"{where}: 'when.{mode}' must be a non-empty list of conditions")
    return When(mode=mode, conds=tuple(_parse_cond(c, f"{where}.{mode}[{i}]") for i, c in enumerate(conds)))


def parse_rules(raw: Any) -> List[Rule]:
    """Parse the raw ``FeatureDef.rules`` list into :class:`Rule` objects.

    Any deviation from the closed grammar (§1.1) raises
    ``FeatureValidationError(code=ValidationErrorCode.INVALID_RULES)``: unknown
    keys, a missing/ambiguous connective, an empty condition list, ``values``
    on ``filled``/``empty`` (or missing on ``in``/``not_in``), ``option`` on
    anything but ``forbid_option`` (or missing there), ``min``/``max`` on
    anything but ``limit`` (or neither present there).

    ``None`` and an empty list both parse to ``[]``.
    """
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise _invalid("'rules' must be a list")

    parsed: List[Rule] = []
    for index, item in enumerate(raw):
        where = f"rules[{index}]"
        if not isinstance(item, dict):
            raise _invalid(f"{where}: rule must be an object")
        unknown = sorted(set(item) - _RULE_KEYS)
        if unknown:
            raise _invalid(f"{where}: unknown rule key(s): {', '.join(unknown)}")

        effect = item.get('effect')
        if effect not in EFFECTS:
            raise _invalid(f"{where}: 'effect' must be one of {', '.join(EFFECTS)}")

        if 'when' not in item:
            raise _invalid(f"{where}: 'when' is required")
        when = _parse_when(item['when'], where)

        option = item.get('option')
        if effect == 'forbid_option':
            if not isinstance(option, str) or not option:
                raise _invalid(f"{where}: 'forbid_option' needs a non-empty 'option'")
        elif option is not None or 'option' in item:
            raise _invalid(f"{where}: 'option' is only allowed on 'forbid_option'")

        has_min, has_max = 'min' in item, 'max' in item
        if effect == 'limit':
            if not (has_min or has_max):
                raise _invalid(f"{where}: 'limit' needs at least one of 'min' / 'max'")
            for key in ('min', 'max'):
                if key in item and not _is_number(item[key]):
                    raise _invalid(f"{where}: '{key}' must be a number")
        elif has_min or has_max:
            raise _invalid(f"{where}: 'min' / 'max' are only allowed on 'limit'")

        parsed.append(Rule(
            effect=effect,
            when=when,
            option=option if effect == 'forbid_option' else None,
            min=item.get('min') if effect == 'limit' else None,
            max=item.get('max') if effect == 'limit' else None,
        ))
    return parsed


# --------------------------------------------------------------------------- #
# Value canonicalization (§1.2)
# --------------------------------------------------------------------------- #

def _number_to_str(value: Any) -> str:
    if isinstance(value, int):
        return str(value)
    number = float(value)
    if number.is_integer():
        return str(int(number))
    text = repr(number)
    if 'e' in text or 'E' in text:
        # Shortest decimal, expanded: repr() already carries the shortest
        # round-tripping digits, Decimal(...):f only drops the exponent.
        text = f"{Decimal(text):f}"
    return text


def stringify(value: Any) -> List[str]:
    """Canonicalize a submitted value into the list of strings rules compare.

    Both evaluators compare strings, so the mapping is fixed (§1.2)::

        None / '' / []                  -> []
        bool                            -> ['true'] / ['false']
        number                          -> ['12'] (integral) / ['2.5'] (shortest, no exponent)
        str                             -> [value]        (never trimmed)
        list                            -> concatenation of the elements
        {'value': ...} (a DTO envelope) -> stringify(value)
        any other dict                  -> []

    ``False`` is *filled*: it canonicalizes to ``['false']``, not ``[]``.
    Anything outside the table (an object no JSON payload can carry) is ``[]``.
    """
    if value is None:
        return []
    if isinstance(value, bool):
        return ['true' if value else 'false']
    if isinstance(value, (int, float, Decimal)):
        return [_number_to_str(value)]
    if isinstance(value, str):
        return [] if value == '' else [value]
    if isinstance(value, (list, tuple)):
        out: List[str] = []
        for item in value:
            out.extend(stringify(item))
        return out
    if isinstance(value, dict):
        return stringify(value['value']) if 'value' in value else []
    return []


# --------------------------------------------------------------------------- #
# Semantics (§1.3)
# --------------------------------------------------------------------------- #

def _def_slug(feature: Any) -> str:
    if isinstance(feature, dict):
        return str(feature.get('slug') or feature.get('name') or feature.get('id') or '')
    return str(getattr(feature, 'slug', '') or getattr(feature, 'name', '') or getattr(feature, 'id', ''))


def _def_attr(feature: Any, name: str, default: Any = None) -> Any:
    if isinstance(feature, dict):
        return feature.get(name, default)
    return getattr(feature, name, default)


def _config_type(feature: Any) -> Optional[str]:
    config = _def_attr(feature, 'config')
    if isinstance(config, dict):
        return config.get('type')
    return getattr(config, 'type', None)


def _cond_matches(cond: Cond, strings: Sequence[str]) -> bool:
    if cond.op == 'filled':
        return bool(strings)
    if cond.op == 'empty':
        return not strings
    hit = any(s in cond.values for s in strings)
    return hit if cond.op == 'in' else not hit


def _when_matches(when: When, readings: Mapping[str, List[str]]) -> bool:
    results = (_cond_matches(c, readings.get(c.feature, [])) for c in when.conds)
    return all(results) if when.mode == 'all' else any(results)


def evaluate_rules(
    feature_defs: Iterable[Any],
    values: Optional[Mapping[str, Any]],
) -> Dict[str, RuleState]:
    """Evaluate every feature's rules against *values* in one pass (§1.3).

    *feature_defs* is any iterable of :class:`~stapel_attributes.base.FeatureDef`
    (or plain feature-def dicts of the same shape); *values* is ``{slug: raw}``
    and also accepts the DTO envelope ``{slug: {'type': ..., 'value': ...}}``
    (:func:`stringify` unwraps it).

    Per feature::

        visible  = not any(hide matched) and (no show rules or any show matched)
        required = visible and (mandatory or any require matched)
        forbidden_options = {option of every matched forbid_option rule}
        min/max  = the LAST matched limit rule, replacing (not intersecting)

    A controlling slug absent from *feature_defs* reads as ``empty`` — a
    feature is reused across categories with different field sets, so that is
    not an error (``validate_configs_structured`` reports it as a warning).
    ``header`` features are always visible and never required.
    """
    defs = list(feature_defs)
    raw_values = values or {}

    readings: Dict[str, List[str]] = {}
    for feature in defs:
        slug = _def_slug(feature)
        readings[slug] = stringify(raw_values.get(slug))

    state: Dict[str, RuleState] = {}
    for feature in defs:
        slug = _def_slug(feature)
        if _config_type(feature) == 'header':
            state[slug] = RuleState()
            continue

        rules = _as_rules(_def_attr(feature, 'rules'))
        matched = [r for r in rules if _when_matches(r.when, readings)]

        has_show = any(r.effect == 'show' for r in rules)
        visible = (
            not any(r.effect == 'hide' for r in matched)
            and (not has_show or any(r.effect == 'show' for r in matched))
        )
        required = visible and (
            bool(_def_attr(feature, 'mandatory', False))
            or any(r.effect == 'require' for r in matched)
        )
        forbidden = frozenset(r.option for r in matched if r.effect == 'forbid_option' and r.option)

        limit_min = limit_max = None
        for rule in matched:
            if rule.effect == 'limit':
                limit_min, limit_max = rule.min, rule.max

        state[slug] = RuleState(
            visible=visible,
            required=required,
            forbidden_options=forbidden,
            min=limit_min,
            max=limit_max,
        )
    return state


def _as_rules(raw: Any) -> List[Rule]:
    if not raw:
        return []
    if isinstance(raw, list) and all(isinstance(r, Rule) for r in raw):
        return list(raw)
    return parse_rules(raw)


# --------------------------------------------------------------------------- #
# Pipeline embedding (§1.4)
# --------------------------------------------------------------------------- #

def narrow_config(config_dict: Any, state: RuleState) -> Any:
    """Apply a :class:`RuleState` to a raw config dict, type-agnostically.

    Two shape-level edits, no type knowledge and no new error codes: options
    whose ``value`` is forbidden are removed, and an existing ``min``/``max``
    is replaced by the state's. The narrowed config then goes through the
    normal ``parse_config`` -> ``validate_dto`` path, so ``select`` rejects a
    forbidden option as ``not_in_options`` and ``int`` reports
    ``above_maximum`` — the rule engine adds no error vocabulary of its own.

    The input is never mutated; an unchanged config is returned as-is.
    """
    if not isinstance(config_dict, dict):
        return config_dict

    changed = False
    out = dict(config_dict)

    if state.forbidden_options:
        options = out.get('options')
        if isinstance(options, list):
            kept = [
                o for o in options
                if not (isinstance(o, dict) and o.get('value') in state.forbidden_options)
            ]
            if len(kept) != len(options):
                out['options'] = kept
                changed = True

    for bound in ('min', 'max'):
        limit = getattr(state, bound)
        if limit is not None and bound in out:
            out[bound] = limit
            changed = True

    return out if changed else config_dict


def rule_warnings(rules: Iterable[Rule], known_slugs: Iterable[str]) -> List[str]:
    """Non-blocking findings for a parsed rule set: controlling slugs that no
    feature in the set defines.

    Not an error — the same feature is reused in categories with different
    field sets, and an unknown controlling slug simply reads as ``empty``.
    Sorted and de-duplicated so the output is stable.
    """
    known = set(known_slugs)
    unknown = {c.feature for rule in rules for c in rule.when.conds if c.feature not in known}
    return [f"Rule condition references unknown feature slug: {slug}" for slug in sorted(unknown)]


__all__ = [
    'CONNECTIVES',
    'Cond',
    'EFFECTS',
    'OPERATORS',
    'Rule',
    'RuleState',
    'When',
    'evaluate_rules',
    'narrow_config',
    'parse_rules',
    'rule_warnings',
    'stringify',
]
