"""stapel_attributes.openapi — stable enum names for the type discriminators."""
from stapel_attributes.openapi import enum_name_overrides, type_enum_name
from stapel_attributes.registry import get_all_type_slugs


def test_each_registered_type_gets_a_name_from_its_slug():
    overrides = enum_name_overrides()

    assert sorted(v[0] for v in overrides.values()) == get_all_type_slugs()
    assert overrides["SelectTypeEnum"] == ["select"]
    assert overrides["RefHierarchicalSelectTypeEnum"] == ["ref_hierarchical_select"]


def test_names_are_unique():
    names = list(enum_name_overrides())
    assert len(names) == len(set(names))


def test_type_enum_name():
    assert type_enum_name("hex_color") == "HexColorTypeEnum"
    assert type_enum_name("int") == "IntTypeEnum"
