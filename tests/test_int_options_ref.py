"""``int`` with a vocabulary-backed allowed set (``optionsRef``).

The mechanism the car composer needs: «год выпуска» is an integer whose
allowed values depend on the chosen modification — 72 174 modifications each
carry their own year range, which cannot ride the rules grammar (a ``limit``
rule per modification would put the whole catalogue into every schema
payload). So the allowed set lives where the modification chain already
lives — the vocabulary — and ``IntConfig`` gains the same ``optionsRef``
pointer the ref-types carry: the value must be a term of ``level``, and with
``parentFeature`` filled, a child of the selected parent term.

The value stays an ``int`` end to end (DTO, DAO, facets, sorting); only the
membership check reads the vocabulary, through the same resolver protocol as
``ref_select`` — one constraint source for both sides of the wire.
"""

import pytest

from stapel_attributes.base import FeatureDef, ValidationContext
from stapel_attributes.exceptions import FeatureValidationError
from stapel_attributes.registry import get_feature_type, parse_config
from stapel_attributes.results import ValidationErrorCode
from stapel_attributes.validation import validate_dto, validate_dto_structured
from stapel_attributes.vocabularies import (
    VocabularyInfo,
    VocabularyLevel,
    register_vocabulary_resolver,
)

try:
    from django.core.exceptions import ValidationError
except ImportError:  # pragma: no cover
    from rest_framework.exceptions import ValidationError


VOCABULARY = 'autocatalog'

LEVELS = (
    VocabularyLevel(name='Modification'),
    VocabularyLevel(name='Year', parent='Modification'),
)

TERMS = {
    'Modification': {'20-mt-150': '2.0 MT (150 л.с.)', '16-at-110': '1.6 AT (110 л.с.)'},
    # Both ranges live in the level; only the edges say which years belong
    # to which modification.
    'Year': {str(year): str(year) for year in (2008, 2009, 2010, 2011, 2012, 2013, 2014)},
}

#: 2.0 MT is built 2008–2012; 1.6 AT is built 2013–2014.
EDGES = frozenset(
    [('Modification', '20-mt-150', 'Year', str(year)) for year in range(2008, 2013)]
    + [('Modification', '16-at-110', 'Year', str(year)) for year in (2013, 2014)]
)


class CarVocabularyResolver:
    """Modification -> Year, the exact shape the importer emits."""

    def describe(self, vocabulary):
        if vocabulary != VOCABULARY:
            return None
        return VocabularyInfo(slug=VOCABULARY, levels=LEVELS)

    def exists(self, vocabulary, level, code):
        return vocabulary == VOCABULARY and code in TERMS.get(level, {})

    def is_child(self, vocabulary, level, code, parent_level, parent_code):
        if vocabulary != VOCABULARY:
            return False
        return (parent_level, parent_code, level, code) in EDGES

    def labels(self, vocabulary, level, codes):
        known = TERMS.get(level, {})
        return {code: known[code] for code in codes if code in known}


YEAR_CONFIG = {
    'type': 'int',
    'min': 1905,
    'max': 2027,
    'optionsRef': {
        'vocabulary': VOCABULARY,
        'level': 'Year',
        'parentFeature': 'modification',
    },
}

MODIFICATION = FeatureDef(
    slug='modification',
    name='Модификация',
    config={
        'type': 'ref_select',
        'optionsRef': {'vocabulary': VOCABULARY, 'level': 'Modification'},
    },
)
YEAR = FeatureDef(slug='year', name='Год выпуска', config=YEAR_CONFIG)


@pytest.fixture(autouse=True)
def resolver():
    fake = CarVocabularyResolver()
    register_vocabulary_resolver(fake)
    yield fake
    register_vocabulary_resolver(None)


def _int_type():
    return get_feature_type('int')


def _config(raw=YEAR_CONFIG):
    return parse_config(raw)


def _dto(value):
    return _int_type().normalize_dto(_config(), {'type': 'int', 'value': value})


# --------------------------------------------------------------------- config

def test_config_with_options_ref_parses_and_keeps_the_pointer():
    config = _config()
    assert config.optionsRef is not None
    ref = config.optionsRef
    get = ref.get if isinstance(ref, dict) else lambda key: getattr(ref, key)
    assert get('vocabulary') == VOCABULARY
    assert get('level') == 'Year'
    assert get('parentFeature') == 'modification'


