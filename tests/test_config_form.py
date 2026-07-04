"""Stage 1 — field-kind config-form contract (docs/attributes-admin-ui.md decision 1).

Covers the spec's required py-tests (completeness, kinds-in-dictionary,
JSON-serializability, custom-type pickup) plus the 1:1-port edge cases from
static_src/LOGIC-NOTES.md (§2 declarations, LN-B* preserved bugs).
"""
import json

import pytest

from stapel_attributes import (
    FIELD_KINDS,
    FormField,
    form_declarations,
    get_feature_type,
    register_feature_type,
)
from stapel_attributes.base import BaseFeatureType

BUILTIN_SLUGS = {
    "int", "float", "string", "bool", "hex_color",
    "select", "hierarchical_select", "date", "header",
}


def _fields(slug):
    return get_feature_type(slug).config_form()


def _by_name(slug):
    return {f.name: f for f in _fields(slug)}


# --------------------------------------------------------------------------- #
# Required: completeness / kinds / serializability / custom pickup
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("slug", sorted(BUILTIN_SLUGS))
def test_every_builtin_type_declares_a_nonempty_form(slug):
    fields = _fields(slug)
    assert fields, f"{slug} declares no config form"
    assert all(isinstance(f, FormField) for f in fields)


def test_every_declared_kind_is_in_the_kind_dictionary():
    for slug in BUILTIN_SLUGS:
        for f in _fields(slug):
            assert f.kind in FIELD_KINDS, f"{slug}.{f.name}: unknown kind {f.kind!r}"


def test_form_declarations_is_json_serializable_and_shaped():
    decls = form_declarations()
    dumped = json.dumps(decls)  # must not raise
    reparsed = json.loads(dumped)
    for slug in BUILTIN_SLUGS:
        assert slug in reparsed
        entry = reparsed[slug]
        assert entry["label_key"] == f"admin.attributes.type.{slug}"
        assert isinstance(entry["fields"], list)
        for f in entry["fields"]:
            assert {"name", "kind", "label_key"} <= set(f)
            assert f["kind"] in FIELD_KINDS


def test_form_declarations_covers_all_builtins():
    assert BUILTIN_SLUGS <= set(form_declarations())


def test_custom_runtime_type_is_picked_up(registry_snapshot):
    from stapel_attributes.tests.sample_types import RatingFeatureType

    register_feature_type(RatingFeatureType)
    decls = form_declarations()
    assert "rating" in decls
    # No config_form() override -> empty fields, still declared with a label_key.
    assert decls["rating"]["fields"] == []
    assert decls["rating"]["label_key"] == "admin.attributes.type.rating"


def test_custom_type_can_declare_its_own_form(registry_snapshot):
    class WidgetType(BaseFeatureType):
        slug = "widget_demo"
        name = "Widget Demo"
        config_class = dto_class = dao_class = dict  # unused by config_form
        config_serializer_class = dto_serializer_class = dao_serializer_class = object

        def config_form(self):
            return [FormField("size", "number", "admin.attributes.form.widget_demo.size", params={"step": 1})]

        def validate_config(self, config): ...
        def validate_dto(self, config, dto): ...
        def dto_to_dao(self, config, dto, feature): ...

    register_feature_type(WidgetType)
    entry = form_declarations()["widget_demo"]
    assert entry["fields"] == [{
        "name": "size", "kind": "number",
        "label_key": "admin.attributes.form.widget_demo.size", "params": {"step": 1},
    }]


# --------------------------------------------------------------------------- #
# FormField.to_dict shape
# --------------------------------------------------------------------------- #

def test_to_dict_omits_none_and_empty_optionals():
    assert FormField("x", "text", "k").to_dict() == {"name": "x", "kind": "text", "label_key": "k"}
    full = FormField("y", "checkbox", "k2", required=True, default=True, params={"a": 1}).to_dict()
    assert full == {"name": "y", "kind": "checkbox", "label_key": "k2", "required": True, "default": True, "params": {"a": 1}}


