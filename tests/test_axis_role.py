"""The axis role — which classified axis a feature IS.

The gap this closes: a storefront that wants «Найти больше вариантов этой
марки» has to know which of a leaf's features is the make, and nothing on a
FeatureDef said so — so it kept a closed table of slugs and a catalogue
spelling the axis a fourth way dropped out with nothing red anywhere.
"""
import json
from pathlib import Path

import pytest

from stapel_attributes import FeatureDef
from stapel_attributes.axis import (
    AXIS_ROLES,
    GENERATION,
    MAKE,
    MILEAGE,
    MODEL,
    YEAR,
    UnknownAxisRole,
    axis_role_of,
    by_axis_role,
    normalize_axis_role,
)

CANON = json.loads(
    (Path(__file__).resolve().parent.parent / "docs" / "feature-def.schema.json").read_text()
)


def _def(slug, role, **kw):
    return FeatureDef(slug=slug, config={"type": "string"}, axis_role=role, **kw)


class TestVocabulary:
    def test_the_five_canonical_axes_in_descent_order(self):
        assert AXIS_ROLES == (MAKE, MODEL, GENERATION, YEAR, MILEAGE)

    def test_the_canon_enum_is_the_vocabulary_plus_null(self):
        """One JSON, a fan of emitters — the TS side generates off this."""
        enum = CANON["$defs"]["FeatureDef"]["properties"]["axis_role"]["enum"]
        assert enum == [*AXIS_ROLES, None]

    def test_the_canon_defaults_to_null(self):
        assert CANON["$defs"]["FeatureDef"]["properties"]["axis_role"]["default"] is None


class TestNormalize:
    @pytest.mark.parametrize("blank", [None, ""])
    def test_nothing_said_is_no_role(self, blank):
        assert normalize_axis_role(blank) is None

    @pytest.mark.parametrize("role", AXIS_ROLES)
    def test_every_role_passes_through(self, role):
        assert normalize_axis_role(role) == role

    def test_an_unknown_role_raises_rather_than_dropping(self):
        # The whole failure mode: a catalogue that meant `make` and wrote
        # something else must not end up claiming no axis at all.
        with pytest.raises(UnknownAxisRole) as exc:
            normalize_axis_role("brand")
        assert "brand" in str(exc.value)
        assert "make" in str(exc.value)


class TestFeatureDef:
    def test_defaults_to_none_so_older_definitions_are_unchanged(self):
        assert FeatureDef(slug="color", config={"type": "string"}).axis_role is None

    def test_carries_a_role(self):
        assert _def("make", MAKE).axis_role == MAKE

    def test_normalizes_blank_to_none(self):
        assert _def("color", "").axis_role is None

    def test_refuses_a_typo_at_construction(self):
        with pytest.raises(UnknownAxisRole):
            _def("make", "manufacturer")

    def test_from_dict_accepts_it_like_every_other_field(self):
        built = FeatureDef.from_dict(
            {"slug": "make", "config": {"type": "string"}, "axis_role": "make"}
        )
        assert built.axis_role == MAKE

    def test_from_dict_without_it_is_unchanged(self):
        built = FeatureDef.from_dict({"slug": "color", "config": {"type": "string"}})
        assert built.axis_role is None


class TestAxisRoleOf:
    def test_reads_a_dataclass(self):
        assert axis_role_of(_def("make", MAKE)) == MAKE

    def test_reads_a_comm_payload_dict(self):
        assert axis_role_of({"slug": "make", "axis_role": "make"}) == MAKE

    def test_a_dict_that_says_nothing_is_none(self):
        assert axis_role_of({"slug": "color"}) is None

    def test_a_dict_with_an_explicit_null_is_none(self):
        assert axis_role_of({"slug": "color", "axis_role": None}) is None


class TestByAxisRole:
    def test_the_lookup_that_replaces_a_slug_table(self):
        schema = [
            _def("make_ref_select", MAKE),
            _def("model_ref_select", MODEL),
            _def("god_vypuska", YEAR),
            _def("color", None),
        ]
        found = by_axis_role(schema)
        assert set(found) == {MAKE, MODEL, YEAR}
        # …and it found them by the ROLE, not by any spelling of the slug.
        assert found[MAKE].slug == "make_ref_select"
        assert found[YEAR].slug == "god_vypuska"

    def test_a_schema_that_names_no_axis_answers_empty(self):
        assert by_axis_role([_def("color", None), _def("size", None)]) == {}

    def test_two_features_claiming_one_role_drop_it(self):
        # A reader has no basis to pick between them, and a link built off
        # the wrong one sends a buyer to a facet they did not click.
        found = by_axis_role([_def("brand", MAKE), _def("vendor", MAKE), _def("model", MODEL)])
        assert MAKE not in found
        assert found[MODEL].slug == "model"

    def test_it_reads_dicts_too(self):
        found = by_axis_role([{"slug": "make", "axis_role": "make"}, {"slug": "color"}])
        assert found[MAKE]["slug"] == "make"
