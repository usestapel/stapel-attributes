"""The axis role — which classified AXIS a feature is, when it is one.

Most features are properties of an object: a colour, a floor, a warranty.
A handful are not — they are the *axis* a whole classified is organised
along, and a product has to know which feature that is before it can do
anything with it:

* «Найти больше вариантов этой марки» needs the MAKE feature of the leaf a
  listing sits in, to build the link;
* an AI descent that fills a draft has to answer make before model, and
  model before generation, because each narrows the next
  (``optionsRef.parentFeature``);
* a card that prints "Toyota Camry, 2019" is reading three axes, not three
  arbitrary attributes.

Nothing in a :class:`~stapel_attributes.base.FeatureDef` used to say which
feature that was, so every consumer kept its own closed table of slugs —
``{"brand", "make", "make_ref_select", "vendor"}`` in one storefront — and a
catalogue that spelled the axis a fourth way (``manufacturer``) silently
dropped out of the feature: no link, no descent, no error. A table of slugs
maintained downstream of the catalogue is a table that is always one
catalogue behind.

So the axis is a property of the DEFINITION, decided once, by the catalogue,
and published with the schema (:attr:`FeatureDef.axis_role`). A consumer asks
"which feature here is the make?" and gets an answer or an honest ``None`` —
it never has to guess from a slug again.

**The vocabulary is closed and small.** These five are the axes a classified
is actually organised along; anything else is a property, and a property does
not need a name here to be useful. Adding a sixth is a deliberate change to
this list (and to every emitter of the canon), not something a catalogue can
do by inventing a value — an unknown role RAISES rather than passing through,
because a role nobody downstream switches on is indistinguishable from a typo.

**Absence is the default and means nothing is claimed.** ``None`` is what
every definition written before this axis existed says, and what a feature
that simply is not an axis says. It is never an error, and a consumer must
treat it as "ask the catalogue for a role, get none" — not as "this is not a
make".

**At most one feature per role in one schema.** Two features claiming
``make`` in the same category is a contradiction the reader cannot resolve
(which one does the link use?), so :func:`by_axis_role` drops the role rather
than picking a winner. The producer side (stapel-categories' derivation) does
the same thing one step earlier: an ambiguous leaf derives no role at all and
says so.
"""

from typing import Any, Dict, Iterable, Mapping, Optional

#: The manufacturer axis — Toyota, Samsung, Zara. Spelled ``brand``,
#: ``make``, ``vendor`` or ``manufacturer`` by different catalogues.
MAKE = 'make'
#: The model axis, narrowed by the make — Camry, Galaxy S21.
MODEL = 'model'
#: The generation/revision axis, narrowed by the model — XV70, (2018—2021).
GENERATION = 'generation'
#: The year axis — year of manufacture / release.
YEAR = 'year'
#: The distance-travelled axis — odometer reading.
MILEAGE = 'mileage'

#: Every accepted value of :attr:`FeatureDef.axis_role`, in descent order:
#: each one narrows the next.
AXIS_ROLES = (MAKE, MODEL, GENERATION, YEAR, MILEAGE)


class UnknownAxisRole(ValueError):
    """``FeatureDef.axis_role`` was set to something outside :data:`AXIS_ROLES`."""


def normalize_axis_role(value: Optional[str]) -> Optional[str]:
    """Coerce ``value`` to a known axis role, defaulting to ``None``.

    ``None`` and ``''`` mean "nothing was said", which is ``None`` — a
    definition written before this axis existed keeps working, and a feature
    that is not an axis says exactly the same thing.

    Anything else that is not a known role RAISES rather than being dropped:
    a catalogue that meant ``make`` and wrote ``brand`` would otherwise get a
    feature that silently claims no axis at all, which is the failure this
    field exists to end.
    """
    if value is None or value == '':
        return None
    if value not in AXIS_ROLES:
        raise UnknownAxisRole(
            f"Unknown axis role {value!r}; expected one of {', '.join(AXIS_ROLES)}"
        )
    return value


def axis_role_of(definition: Any) -> Optional[str]:
    """The axis role of one feature definition — dict or dataclass.

    Mirrors :func:`stapel_attributes.visibility.dao_visibility`: consumers
    hold feature definitions in both shapes (a comm payload is a dict, a
    parsed schema is a :class:`FeatureDef`) and neither should have to know
    which one it has.
    """
    if isinstance(definition, Mapping):
        return normalize_axis_role(definition.get('axis_role'))
    return normalize_axis_role(getattr(definition, 'axis_role', None))


def by_axis_role(definitions: Iterable[Any]) -> Dict[str, Any]:
    """``{role: definition}`` over a category's feature definitions.

    The lookup a storefront does instead of keeping a slug table: given the
    schema of a leaf, which feature is the make, which is the model.

    A role claimed by two features is DROPPED, not resolved: the reader has no
    basis to pick between them, and a link built off the wrong one sends a
    buyer to a facet that is not the one they clicked. Absent from the result
    therefore means "this schema does not name that axis" — the same answer a
    schema that never claimed it gives, which is what a caller can act on.
    """
    seen: Dict[str, Any] = {}
    ambiguous = set()
    for definition in definitions:
        role = axis_role_of(definition)
        if role is None:
            continue
        if role in seen:
            ambiguous.add(role)
            continue
        seen[role] = definition
    for role in ambiguous:
        seen.pop(role, None)
    return seen


__all__ = [
    'AXIS_ROLES',
    'GENERATION',
    'MAKE',
    'MILEAGE',
    'MODEL',
    'UnknownAxisRole',
    'YEAR',
    'axis_role_of',
    'by_axis_role',
    'normalize_axis_role',
]
