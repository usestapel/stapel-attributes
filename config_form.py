"""Field-kind contract — the schema-driven config-form declaration.

Python is the source of truth for each feature type's admin config form
(docs/attributes-admin-ui.md, decision 1). A type declares its form as a list
of :class:`FormField` via :meth:`BaseFeatureType.config_form`; the admin JS
renders the form from that declaration, so **a newly registered type gets an
admin form with zero JS** as long as it uses the standard field-kinds.

The declarations are ported 1:1 from the legacy catalog's ``feature_types.js``
``FEATURE_TYPES`` dictionary (static_src/LOGIC-NOTES.md §1–2), including its
latent quirks (e.g. ``header.style`` default ``'h2'`` matches no option —
LN-B01). Labels are emitted as i18n keys (``admin.attributes.form.<type>.<field>``);
the en/ru catalogs carry the literal strings. The kind dictionary
(:data:`FIELD_KINDS`) is the minimally-sufficient set the nine generic types
need; hosts registering exotic kinds ship their own JS widget (the config
widget registry) but declare through the same contract.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Field-kind dictionary (LOGIC-NOTES §1) — minimally sufficient for 9 generic types
# ---------------------------------------------------------------------------
# kind -> tuple of parameter names it understands (documentation + validation).
FIELD_KINDS: Dict[str, tuple] = {
    "number": ("step",),                       # LN-K01
    "text": ("placeholder",),                  # LN-K02
    "checkbox": (),                            # LN-K03 (default carried on the field)
    "translatable_text": ("placeholder",),     # LN-K04
    "number_options": ("itemType",),           # LN-K05
    "string_options": (),                      # LN-K06 (no itemType)
    "color_options": (),                       # LN-K07
    "select": ("options",),                    # LN-K08 (fixed inline options)
    "select_options_with_default": (),         # LN-K09
    "max_selected_dropdown": (),               # LN-K10
    "hierarchical_options": (),                # LN-K11
    "timestamp": ("placeholder",),             # LN-K12
    "timestamp_array": ("placeholder",),       # LN-K13
}


@dataclass
class FormField:
    """One declared config-form field (LOGIC-NOTES §1, LN-K00).

    Attributes:
        name: config key this field edits (order within a type is significant).
        kind: a key of :data:`FIELD_KINDS`.
        label_key: i18n key (``admin.attributes.form.<type>.<field>``); the
            admin i18n engine resolves it, falling back to the key itself.
        required: cosmetic ``*`` marker only — real validation is on the Python
            side (LN-C00 / docs §4). ``None`` omitted from output.
        default: default value applied when the config key is absent.
        params: kind-specific params (``step``, ``itemType``, inline ``options``,
            ``placeholder``, …). Only keys the kind understands are meaningful.
    """

    name: str
    kind: str
    label_key: str
    required: Optional[bool] = None
    default: Any = None
    params: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """JSON-serializable snapshot; ``None``/empty optionals omitted."""
        out: Dict[str, Any] = {"name": self.name, "kind": self.kind, "label_key": self.label_key}
        if self.required:
            out["required"] = True
        if self.default is not None:
            out["default"] = self.default
        if self.params:
            out["params"] = dict(self.params)
        return out


def _lk(type_slug: str, field_name: str) -> str:
    """Label key for a (type, field) pair."""
    return f"admin.attributes.form.{type_slug}.{field_name}"


def _f(type_slug: str, name: str, kind: str, **kw: Any) -> FormField:
    return FormField(name=name, kind=kind, label_key=_lk(type_slug, name), **kw)


# ---------------------------------------------------------------------------
# Built-in declarations (LOGIC-NOTES §2) — ported 1:1 from feature_types.js
# ---------------------------------------------------------------------------
def _int_form() -> List[FormField]:  # LN-T-int
    return [
        _f("int", "min", "number", params={"step": 1}),
        _f("int", "max", "number", params={"step": 1}),
        _f("int", "options", "number_options", params={"itemType": "number"}),
        _f("int", "allowCustom", "checkbox", default=True),
        _f("int", "prefix", "translatable_text", params={"placeholder": "$"}),
        _f("int", "postfix", "translatable_text", params={"placeholder": "km"}),
        _f("int", "postfix1000", "translatable_text", params={"placeholder": "k"}),
        _f("int", "placeholder", "translatable_text"),
    ]


def _float_form() -> List[FormField]:  # LN-T-float
    return [
        _f("float", "min", "number", params={"step": 0.01}),
        _f("float", "max", "number", params={"step": 0.01}),
        _f("float", "precision", "number", default=2, params={"step": 1}),
        _f("float", "options", "number_options", params={"itemType": "number"}),
        _f("float", "allowCustom", "checkbox", default=True),
        _f("float", "prefix", "translatable_text", params={"placeholder": "$"}),
        _f("float", "postfix", "translatable_text", params={"placeholder": "m²"}),
        _f("float", "postfix1000", "translatable_text", params={"placeholder": "k"}),
        _f("float", "placeholder", "translatable_text"),
    ]


def _string_form() -> List[FormField]:  # LN-T-string (no postfix1000; pattern is text; LN-B17)
    return [
        _f("string", "minLength", "number", params={"step": 1}),
        _f("string", "maxLength", "number", params={"step": 1}),
        _f("string", "pattern", "text"),
        _f("string", "options", "string_options"),
        _f("string", "allowCustom", "checkbox", default=True),
        _f("string", "prefix", "translatable_text", params={"placeholder": "$"}),
        _f("string", "postfix", "translatable_text", params={"placeholder": "m²"}),
        _f("string", "placeholder", "translatable_text"),
    ]


def _bool_form() -> List[FormField]:  # LN-T-bool
    return [
        _f("bool", "trueLabel", "translatable_text", params={"placeholder": "yes"}),
        _f("bool", "falseLabel", "translatable_text", params={"placeholder": "no"}),
    ]


def _hex_color_form() -> List[FormField]:  # LN-T-hex_color (allowCustom default FALSE — LN-B15)
    return [
        _f("hex_color", "options", "color_options"),
        _f("hex_color", "allowCustom", "checkbox", default=False),
    ]


def _select_form() -> List[FormField]:  # LN-T-select
    # B2 canon: the untouched-form defaults MUST equal the engine dataclass
    # defaults (SelectConfig: uiStyle='dropdown', maxSelected=None=unlimited),
    # so a select saved without touching these fields round-trips to what the
    # UI displayed. Chosen over the legacy chips/1 default because it keeps the engine's
    # established default — no stored config that omits these keys is
    # reinterpreted, and no already-stored multi-select DAO is retroactively
    # invalidated by a maxSelected=1 cap. ``maxSelected`` carries no default
    # (None omitted from to_dict): the max_selected_dropdown widget then shows
    # "Unlimited", matching the engine.
    return [
        _f("select", "options", "select_options_with_default"),
        _f(
            "select", "uiStyle", "select", required=True, default="dropdown",
            params={"options": [
                {"value": "chips", "label": "Chips/Tags"},
                {"value": "checkboxes", "label": "Checkboxes (like checklist)"},
                {"value": "dropdown", "label": "Dropdown"},
            ]},
        ),
        _f("select", "minSelected", "number", default=0, params={"step": 1}),
        _f("select", "maxSelected", "max_selected_dropdown"),
        _f("select", "lockUserInput", "checkbox"),
    ]


def _hierarchical_select_form() -> List[FormField]:  # LN-T-hierarchical_select
    return [
        _f("hierarchical_select", "options", "hierarchical_options"),
    ]


def _date_form() -> List[FormField]:  # LN-T-date (field literally named 'default'; lockInput — LN-B16)
    return [
        _f(
            "date", "precision", "select", required=True, default="date",
            params={"options": [
                {"value": "year", "label": "Year only"},
                {"value": "month", "label": "Month (year + month)"},
                {"value": "date", "label": "Date (year + month + day)"},
                {"value": "datetime", "label": "Date & Time"},
            ]},
        ),
        _f("date", "minDate", "timestamp", params={"placeholder": "Select minimum date..."}),
        _f("date", "maxDate", "timestamp", params={"placeholder": "Select maximum date..."}),
        _f("date", "allowFuture", "checkbox", default=True),
        _f("date", "allowPast", "checkbox", default=True),
        _f("date", "default", "timestamp", params={"placeholder": "Select default date..."}),
        _f("date", "options", "timestamp_array", params={"placeholder": "Add preset date options"}),
        _f("date", "lockInput", "checkbox"),
        _f("date", "placeholder", "text", params={"placeholder": "Select date..."}),
    ]


def _header_form() -> List[FormField]:  # LN-T-header (style default 'h2' matches no option — LN-B01)
    # B7 (LN-D07): the legacy ``label`` field is dropped. HeaderConfig has no
    # ``label`` — parse_config silently discarded it and the header value-editor
    # reads config.title ?? config.name (never label). The header text is
    # authored through the feature definition's name (docs §4 / header/type.py
    # dto_to_dao uses feature.name), so a required-but-ignored config field was
    # a port artifact; removed rather than wiring a redundant second source.
    return [
        _f(
            "header", "style", "select", required=True, default="h2",
            params={"options": [
                {"value": "l", "label": "H1 - Large"},
                {"value": "m", "label": "H2 - Medium"},
            ]},
        ),
    ]


#: slug -> builder. Built-ins only; host types declare via ``config_form()``.
BUILTIN_FORMS = {
    "int": _int_form,
    "float": _float_form,
    "string": _string_form,
    "bool": _bool_form,
    "hex_color": _hex_color_form,
    "select": _select_form,
    "hierarchical_select": _hierarchical_select_form,
    "date": _date_form,
    "header": _header_form,
}


def form_declarations() -> Dict[str, Any]:
    """JSON-serializable snapshot of every registered type's config-form
    declaration (built-ins + ``EXTRA_TYPES`` + runtime registrations).

    Shape::

        {
          "<slug>": {
            "label_key": "admin.attributes.type.<slug>",
            "fields": [ {"name", "kind", "label_key", ...}, ... ]
          },
          ...
        }

    Emitted server-side onto the admin page via the widget (no endpoint).
    Types that declare no form (custom types relying only on a JS widget) still
    appear with an empty ``fields`` list.
    """
    # Imported here to avoid a module-import cycle (registry imports base only).
    from stapel_attributes.registry import registered_types

    out: Dict[str, Any] = {}
    for slug, ftype in sorted(registered_types().items()):
        out[slug] = {
            "label_key": f"admin.attributes.type.{slug}",
            "fields": [f.to_dict() for f in ftype.config_form()],
        }
    return out


__all__ = [
    "FIELD_KINDS",
    "FormField",
    "BUILTIN_FORMS",
    "form_declarations",
]
