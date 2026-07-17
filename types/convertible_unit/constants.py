"""Convertible Unit Feature Type - shipped unit-family presets.

Each family is ``{'base_unit': <code>, 'units': {<code>: <factor>, ...}}``:
``factor`` converts *to* the base unit (``base = value * factor``), so the
base unit itself always carries ``1.0``. ``temperature`` is the one affine
(non-multiplicative) family — its ``units`` factors are unused for ``c``/``f``
conversion (kept at ``1.0`` only so the codes resolve as valid/known units);
:func:`convert_to_base` / :func:`convert_from_base` special-case it.

Ported from the legacy marketplace catalog's
``categories/feature_types/types/convertible_unit/constants.py``
(``UNIT_DEFINITIONS``/``UNIT_SYSTEMS``), reshaped from
``{unit_type: {unit: (factor, key_suffix)}}`` tuples into the
``base_unit`` + ``units{name: factor}`` shape (the translation-key suffix was
always equal to the unit code, so it is derived as ``feature.unit.<code>``
instead of carried separately).
"""

from typing import Dict, List

#: family slug -> {'base_unit': str, 'units': {unit_code: factor_to_base}}
UNIT_FAMILIES: Dict[str, Dict] = {
    'length': {
        'base_unit': 'm',
        'units': {
            'mm': 0.001, 'cm': 0.01, 'm': 1.0, 'km': 1000.0,
            'in': 0.0254, 'ft': 0.3048, 'yd': 0.9144, 'mi': 1609.344,
        },
    },
    'weight': {
        'base_unit': 'kg',
        'units': {
            'mg': 0.000001, 'g': 0.001, 'kg': 1.0, 't': 1000.0,
            'oz': 0.0283495, 'lb': 0.453592,
        },
    },
    'area': {
        'base_unit': 'm2',
        'units': {
            'mm2': 0.000001, 'cm2': 0.0001, 'm2': 1.0, 'km2': 1000000.0, 'ha': 10000.0,
            'in2': 0.00064516, 'ft2': 0.092903, 'yd2': 0.836127, 'ac': 4046.86, 'mi2': 2589988.0,
        },
    },
    'volume': {
        'base_unit': 'l',
        'units': {
            'ml': 0.001, 'l': 1.0, 'm3': 1000.0,
            'fl_oz': 0.0295735, 'cup': 0.236588, 'pt': 0.473176, 'qt': 0.946353, 'gal': 3.78541,
        },
    },
    'temperature': {
        # Affine, not multiplicative — 'base_unit'/'units' shape kept for a
        # uniform contract; see convert_to_base/convert_from_base.
        'base_unit': 'c',
        'units': {'c': 1.0, 'f': 1.0, 'k': 1.0},
    },
}

#: family slug -> {'metric': [unit_code, ...], 'imperial': [unit_code, ...]}
#: The subset of UNIT_FAMILIES[family]['units'] offered per measurement
#: system — drives ``unit_m``/``unit_i`` config validation.
UNIT_SYSTEMS: Dict[str, Dict[str, List[str]]] = {
    'metric': {
        'length': ['mm', 'cm', 'm', 'km'],
        'weight': ['mg', 'g', 'kg', 't'],
        'area': ['mm2', 'cm2', 'm2', 'km2', 'ha'],
        'volume': ['ml', 'l', 'm3'],
        'temperature': ['c', 'k'],
    },
    'imperial': {
        'length': ['in', 'ft', 'yd', 'mi'],
        'weight': ['oz', 'lb'],
        'area': ['in2', 'ft2', 'yd2', 'ac', 'mi2'],
        'volume': ['fl_oz', 'cup', 'pt', 'qt', 'gal'],
        'temperature': ['f'],
    },
}

#: family slug -> static translation key for its human-readable name.
UNIT_TYPE_KEYS: Dict[str, str] = {
    'length': 'feature.unit_type.length.name',
    'weight': 'feature.unit_type.weight.name',
    'area': 'feature.unit_type.area.name',
    'volume': 'feature.unit_type.volume.name',
    'temperature': 'feature.unit_type.temperature.name',
}


def units_for_system(unit_type: str, system: str) -> List[str]:
    """Unit codes offered for *unit_type* under *system* ('metric'/'imperial')."""
    return UNIT_SYSTEMS.get(system, {}).get(unit_type, [])


def convert_to_base(value: float, unit: str, unit_type: str) -> float:
    """Convert *value* expressed in *unit* to the family's canonical base unit.

    This is the single conversion point the type handler uses to normalize
    user input for storage — DAO ``value`` is always in the base unit.
    """
    if unit_type == 'temperature':
        return _celsius_from(value, unit)
    factor = UNIT_FAMILIES[unit_type]['units'][unit]
    return value * factor


def convert_from_base(base_value: float, unit: str, unit_type: str) -> float:
    """Convert a canonical base-unit value to *unit* (for display, or for
    translating a UI range-filter bound into the base unit the DAO is stored
    in — the same conversion, run in reverse).
    """
    if unit_type == 'temperature':
        return _celsius_to(base_value, unit)
    factor = UNIT_FAMILIES[unit_type]['units'][unit]
    return base_value / factor


def _celsius_from(value: float, unit: str) -> float:
    if unit == 'f':
        return (value - 32) * 5 / 9
    if unit == 'k':
        return value - 273.15
    return value


def _celsius_to(celsius: float, unit: str) -> float:
    if unit == 'f':
        return celsius * 9 / 5 + 32
    if unit == 'k':
        return celsius + 273.15
    return celsius


__all__ = [
    'UNIT_FAMILIES',
    'UNIT_SYSTEMS',
    'UNIT_TYPE_KEYS',
    'units_for_system',
    'convert_to_base',
    'convert_from_base',
]
