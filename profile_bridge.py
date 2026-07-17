"""Profile-field <-> attribute FIELD_KINDS bridge (§66 slice, ADDITIVE ONLY —
docs/pending/profile-fields.md §4).

Small, one-directional, optional dependency: `stapel-profiles` describes a
profile field's shape as a `stapel_profiles.field_defs.ProfileFieldKind`
(``text``/``bool``/``enum``/``model_ref``/``geohash``) — its OWN vocabulary,
Django-model-field-shaped, not admin-config-form-shaped. When a shop/
classified projection (docs/pending/projections-and-composition.md) builds a
filterable/convertible attribute FROM a profile field (e.g. category
"Services" wants a filter on ironmemo's ``occupation``), it needs a
:data:`stapel_attributes.config_form.FIELD_KINDS` entry to render that
attribute's admin config form — this module is the one small lookup table
that answers "which FIELD_KINDS key matches this ProfileFieldKind", so the
projection never re-derives the mapping (or worse, duplicates choices) by
hand.

This module does NOT import `stapel_profiles` at module load time — that
would give `stapel-attributes` a hard dependency on a sibling package it has
no other reason to need (attributes stays domain-blind, per
projections-and-composition.md §3's "target-generic engines" convention).
`stapel_profiles.field_defs.ProfileFieldDef.attribute_kind` is the one
caller, and it already only imports THIS module inside a try/except
ImportError — so in practice this file only ever runs in a process that
already has stapel-profiles installed, but it stays importable (and its own
dict inspectable) even when it doesn't.
"""
from __future__ import annotations

from typing import Dict, Optional

#: `ProfileFieldKind.value` -> `stapel_attributes.config_form.FIELD_KINDS`
#: key, or ``None`` when a profile field kind has no attribute-projectable
#: admin-config-form shape at all (``geohash`` — proximity search, not a
#: discrete filterable value).
PROFILE_KIND_TO_FIELD_KIND: Dict[str, Optional[str]] = {
    "text": "text",
    "bool": "checkbox",
    "enum": "select",                      # ProfileFieldDef.enum.choices -> select's fixed inline options
    "model_ref": "select_options_with_default",  # live catalog -> dropdown, no fixed inline options
    "geohash": None,                       # not attribute-projectable — proximity, not a discrete filter
}


def field_kind_for(profile_kind: str) -> Optional[str]:
    """The :data:`stapel_attributes.config_form.FIELD_KINDS` key matching a
    ``ProfileFieldKind`` value (its ``.value``, a plain string so this module
    never needs to import the enum type itself). Unknown/unmapped input
    returns ``None`` rather than raising — an unrecognised profile field kind
    just means "not projectable yet", not a caller error.
    """
    return PROFILE_KIND_TO_FIELD_KIND.get(profile_kind)


__all__ = ["PROFILE_KIND_TO_FIELD_KIND", "field_kind_for"]
