"""Vocabulary resolver seam — the L1 protocol the ref-types validate against.

Reference vocabularies (14 962 phone models, 107 049 car modifications) cannot
be inlined into a category's feature schema, so ``ref_select`` /
``ref_hierarchical_select`` carry an ``optionsRef`` and resolve codes through a
**resolver**. This library declares only the protocol and the registry; the
implementation lives outside it (stapel-vocabularies ships an ORM-backed one
and a comm-backed one).

Two ways in, later wins:

1. ``STAPEL_ATTRIBUTES["VOCABULARY_RESOLVER"]`` — a dotted path, resolved
   lazily through the settings ``import_strings`` seam (a class is
   instantiated once, an instance/factory result is used as-is);
2. :func:`register_vocabulary_resolver` at runtime (e.g. an ``AppConfig.ready()``
   registering the in-process ORM resolver) — this always wins over the
   setting.

Importing this module pulls in neither Django nor DRF; the setting is only
read when :func:`get_vocabulary_resolver` is actually called.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Protocol, Sequence, Tuple, runtime_checkable


@dataclass(frozen=True)
class VocabularyLevel:
    """One level of a vocabulary. ``parent`` names the level above it."""

    name: str
    parent: Optional[str] = None


@dataclass(frozen=True)
class VocabularyInfo:
    """A vocabulary's shape: its slug and its ordered level chain."""

    slug: str
    levels: Tuple[VocabularyLevel, ...] = ()

    def level(self, name: str) -> Optional[VocabularyLevel]:
        """The level called *name*, or ``None``."""
        for candidate in self.levels:
            if candidate.name == name:
                return candidate
        return None


@runtime_checkable
class VocabularyResolver(Protocol):
    """What the ref-types need from a vocabulary source.

    Deliberately four read-only questions — no listing, no search, no paging:
    those belong to the HTTP surface a form's typeahead talks to, not to the
    validation path.
    """

    def describe(self, vocabulary: str) -> Optional[VocabularyInfo]:
        """The vocabulary's shape, or ``None`` if it does not exist."""

    def exists(self, vocabulary: str, level: str, code: str) -> bool:
        """Whether ``code`` is a term of ``level`` in ``vocabulary``."""

    def is_child(
        self,
        vocabulary: str,
        level: str,
        code: str,
        parent_level: str,
        parent_code: str,
    ) -> bool:
        """Whether the term is an edge-child of the given parent term."""

    def labels(self, vocabulary: str, level: str, codes: Sequence[str]) -> Dict[str, str]:
        """Display labels for *codes*; unknown codes may be omitted."""


_resolver: Optional[VocabularyResolver] = None
#: Instance built from the configured dotted path, cached per resolved object.
_configured: Dict[int, VocabularyResolver] = {}


def register_vocabulary_resolver(resolver: Optional[VocabularyResolver]) -> None:
    """Register the process-wide vocabulary resolver (``None`` clears it).

    A runtime registration wins over
    ``STAPEL_ATTRIBUTES["VOCABULARY_RESOLVER"]``, so a service that hosts the
    vocabularies in-process can register its ORM resolver from
    ``AppConfig.ready()`` without touching settings.
    """
    global _resolver
    _resolver = resolver


def get_vocabulary_resolver() -> Optional[VocabularyResolver]:
    """The effective resolver: the runtime registration, else the configured
    dotted path, else ``None`` (ref-type configs then fail loudly)."""
    if _resolver is not None:
        return _resolver
    try:
        from django.core.exceptions import ImproperlyConfigured
    except ImportError:  # pragma: no cover - Django is a hard dependency
        return None
    try:
        from stapel_attributes.conf import attributes_settings

        configured = attributes_settings.VOCABULARY_RESOLVER
    except ImproperlyConfigured:
        return None
    if configured is None:
        return None
    if not isinstance(configured, type):
        return configured
    instance = _configured.get(id(configured))
    if instance is None:
        instance = _configured[id(configured)] = configured()
    return instance


__all__ = [
    'VocabularyInfo',
    'VocabularyLevel',
    'VocabularyResolver',
    'get_vocabulary_resolver',
    'register_vocabulary_resolver',
]
