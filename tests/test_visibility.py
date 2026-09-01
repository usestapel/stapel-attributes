"""The visibility axis: the stamp, the ranking, and the redaction allowlist.

The product ruling behind these tests: a VIN and an IMEI identify a specific
physical unit, so they may be collected, validated, stored and moderated — and
never handed to an anonymous reader. Everything here is written against a VIN
because that is the value that was live on the stand when the axis was built.
"""
import pytest

from stapel_attributes.base import FeatureDef
from stapel_attributes.exceptions import FeatureValidationError
from stapel_attributes.registry import dto_to_dao, parse_dto
from stapel_attributes.results import ValidationErrorCode
from stapel_attributes.validation import normalize_to_dao, validate_dto_structured
from stapel_attributes.visibility import (
    ANONYMOUS,
    AUDIENCE_OWNER,
    AUDIENCE_STAFF,
    OWNER,
    PUBLIC,
    STAFF,
    UnknownVisibility,
    dao_visibility,
    has_value,
    is_public,
    is_visible_to,
    normalize_audience,
    normalize_visibility,
    public_daos,
    public_slugs,
    redact_dao,
    redact_daos,
)

VIN_CONFIG = {"type": "string", "minLength": 17, "maxLength": 17}


def vin_def(**overrides):
    kwargs = dict(
        slug="vin",
        name="VIN, номер кузова или SN",
        config=dict(VIN_CONFIG),
        mandatory=True,
        visibility=OWNER,
    )
    kwargs.update(overrides)
    return FeatureDef(**kwargs)


# ---------------------------------------------------------------- the default

class TestPublicIsTheDefault:
    """Adding an axis must not change one byte of an existing definition."""

    def test_a_feature_def_that_says_nothing_is_public(self):
        assert FeatureDef(slug="color", config={"type": "string"}).visibility == PUBLIC

    def test_a_public_dao_carries_no_visibility_key_at_all(self):
        feature = FeatureDef(slug="color", config={"type": "string"})
        dao = dto_to_dao(feature.config, parse_dto("string", {"value": "чёрный"}), feature)
        assert dao.visibility is None
        stored = normalize_to_dao([feature], {"color": {"type": "string", "value": "чёрный"}})
        assert "visibility" not in stored["color"]

    @pytest.mark.parametrize("blank", [None, ""])
    def test_blank_means_public_not_an_error(self, blank):
        assert normalize_visibility(blank) == PUBLIC


# ------------------------------------------------------------------ the stamp

class TestTheStampTravelsWithTheValue:
    """Every read path in the fleet sees the stored DAO and nothing else."""

    def test_dto_to_dao_stamps_visibility_from_the_definition(self):
        feature = vin_def()
        dao = dto_to_dao(
            feature.config, parse_dto("string", {"value": "JTNBE40K803512345"}), feature
        )
        assert dao.visibility == OWNER
        assert dao.value == "JTNBE40K803512345"

    def test_the_pipeline_stamps_it_into_the_stored_projection(self):
        stored = normalize_to_dao(
            [vin_def()], {"vin": {"type": "string", "value": "JTNBE40K803512345"}}
        )
        assert stored["vin"]["visibility"] == OWNER

    def test_a_hidden_value_is_still_validated(self):
        """Hiding is not an excuse to stop checking. A short VIN is still an error."""
        result = validate_dto_structured(
            [vin_def()], {"vin": {"type": "string", "value": "TOO-SHORT"}}
        )
        assert result.valid is False
        assert {r.slug: r.error for r in result.results} == {
            "vin": ValidationErrorCode.BELOW_MINIMUM
        }

    def test_a_hidden_value_is_still_mandatory(self):
        """The axis is orthogonal to requiredness — hidden does not mean optional."""
        result = validate_dto_structured([vin_def()], {})
        assert result.valid is False
        assert {r.slug: r.error for r in result.results} == {
            "vin": ValidationErrorCode.MANDATORY_MISSING
        }

    def test_a_hidden_value_is_still_stored(self):
        stored = normalize_to_dao(
            [vin_def()], {"vin": {"type": "string", "value": "JTNBE40K803512345"}}
        )
        assert stored["vin"]["value"] == "JTNBE40K803512345"

    def test_every_registered_type_can_be_stamped(self):
        """The stamp lives in the registry, so no type author can forget it.

        If someone adds a DAO that does not inherit ``DaoMeta``, this fails on
        the day the type lands rather than on the day it is used to hold a
        serial number.
        """
        from stapel_attributes.registry import get_all_feature_types

        missing = [
            ft.slug
            for ft in get_all_feature_types()
            if "visibility" not in {f.name for f in __import__("dataclasses").fields(ft.dao_class)}
        ]
        assert missing == [], f"DAO types that cannot carry a visibility stamp: {missing}"

    def test_an_unstampable_dao_refuses_to_store_a_hidden_value(self):
        """Fail closed: better a 500 than a silently published identifier."""
        from dataclasses import dataclass

        from typing import Literal

        from stapel_attributes.base import BaseFeatureType, DictDataclassSerializer
        from stapel_attributes.registry import register_feature_type
        from stapel_attributes.types.string.dto import StringDto, StringDtoSerializer

        @dataclass
        class BareConfig:
            type: Literal["legacy_bare"] = "legacy_bare"

        class BareConfigSerializer(DictDataclassSerializer):
            class Meta:
                dataclass = BareConfig

        @dataclass
        class BareDao:  # deliberately NOT a DaoMeta
            type: str = "legacy_bare"
            value: str = ""

        class BareDaoSerializer(DictDataclassSerializer):
            class Meta:
                dataclass = BareDao

        class BareType(BaseFeatureType):
            slug = "legacy_bare"
            name = "Bare"
            config_class = BareConfig
            dto_class = StringDto
            dao_class = BareDao
            config_serializer_class = BareConfigSerializer
            dto_serializer_class = StringDtoSerializer
            dao_serializer_class = BareDaoSerializer

            def validate_config(self, config):
                return None

            def validate_dto(self, config, dto):
                return None

            def dto_to_dao(self, config, dto, feature):
                return BareDao(value=dto.value)

        register_feature_type(BareType)
        try:
            feature = FeatureDef(slug="sn", config={"type": "legacy_bare"}, visibility=STAFF)
            with pytest.raises(FeatureValidationError, match="no 'visibility' field"):
                dto_to_dao(feature.config, parse_dto("legacy_bare", {"value": "x"}), feature)
            # ... and a PUBLIC one still works, so the guard costs nothing.
            public = FeatureDef(slug="sn", config={"type": "legacy_bare"})
            assert dto_to_dao(public.config, parse_dto("legacy_bare", {"value": "x"}), public)
        finally:
            from stapel_attributes.registry import _FEATURE_TYPES

            _FEATURE_TYPES.pop("legacy_bare", None)