def test_default_false_and_zero_are_emitted_but_none_is_not():
    # LN-B15: hex_color.allowCustom default False must survive serialization
    # (drives the faithful unchecked initial state). Only None is omitted.
    assert FormField("allowCustom", "checkbox", "k", default=False).to_dict()["default"] is False
    assert FormField("minSelected", "number", "k", default=0).to_dict()["default"] == 0
    assert "default" not in FormField("x", "text", "k").to_dict()


def test_label_keys_are_namespaced_per_type_and_field():
    for slug in BUILTIN_SLUGS:
        for f in _fields(slug):
            assert f.label_key == f"admin.attributes.form.{slug}.{f.name}"


# --------------------------------------------------------------------------- #
# 1:1 port fidelity — per-type declarations & preserved bugs (LOGIC-NOTES §2, LN-B*)
# --------------------------------------------------------------------------- #

def test_int_field_order_and_kinds():  # LN-T-int
    fields = _fields("int")
    assert [f.name for f in fields] == [
        "min", "max", "options", "allowCustom", "prefix", "postfix", "postfix1000", "placeholder",
    ]
    kinds = {f.name: f.kind for f in fields}
    assert kinds["min"] == kinds["max"] == "number"
    assert kinds["options"] == "number_options"
    assert _by_name("int")["options"].params["itemType"] == "number"
    assert _by_name("int")["min"].params["step"] == 1
    assert _by_name("int")["allowCustom"].default is True


def test_float_has_precision_default_2_and_step_001():  # LN-T-float
    f = _by_name("float")
    assert f["precision"].kind == "number" and f["precision"].default == 2
    assert f["min"].params["step"] == 0.01
    assert "postfix1000" in f  # int/float have it


def test_string_has_no_postfix1000_and_pattern_is_plain_text():  # LN-B17
    f = _by_name("string")
    assert "postfix1000" not in f
    assert f["pattern"].kind == "text"
    assert f["options"].kind == "string_options"
    assert "itemType" not in f["options"].params  # string_options has no itemType


def test_hex_color_allowCustom_defaults_false():  # LN-B15
    assert _by_name("hex_color")["allowCustom"].default is False


def test_bool_two_translatable_labels():  # LN-T-bool
    f = _by_name("bool")
    assert set(f) == {"trueLabel", "falseLabel"}
    assert all(f[n].kind == "translatable_text" for n in f)


def test_select_declaration():  # LN-T-select
    f = _by_name("select")
    assert f["options"].kind == "select_options_with_default"
    assert f["uiStyle"].kind == "select" and f["uiStyle"].required and f["uiStyle"].default == "chips"
    assert [o["value"] for o in f["uiStyle"].params["options"]] == ["chips", "checkboxes", "dropdown"]
    assert f["minSelected"].default == 0
    assert f["maxSelected"].kind == "max_selected_dropdown" and f["maxSelected"].default == 1
    assert "lockUserInput" in f  # LN-B16 naming


def test_hierarchical_single_tree_field():  # LN-T-hierarchical_select
    f = _fields("hierarchical_select")
    assert len(f) == 1 and f[0].name == "options" and f[0].kind == "hierarchical_options"


def test_date_declaration_and_naming_quirks():  # LN-T-date, LN-B16
    f = _by_name("date")
    assert f["precision"].kind == "select" and f["precision"].default == "date"
    assert [o["value"] for o in f["precision"].params["options"]] == ["year", "month", "date", "datetime"]
    assert f["minDate"].kind == f["maxDate"].kind == "timestamp"
    assert "default" in f and f["default"].kind == "timestamp"   # field literally named 'default'
    assert f["options"].kind == "timestamp_array"
    assert "lockInput" in f and "lockUserInput" not in f          # LN-B16: date uses lockInput
    assert f["placeholder"].kind == "text"                        # LN-B17: not translatable_text


def test_header_style_default_h2_matches_no_option():  # LN-B01 (latent bug preserved 1:1)
    f = _by_name("header")
    assert f["style"].default == "h2"
    option_values = {o["value"] for o in f["style"].params["options"]}
    assert option_values == {"l", "m"}
    assert f["style"].default not in option_values  # the preserved mismatch
    assert f["label"].kind == "text" and f["label"].required
