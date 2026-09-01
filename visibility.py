"""The visibility axis — which audience may read a stored value.

Some attributes identify a *specific physical unit*, not a property of it: a
VIN, an IMEI, a serial number, a registry number. They are legitimate catalogue
data — mandatory, validated, moderated, shown to the seller who typed them —
and they must never reach an anonymous reader, because publishing them lets a
stranger impersonate the object: order duplicate keys, clone a handset's
identity, file a registry request against someone else's property.

The axis is a property of the *definition* (:attr:`FeatureDef.visibility`), so
it is decided once, by the catalogue, and not re-decided by every renderer:

``public``
    Anyone may read the value. The default — a feature that says nothing about
    visibility keeps behaving exactly as it did before this axis existed.
``owner``
    Only the object's own owner (and staff) may read the value.
``staff``
    Only staff — moderators, support. Not even the owner's own view. For values
    a product collects but must not echo back at all.

**The stamp travels with the value.** Every read path in the fleet — a listing
card, a detail payload, a search document, a bus event — sees only the stored
DAO; it has no category schema at hand and no cheap way to get one (see
stapel-listings' ``services/features.py``). So the pipeline stamps
``visibility`` into the DAO at write time, next to ``name``/``order``/``badge``,
and every consumer can decide with the value in its hand. A definition whose
visibility changes later needs a re-projection to re-stamp its stored values;
that is what ``listings_reproject_features`` is for.

**Redaction is an allowlist, and its default is the anonymous audience.**
:func:`redact_dao` builds a *new* dict out of the handful of keys that are safe
to publish, rather than deleting the keys it currently knows to be unsafe — so
a feature type that grows a new value-bearing field (a label snapshot, a
resolved option title, a nested subform) is redacted correctly on the day it is
written, without anybody remembering to update this module.

**Presence is not a claim.** The redacted stub keeps ``present`` — "the seller
did fill this in" — and passes through ``verification`` untouched. Presence is
a fact this system observes; verification is a claim about the outside world,
and nothing in the fleet writes one today. A renderer must therefore say
"указан продавцом" off ``present`` and may say "проверен" only off
``verification``. See ``docs/visibility.md``.
"""

from typing import Any, Dict, Mapping, Optional, Sequence

#: Anyone may read the value. The default.
PUBLIC = 'public'
#: The object's owner and staff may read the value.
OWNER = 'owner'
#: Only staff may read the value.
STAFF = 'staff'

#: Every accepted value of ``FeatureDef.visibility``.
VISIBILITIES = (PUBLIC, OWNER, STAFF)

#: The reader is not known, or is not the owner: the fleet-wide default.
ANONYMOUS = 'anonymous'
#: The reader owns the object the values belong to.
AUDIENCE_OWNER = 'owner'
#: The reader is staff — moderation, support, an internal service.
AUDIENCE_STAFF = 'staff'

#: Every accepted audience, weakest first.
AUDIENCES = (ANONYMOUS, AUDIENCE_OWNER, AUDIENCE_STAFF)

# How much each side is worth. A value is readable when the audience's rank is
# at least the visibility's rank. ``staff`` outranks ``owner`` on both sides,
# which is what makes a ``staff`` value invisible in the owner's own view while
# a moderator still sees it.
_VISIBILITY_RANK = {PUBLIC: 0, OWNER: 1, STAFF: 2}
_AUDIENCE_RANK = {ANONYMOUS: 0, AUDIENCE_OWNER: 1, AUDIENCE_STAFF: 2}

#: Keys :func:`redact_dao` copies from a hidden DAO. Presentation metadata
#: only: enough to render "this field exists and the seller answered it",
#: nothing that carries or reconstructs the answer.
REDACTED_KEYS = ('slug', 'type', 'name', 'order', 'translate', 'visibility', 'verification')

#: What a redacted DAO says about itself, so a renderer never has to infer
#: "the value is missing" from "the ``value`` key is absent".
REDACTED_MARKER = 'redacted'

#: Whether the (hidden) value is actually filled in.
PRESENCE_MARKER = 'present'


class UnknownVisibility(ValueError):
    """``FeatureDef.visibility`` was set to something outside :data:`VISIBILITIES`."""


def normalize_visibility(value: Optional[str]) -> str:
    """Coerce ``value`` to a known visibility, defaulting to :data:`PUBLIC`.

    ``None`` and ``''`` mean "nothing was said", which is ``public`` — the
    whole point of the default is that a definition written before this axis
    existed keeps working. Anything else that is *not* a known visibility is an
    error rather than a silent downgrade: a typo like ``"private"`` must not
    quietly publish a VIN.
    """
    if value is None or value == '':
        return PUBLIC
    if value not in _VISIBILITY_RANK:
        raise UnknownVisibility(
            f"Unknown visibility {value!r}; expected one of {', '.join(VISIBILITIES)}"
        )
    return value


