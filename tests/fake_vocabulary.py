"""An in-memory :class:`VocabularyResolver` for the ref-type tests.

Shape mirrors the real phone catalogue the ref-types were designed for:
``Vendor -> Model -> MemorySize``, three levels chained by ``parent``, with a
handful of terms and edges so parent-narrowing has something to reject. A
detached ``Floor`` level holds numeric codes — the shape that needs a unit
printed after the label.
"""

from typing import Dict, List, Optional, Sequence, Tuple

from stapel_attributes.vocabularies import VocabularyInfo, VocabularyLevel

VOCABULARY = 'phones'

LEVELS = (
    VocabularyLevel(name='Vendor'),
    VocabularyLevel(name='Model', parent='Vendor'),
    VocabularyLevel(name='MemorySize', parent='Model'),
    VocabularyLevel(name='Floor'),
)

TERMS: Dict[str, Dict[str, str]] = {
    'Vendor': {'apple': 'Apple', 'samsung': 'Samsung'},
    'Model': {'iphone-15': 'iPhone 15', 'iphone-14': 'iPhone 14', 'galaxy-s24': 'Galaxy S24'},
    'MemorySize': {'128-gb': '128 GB', '256-gb': '256 GB'},
    'Floor': {'3': '3', '9': '9'},
}

#: (parent_level, parent_code, child_level, child_code)
EDGES: Tuple[Tuple[str, str, str, str], ...] = (
    ('Vendor', 'apple', 'Model', 'iphone-15'),
    ('Vendor', 'apple', 'Model', 'iphone-14'),
    ('Vendor', 'samsung', 'Model', 'galaxy-s24'),
    ('Model', 'iphone-15', 'MemorySize', '128-gb'),
    ('Model', 'iphone-15', 'MemorySize', '256-gb'),
    ('Model', 'galaxy-s24', 'MemorySize', '256-gb'),
)


class FakeVocabularyResolver:
    """Reads the tables above; counts calls so a test can assert lookups."""

    def __init__(self, slug: str = VOCABULARY) -> None:
        self.slug = slug
        self.label_calls: List[Tuple[str, str, Tuple[str, ...]]] = []

    def describe(self, vocabulary: str) -> Optional[VocabularyInfo]:
        if vocabulary != self.slug:
            return None
        return VocabularyInfo(slug=self.slug, levels=LEVELS)

    def exists(self, vocabulary: str, level: str, code: str) -> bool:
        if vocabulary != self.slug:
            return False
        return code in TERMS.get(level, {})

    def is_child(
        self,
        vocabulary: str,
        level: str,
        code: str,
        parent_level: str,
        parent_code: str,
    ) -> bool:
        if vocabulary != self.slug:
            return False
        return (parent_level, parent_code, level, code) in EDGES

    def labels(self, vocabulary: str, level: str, codes: Sequence[str]) -> Dict[str, str]:
        self.label_calls.append((vocabulary, level, tuple(codes)))
        if vocabulary != self.slug:
            return {}
        known = TERMS.get(level, {})
        return {code: known[code] for code in codes if code in known}


__all__ = ['EDGES', 'LEVELS', 'TERMS', 'VOCABULARY', 'FakeVocabularyResolver']
