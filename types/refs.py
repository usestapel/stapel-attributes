"""Shared support for the vocabulary-backed types (``ref_*``).

Not a feature type of its own: the two ref-types only need the same three
answers — reach the resolver loudly, read the ``optionsRef`` whether it came
back as a dataclass or a dict, and turn codes into labels.
"""

from typing import Any, Dict, List, Optional, Sequence

from stapel_attributes.exceptions import FeatureValidationError
from stapel_attributes.results import ValidationErrorCode
from stapel_attributes.vocabularies import VocabularyInfo, VocabularyResolver, get_vocabulary_resolver


def require_resolver(type_slug: str) -> VocabularyResolver:
    """The registered resolver, or a loud ``INVALID_CONFIG``.

    Raised at *config* validation — the moment a feature is saved — rather
    than when a value is submitted: a schema pointing at a vocabulary nobody
    can resolve is broken at authoring time, and discovering that on the first
    listing submission would be a much later, much stranger failure.
    """
    resolver = get_vocabulary_resolver()
    if resolver is None:
        raise FeatureValidationError(
            f"no vocabulary resolver registered — '{type_slug}' needs "
            "STAPEL_ATTRIBUTES['VOCABULARY_RESOLVER'] or "
            "register_vocabulary_resolver()",
            code=ValidationErrorCode.INVALID_CONFIG,
        )
    return resolver


def describe_or_fail(resolver: VocabularyResolver, vocabulary: str) -> VocabularyInfo:
    """The vocabulary's shape, or a loud ``INVALID_CONFIG``."""
    info = resolver.describe(vocabulary)
    if info is None:
        raise FeatureValidationError(
            f"unknown vocabulary: {vocabulary}",
            code=ValidationErrorCode.INVALID_CONFIG,
            ref_value=vocabulary,
        )
    return info


def ref_field(options_ref: Any, name: str) -> Optional[str]:
    """Read one field of an ``optionsRef``, dataclass or dict alike.

    ``parse_config`` hands typed configs back with nested dataclasses already
    flattened to dicts (``DictDataclassSerializer``), while a hand-built
    config carries the real dataclass — both shapes reach the type handler.
    """
    if options_ref is None:
        return None
    value = options_ref.get(name) if isinstance(options_ref, dict) else getattr(options_ref, name, None)
    return value if value else None


def resolve_labels(
    resolver: Optional[VocabularyResolver],
    vocabulary: Optional[str],
    level: Optional[str],
    codes: Sequence[str],
) -> List[str]:
    """Labels for *codes*, positionally. An unresolved code labels as itself."""
    if not codes:
        return []
    mapping: Dict[str, str] = {}
    if resolver is not None and vocabulary and level:
        mapping = resolver.labels(vocabulary, level, list(codes)) or {}
    return [mapping.get(code, code) for code in codes]


__all__ = [
    'describe_or_fail',
    'ref_field',
    'require_resolver',
    'resolve_labels',
]