def normalize_audience(value: Optional[str]) -> str:
    """Coerce ``value`` to a known audience, defaulting to :data:`ANONYMOUS`.

    Fail-closed on purpose: an unknown or missing audience is the *weakest*
    one, so a caller that forgets to pass a viewer, or passes a role name this
    library has never heard of, gets the redacted payload rather than the
    values.
    """
    if value is None:
        return ANONYMOUS
    return value if value in _AUDIENCE_RANK else ANONYMOUS


def is_visible_to(visibility: Optional[str], audience: Optional[str]) -> bool:
    """Whether a value of ``visibility`` may be read by ``audience``."""
    return _AUDIENCE_RANK[normalize_audience(audience)] >= _VISIBILITY_RANK[
        normalize_visibility(visibility)
    ]


def dao_visibility(dao: Any) -> str:
    """The visibility stamped on a stored DAO (dict or dataclass)."""
    if isinstance(dao, Mapping):
        return normalize_visibility(dao.get('visibility'))
    return normalize_visibility(getattr(dao, 'visibility', None))


def is_public(dao: Any) -> bool:
    """Whether a stored DAO may be read by anyone — the indexer's predicate."""
    return dao_visibility(dao) == PUBLIC


def has_value(dao: Mapping[str, Any]) -> bool:
    """Whether the DAO actually carries an answer.

    Mirrors ``validation.is_blank_value``: absent, ``None``, ``''`` and ``[]``
    are "not answered"; every zero value of every other kind is an answer, so a
    hidden ``0`` or ``False`` still reports as present.
    """
    if 'value' not in dao:
        return False
    raw = dao['value']
    return not (raw is None or raw == '' or raw == [])


def redact_dao(dao: Mapping[str, Any]) -> Dict[str, Any]:
    """Return the publishable stub of a hidden DAO.

    Built by *copying an allowlist*, never by deleting a denylist — see this
    module's docstring. The result carries no value and no label, only:

    - the identity of the field (``slug``, ``type``, ``name``, ``order``,
      ``translate``, ``visibility``),
    - ``redacted: True`` — "this is deliberately not the value",
    - ``present`` — whether the seller answered,
    - ``verification`` if the value has one, passed through verbatim so a real
      verification result (when some product grows one) drives the badge
      without another pass through this function.

    ``title``/``badge`` are deliberately NOT copied: a hidden value is never a
    title or a badge, so the flags would be lies even on a stub.
    """
    out = {key: dao[key] for key in REDACTED_KEYS if key in dao and dao[key] is not None}
    out[REDACTED_MARKER] = True
    out[PRESENCE_MARKER] = has_value(dao)
    return out


def redact_daos(
    daos: Sequence[Mapping[str, Any]],
    audience: Optional[str] = None,
) -> list:
    """Redact an ordered ``List[FeatureDao]`` for ``audience``.

    The listing projection's chokepoint. Hidden entries are kept in place, as
    stubs, rather than dropped: the seller's own attribute table and the public
    one then have the same rows in the same order, and the public one says
    "VIN — указан продавцом" where the seller's says the number. Dropping the
    row instead would make the field's very existence invisible, which is a
    worse answer for a buyer deciding whether to ask.
    """
    resolved = normalize_audience(audience)
    return [
        dict(dao) if is_visible_to(dao_visibility(dao), resolved) else redact_dao(dao)
        for dao in daos
    ]


def public_daos(daos: Sequence[Mapping[str, Any]]) -> list:
    """The subset of ``daos`` an anonymous reader may see, hidden ones *dropped*.

    For projections where a stub would be nonsense rather than useful: a title
    line, a badge strip, a search document. Nobody wants to read
    "Toyota Camry, VIN редактирован" in a title.
    """
    return [dict(dao) for dao in daos if is_public(dao)]


def public_slugs(daos: Sequence[Mapping[str, Any]]) -> set:
    """The slugs in ``daos`` that are safe to index or facet."""
    return {dao['slug'] for dao in daos if 'slug' in dao and is_public(dao)}


__all__ = [
    'ANONYMOUS',
    'AUDIENCES',
    'AUDIENCE_OWNER',
    'AUDIENCE_STAFF',
    'OWNER',
    'PRESENCE_MARKER',
    'PUBLIC',
    'REDACTED_KEYS',
    'REDACTED_MARKER',
    'STAFF',
    'UnknownVisibility',
    'VISIBILITIES',
    'dao_visibility',
    'has_value',
    'is_public',
    'is_visible_to',
    'normalize_audience',
    'normalize_visibility',
    'public_daos',
    'public_slugs',
    'redact_dao',
    'redact_daos',
]