class TestATyposMustNotPublish:
    def test_an_unknown_visibility_is_an_error_not_a_downgrade(self):
        with pytest.raises(UnknownVisibility):
            FeatureDef(slug="vin", config=dict(VIN_CONFIG), visibility="private")

    def test_from_dict_carries_the_axis(self):
        feature = FeatureDef.from_dict(
            {"slug": "imei", "config": {"type": "string"}, "visibility": "owner"}
        )
        assert feature.visibility == OWNER


class TestHiddenIsNeverATitleOrABadge:
    """Two flags that would otherwise put the value on the card itself."""

    def test_the_definition_resolves_the_contradiction_towards_hiding(self):
        feature = vin_def(show_at_title=True, show_as_badge=True)
        assert feature.show_at_title is False
        assert feature.show_as_badge is False

    def test_the_stored_dao_makes_no_title_or_badge_claim(self):
        stored = normalize_to_dao(
            [vin_def(show_at_title=True)],
            {"vin": {"type": "string", "value": "JTNBE40K803512345"}},
        )
        assert stored["vin"].get("title") is None
        assert stored["vin"].get("badge") is None


# --------------------------------------------------------------- the ranking

class TestWhoMaySee:
    @pytest.mark.parametrize(
        "visibility,audience,expected",
        [
            (PUBLIC, ANONYMOUS, True),
            (PUBLIC, AUDIENCE_OWNER, True),
            (PUBLIC, AUDIENCE_STAFF, True),
            (OWNER, ANONYMOUS, False),
            (OWNER, AUDIENCE_OWNER, True),
            (OWNER, AUDIENCE_STAFF, True),
            (STAFF, ANONYMOUS, False),
            # 'staff' outranks 'owner': a value the product must not echo back
            # to the person who typed it is still readable by moderation.
            (STAFF, AUDIENCE_OWNER, False),
            (STAFF, AUDIENCE_STAFF, True),
        ],
    )
    def test_the_grid(self, visibility, audience, expected):
        assert is_visible_to(visibility, audience) is expected

    @pytest.mark.parametrize("bogus", [None, "", "admin", "superuser", "root", "moderator"])
    def test_an_unknown_or_missing_audience_is_the_weakest_one(self, bogus):
        """Fail closed. Forgetting to pass a viewer must redact, never publish."""
        assert normalize_audience(bogus) == ANONYMOUS
        assert is_visible_to(OWNER, bogus) is False


# -------------------------------------------------------------- the redaction

