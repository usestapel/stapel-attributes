"""Tests for the profile-field <-> attribute FIELD_KINDS bridge (§66,
docs/pending/profile-fields.md §4, additive-only slice)."""
from stapel_attributes.config_form import FIELD_KINDS
from stapel_attributes.profile_bridge import PROFILE_KIND_TO_FIELD_KIND, field_kind_for


def test_every_mapped_kind_is_a_real_field_kind():
    """Every non-None value must be a key stapel_attributes.config_form
    actually understands — a stale/typoed mapping would silently break the
    admin config-form render for a projected attribute."""
    for profile_kind, attribute_kind in PROFILE_KIND_TO_FIELD_KIND.items():
        if attribute_kind is not None:
            assert attribute_kind in FIELD_KINDS, (
                f"{profile_kind!r} -> {attribute_kind!r} is not in FIELD_KINDS"
            )


def test_covers_every_profile_field_kind():
    """Mirrors stapel_profiles.field_defs.ProfileFieldKind's members by
    value, without importing stapel-profiles (kept optional/domain-blind) —
    a hardcoded set here is deliberately kept in lockstep by hand."""
    assert set(PROFILE_KIND_TO_FIELD_KIND) == {"text", "bool", "enum", "model_ref", "geohash"}


def test_field_kind_for_known_kinds():
    assert field_kind_for("text") == "text"
    assert field_kind_for("bool") == "checkbox"
    assert field_kind_for("enum") == "select"
    assert field_kind_for("model_ref") == "select_options_with_default"


def test_field_kind_for_geohash_is_not_projectable():
    assert field_kind_for("geohash") is None


def test_field_kind_for_unknown_kind_returns_none():
    assert field_kind_for("nonexistent") is None
