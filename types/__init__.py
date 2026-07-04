"""Built-in feature type implementations.

All nine generic feature types are registered automatically when this module
is imported (the registry imports it lazily on first access). Marketplace-
specific types (e.g. size grids, convertible units) are NOT shipped here —
they are registered by vertical packages via ``STAPEL_ATTRIBUTES["EXTRA_TYPES"]``
or ``register_feature_type`` (see MODULE.md for the worked example).
"""

# Import all feature types to trigger registration
from stapel_attributes.types.int import IntFeatureType
from stapel_attributes.types.float import FloatFeatureType
from stapel_attributes.types.string import StringFeatureType
from stapel_attributes.types.bool import BoolFeatureType
from stapel_attributes.types.hex_color import HexColorFeatureType
from stapel_attributes.types.select import SelectFeatureType
from stapel_attributes.types.date import DateFeatureType
from stapel_attributes.types.header import HeaderFeatureType
from stapel_attributes.types.hierarchical_select import HierarchicalSelectFeatureType

__all__ = [
    'IntFeatureType',
    'FloatFeatureType',
    'StringFeatureType',
    'BoolFeatureType',
    'HexColorFeatureType',
    'SelectFeatureType',
    'DateFeatureType',
    'HeaderFeatureType',
    'HierarchicalSelectFeatureType',
]
