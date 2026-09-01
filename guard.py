"""A source-level gate against the next projection path that leaks.

Behavioural tests prove that *today's* payloads are clean. They say nothing
about the payload somebody adds next quarter. The failure this module exists to
prevent is not "the redaction is wrong" — it is "a new endpoint read the raw
column and nobody noticed", which is precisely how the VIN got out in the first
place: `features` was a plain ``JSONField`` and every new serializer that listed
it inherited the leak for free.

So the rule is structural, and it is about *reach*, not about correctness:

    Outside a short, named list of files, the raw value-bearing columns are not
    mentioned at all. Everything else goes through the redacting chokepoint.

:func:`assert_raw_access_confined` reads the package's own source and fails with
the offending file and line. It is deliberately a grep and not an import graph:
a grep cannot be defeated by indirection, it costs nothing, and its false
positives (a mention in a docstring, a migration) are cheap to allowlist and
loud when they appear. A reviewer adding a file to ``allow`` has to write down
why, in the test, where the next reviewer will read it.

Usage, in a consumer's test suite::

    from stapel_attributes.guard import assert_raw_access_confined

    def test_only_the_projection_touches_raw_feature_columns():
        assert_raw_access_confined(
            root=Path(stapel_listings.__file__).parent,
            names=("features", "features_draft"),
            allow=("services/features.py", "serializers.py", "models.py"),
        )
"""

import re
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

#: Never scanned: generated code, build leftovers, caches, and the tests
#: themselves (a test that asserts on a leaked payload is doing its job).
DEFAULT_SKIP_DIRS = (
    '__pycache__',
    'build',
    'dist',
    'migrations',
    'node_modules',
    'tests',
    '.git',
    '.tox',
    '.venv',
)


def _iter_sources(root: Path, skip_dirs: Sequence[str]) -> Iterable[Path]:
    for path in sorted(root.rglob('*.py')):
        if any(part in skip_dirs for part in path.relative_to(root).parts[:-1]):
            continue
        yield path


def find_raw_access(
    root: Path,
    names: Sequence[str],
    allow: Sequence[str] = (),
    skip_dirs: Sequence[str] = DEFAULT_SKIP_DIRS,
    ignore: Sequence[str] = (),
) -> List[Tuple[str, int, str]]:
    """Every mention of ``names`` under ``root`` outside ``allow``.

    ``allow`` entries are POSIX-style paths relative to ``root``; an entry
    ending in ``/`` allows a whole directory.

    A "mention" is the bare identifier as a whole word — ``listing.features``,
    ``"features"``, ``features=``. Lines whose first non-space character is
    ``#`` are skipped, so a comment explaining the rule does not trip it.

    ``ignore`` is a list of regexes for spellings that merely *look* like the
    column: a value column and a comm function can honestly share a word
    (``listing.features`` the stored values, ``"categories.features"`` the
    schema that describes them). Blank the homographs rather than allowlisting
    the whole file, so the file keeps being checked for the real thing.
    """
    pattern = re.compile(r'\b(' + '|'.join(re.escape(n) for n in names) + r')\b')
    ignored = [re.compile(p) for p in ignore]
    allowed_files = {a for a in allow if not a.endswith('/')}
    allowed_dirs = tuple(a for a in allow if a.endswith('/'))
    hits: List[Tuple[str, int, str]] = []

    for path in _iter_sources(root, skip_dirs):
        rel = path.relative_to(root).as_posix()
        if rel in allowed_files or rel.startswith(allowed_dirs):
            continue
        for lineno, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
            if line.lstrip().startswith('#'):
                continue
            probe = line
            for homograph in ignored:
                probe = homograph.sub('', probe)
            if pattern.search(probe):
                hits.append((rel, lineno, line.strip()))
    return hits


def assert_raw_access_confined(
    root: Path,
    names: Sequence[str],
    allow: Sequence[str] = (),
    skip_dirs: Sequence[str] = DEFAULT_SKIP_DIRS,
    ignore: Sequence[str] = (),
) -> None:
    """Raise ``AssertionError`` naming every file that reaches past the chokepoint."""
    hits = find_raw_access(root, names, allow, skip_dirs, ignore)
    if not hits:
        return
    listed = '\n'.join(f"  {rel}:{lineno}: {line}" for rel, lineno, line in hits)
    raise AssertionError(
        f"{len(hits)} unreviewed mention(s) of the raw value column(s) "
        f"{', '.join(names)}:\n{listed}\n\n"
        "A raw feature column carries values whose FeatureDef may be "
        "visibility='owner' or 'staff' (a VIN, an IMEI, a serial number). Emit "
        "it through the redacting projection instead — or, if this path is "
        "genuinely entitled to the values, add the file to the test's `allow` "
        "list together with a comment saying which audience it serves."
    )


__all__ = ['DEFAULT_SKIP_DIRS', 'assert_raw_access_confined', 'find_raw_access']
