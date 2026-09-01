# The visibility axis

## What it is for

Some attributes do not describe an object — they *identify* one. A VIN, an
IMEI, a serial number, a registry number: knowing the value lets a stranger act
as if they were the owner of that specific unit. Order duplicate keys against
the VIN. Clone a handset's identity from its IMEI. File a registry request
against someone else's flat.

These are legitimate catalogue fields. A marketplace wants them: mandatory,
validated, moderated, deduplicated on. What it must not do is print them on a
public page — and, worse, let a stranger *query* them, which turns the search
index into an oracle that confirms "yes, listing 287 is the car with this VIN".

`FeatureDef.visibility` is the one place that decision is recorded.

| value | who may read a stored value |
|---|---|
| `public` | anyone — **the default**, so nothing that existed before this axis changed |
| `owner` | the object's owner, and staff |
| `staff` | staff only — not even the owner's own view |

It is **orthogonal to `mandatory`**. A non-public feature is still required,
still validated against its config, still stored verbatim, still visible to
moderation, still editable by the seller. It is only never handed to a reader
who is not entitled to it.

It also forces `show_at_title` and `show_as_badge` to `false`. A definition may
hold that contradiction (a feature flagged as a badge years before someone
marked it hidden); the engine resolves it in the only direction that cannot
leak.

## Where enforcement lives

Not in the renderers. Asking every serializer, card, badge strip, index writer
and bus payload to remember a rule is how the VIN got out in the first place:
`features` was a plain `JSONField` and every new serializer that listed it
inherited the leak for free.

Instead, three mechanisms, in order of how much they can be defeated:

**1. The stamp travels with the value.** Every read path in the fleet sees the
stored DAO and nothing else — a listing card, a detail payload, a search
document and a bus event all read a JSON column, with no category schema at
hand and no cheap way to fetch one. So `registry.dto_to_dao` stamps
`visibility` into the DAO next to `name`/`order`/`badge`, at write time, for
every registered type including ones the host registered itself. A type author
cannot forget it, because they never write it. A DAO that *cannot* carry the
stamp refuses to store a non-public value at all — a 500 beats a published
identifier.

`public` is stamped as `None`, which `dataclass_to_dict_no_none` drops, so the
axis costs zero bytes on the values that are public and a re-projection leaves
an existing public row byte-identical.

**2. Redaction is an allowlist.** `visibility.redact_dao` builds a *new* dict
out of the handful of keys that are safe to publish, rather than deleting the
keys it currently knows to be unsafe. This is the property that survives the
future: when a feature type grows a new value-bearing field — `ref_select`
already snapshots its option `labels` into the DAO — the redaction is correct
on the day that field is written, without anybody remembering this module
exists.

**3. A source-level gate.** `guard.assert_raw_access_confined` reads a
consumer's own source and fails if the raw value column is mentioned outside a
short, named list of files. Behavioural tests prove today's payloads are clean;
they say nothing about the endpoint somebody adds next quarter. Adding a file
to the `allow` list is a line in a test with a comment saying which audience it
serves — which is exactly the review conversation that should happen.

## The two projection shapes

Hidden values leave the system in one of two ways, and the choice is about what
the reader is trying to learn.

`redact_daos(daos, audience)` — **keeps the row, as a stub.** For the attribute
table on a detail page. The public table and the seller's own table then have
the same rows in the same order; the public one says "VIN — указан продавцом"
where the seller's says the number. Dropping the row instead would make the
field's very existence invisible, which is a worse answer for a buyer deciding
whether to ask.

A stub carries `{slug, type, name, order, translate, visibility, verification}`
plus `redacted: true` and `present: <bool>` — never `value`, never `title`,
never `badge`.

`public_daos(daos)` / `public_slugs(daos)` — **drops the row.** For a title
line, a badge strip, a search document, a facet plan. Nobody wants to read
"Toyota Camry, VIN скрыт" in a title, and a stub in an index is a slug waiting
to be filtered on.

## Presence is a fact; verification is a claim

The stub reports `present` — did the seller actually fill this in — and that is
all the fleet can honestly say today, because **nothing in the fleet runs a VIN
check**. A renderer may therefore say «VIN указан продавцом». It may **not** say
«VIN проверен», which asserts something about the outside world that no code
here has established.

The DAO reserves `verification` for the day something does:

```json
{"status": "verified", "verified_at": "2026-09-02T10:00:00Z", "source": "<who checked>"}
```

It is passed through redaction untouched, so the badge upgrades itself the
moment a real integration writes one — and the engine never synthesizes one, so
the badge cannot upgrade by accident. `stapel_attributes` deliberately does not
define the `status` vocabulary beyond "absent means nobody checked": the
product that runs the check owns what its outcomes mean.

What a real integration would need, and none of which exists in this slice: a
provider seam (registry lookup per country), a stored result with a checked-at
timestamp and a TTL, a re-check trigger when the value is edited, a rule for
what a *failed* check does to the listing's moderation state, and a decision
about whether a failed check is shown publicly at all.

## Migrating existing data

The stamp is written at projection time, so values stored before a definition
became non-public still carry no stamp and still read as public. Changing a
`FeatureDef.visibility` is therefore **not** complete until the values are
re-projected:

```
python manage.py listings_reproject_features --category <id>
```

That re-runs `normalize_to_dao` against the current definitions, re-stamps
every value and rebuilds the title/badge/search projections without touching
lifecycle, moderation status or `updated_at`.