def test_config_without_options_ref_is_untouched():
    config = parse_config({'type': 'int', 'min': 0, 'max': 10})
    _int_type().validate_config(config)  # no resolver needed, no error


def test_unknown_vocabulary_is_an_invalid_config():
    config = parse_config({
        'type': 'int',
        'optionsRef': {'vocabulary': 'nope', 'level': 'Year'},
    })
    with pytest.raises(FeatureValidationError) as caught:
        _int_type().validate_config(config)
    assert caught.value.error_code is ValidationErrorCode.INVALID_CONFIG


def test_unknown_level_is_an_invalid_config():
    config = parse_config({
        'type': 'int',
        'optionsRef': {'vocabulary': VOCABULARY, 'level': 'Nope'},
    })
    with pytest.raises(FeatureValidationError) as caught:
        _int_type().validate_config(config)
    assert caught.value.error_code is ValidationErrorCode.INVALID_CONFIG


def test_options_ref_without_resolver_is_an_invalid_config():
    register_vocabulary_resolver(None)
    with pytest.raises(FeatureValidationError) as caught:
        _int_type().validate_config(_config())
    assert caught.value.error_code is ValidationErrorCode.INVALID_CONFIG


# ------------------------------------------------------- membership, no parent

def test_a_year_in_the_level_is_accepted_without_parent_context():
    _int_type().validate_dto(_config(), _dto(2010))


def test_a_year_outside_the_level_is_refused_even_without_parent():
    with pytest.raises(FeatureValidationError) as caught:
        _int_type().validate_dto(_config(), _dto(1999))
    assert caught.value.error_code is ValidationErrorCode.NOT_IN_OPTIONS


def test_static_bounds_still_apply_alongside_the_ref():
    with pytest.raises(FeatureValidationError) as caught:
        _int_type().validate_dto(_config(), _dto(1899))
    assert caught.value.error_code is ValidationErrorCode.BELOW_MINIMUM


# ------------------------------------------------------ parent-narrowed check

def _context(values):
    return ValidationContext(values=values, feature_defs=[MODIFICATION, YEAR])


def test_a_year_of_the_chosen_modification_is_accepted():
    _int_type().validate_dto_in_context(
        _config(), _dto(2010), _context({'modification': ['20-mt-150'], 'year': 2010})
    )


def test_a_year_of_another_modification_is_refused():
    # 2013 exists in the level (1.6 AT is built then) but is not a child of
    # the chosen 2.0 MT — the exact case the prose used to describe.
    with pytest.raises(FeatureValidationError) as caught:
        _int_type().validate_dto_in_context(
            _config(), _dto(2013), _context({'modification': ['20-mt-150'], 'year': 2013})
        )
    assert caught.value.error_code is ValidationErrorCode.NOT_IN_OPTIONS


def test_empty_parent_is_the_soft_path():
    # Same contract as ref_select: with no parent chosen the whole level is
    # allowed, so a form validates top-down without forcing an order.
    _int_type().validate_dto_in_context(
        _config(), _dto(2013), _context({'year': 2013})
    )


# ---------------------------------------------------------- the full pipeline

def _configs():
    return [MODIFICATION, YEAR]


def test_validate_names_the_year_field_on_an_out_of_range_submission():
    with pytest.raises(ValidationError) as caught:
        validate_dto(_configs(), {'modification': ['20-mt-150'], 'year': 2013})
    rendered = str(caught.value)
    assert 'year' in rendered
    assert 'modification' not in rendered.replace("'20-mt-150'", '')


def test_validate_structured_reports_not_in_options_for_the_year():
    result = validate_dto_structured(_configs(), {'modification': ['20-mt-150'], 'year': 2013})
    assert not result.valid
    codes = {one.slug: one.error for one in result.results if one.error is not None}
    assert codes.get('year') == ValidationErrorCode.NOT_IN_OPTIONS


def test_validate_accepts_a_year_the_modification_allows():
    validate_dto(_configs(), {'modification': ['20-mt-150'], 'year': 2010})