class TestRedactionIsAnAllowlist:
    """The property that survives a feature type growing a new value field."""

    def test_a_redacted_dao_carries_no_value(self):
        dao = {
            "slug": "vin",
            "type": "string",
            "name": "VIN",
            "order": 15,
            "visibility": OWNER,
            "value": "JTNBE40K803512345",
        }
        out = redact_dao(dao)
        assert "value" not in out
        assert "JTNBE40K803512345" not in repr(out)
        assert out["redacted"] is True
        assert out["present"] is True

    def test_an_unknown_value_bearing_key_is_dropped_without_anyone_updating_this_module(self):
        """The whole reason redaction copies instead of deletes.

        ``labels``/``options_snapshot`` are real: ``ref_select`` snapshots its
        option labels into the DAO. A denylist would have published them.
        """
        dao = {
            "slug": "vin",
            "type": "ref_select",
            "name": "VIN",
            "visibility": OWNER,
            "value": ["JTNBE40K803512345"],
            "labels": ["JTNBE40K803512345"],
            "some_future_snapshot_field": "JTNBE40K803512345",
        }
        out = redact_dao(dao)
        assert "JTNBE40K803512345" not in repr(out)
        assert set(out) <= {"slug", "type", "name", "order", "translate", "visibility",
                            "verification", "redacted", "present"}

    def test_a_redacted_stub_never_claims_title_or_badge(self):
        out = redact_dao({"slug": "vin", "type": "string", "value": "x", "title": True,
                          "badge": True, "visibility": OWNER})
        assert "title" not in out and "badge" not in out

    @pytest.mark.parametrize(
        "value,present",
        [
            ("JTNBE40K803512345", True),
            ("", False),
            (None, False),
            ([], False),
            # Every zero value of every other kind is an ANSWER, mirroring
            # ``validation.is_blank_value``.
            (0, True),
            (False, True),
            (0.0, True),
        ],
    )
    def test_presence_mirrors_the_blankness_predicate(self, value, present):
        assert has_value({"value": value}) is present
        assert redact_dao({"slug": "vin", "value": value, "visibility": OWNER})["present"] is present

    def test_a_missing_value_key_is_absent_not_present(self):
        assert has_value({"slug": "vin"}) is False

    def test_verification_passes_through_so_a_real_check_can_drive_the_badge(self):
        """Nothing in the fleet writes one today — the shape is reserved, not faked."""
        dao = {
            "slug": "vin",
            "value": "JTNBE40K803512345",
            "visibility": OWNER,
            "verification": {"status": "verified", "verified_at": "2026-09-02T10:00:00Z",
                             "source": "gibdd"},
        }
        out = redact_dao(dao)
        assert out["verification"]["status"] == "verified"
        assert "value" not in out

    def test_the_engine_never_synthesizes_a_verification(self):
        """Honesty gate: presence is observed, verification is claimed.

        The renderer may say «указан продавцом» off ``present``; it may say
        «проверен» only off ``verification``, and this proves the pipeline does
        not quietly manufacture one.
        """
        stored = normalize_to_dao(
            [vin_def()], {"vin": {"type": "string", "value": "JTNBE40K803512345"}}
        )
        assert "verification" not in stored["vin"]
        assert redact_dao({**stored["vin"], "slug": "vin"}).get("verification") is None


class TestTheTwoProjectionShapes:
    """A stub where the row should stay; a drop where a stub would be noise."""

    def setup_method(self):
        self.daos = [
            {"slug": "color", "type": "select", "value": ["чёрный"], "title": True},
            {"slug": "vin", "type": "string", "value": "JTNBE40K803512345", "visibility": OWNER},
            {"slug": "note", "type": "string", "value": "n", "visibility": STAFF},
        ]

    def test_the_attribute_table_keeps_the_row_as_a_stub(self):
        """The buyer must be able to see that the field exists and was filled."""
        out = redact_daos(self.daos, ANONYMOUS)
        assert [d["slug"] for d in out] == ["color", "vin", "note"]
        assert out[0]["value"] == ["чёрный"]
        assert out[1] == {"slug": "vin", "type": "string", "visibility": OWNER,
                          "redacted": True, "present": True}

    def test_the_owner_sees_their_own_value_but_not_the_staff_one(self):
        out = redact_daos(self.daos, AUDIENCE_OWNER)
        assert out[1]["value"] == "JTNBE40K803512345"
        assert out[2]["redacted"] is True

    def test_staff_sees_everything(self):
        out = redact_daos(self.daos, AUDIENCE_STAFF)
        assert [d.get("value") for d in out] == [["чёрный"], "JTNBE40K803512345", "n"]

    def test_redaction_does_not_mutate_the_stored_rows(self):
        redact_daos(self.daos, ANONYMOUS)
        assert self.daos[1]["value"] == "JTNBE40K803512345"

    def test_a_title_or_badge_or_index_drops_the_row_entirely(self):
        """Nobody wants to read "Toyota Camry, VIN скрыт" in a title."""
        assert [d["slug"] for d in public_daos(self.daos)] == ["color"]
        assert public_slugs(self.daos) == {"color"}

    def test_the_default_audience_is_anonymous(self):
        assert redact_daos(self.daos)[1]["redacted"] is True


class TestDaoHelpers:
    def test_visibility_reads_off_a_dict_or_a_dataclass(self):
        feature = vin_def()
        dao = dto_to_dao(feature.config, parse_dto("string", {"value": "J" * 17}), feature)
        assert dao_visibility(dao) == OWNER
        assert dao_visibility({"visibility": OWNER}) == OWNER
        assert dao_visibility({}) == PUBLIC
        assert is_public({}) is True
        assert is_public({"visibility": STAFF}) is False
