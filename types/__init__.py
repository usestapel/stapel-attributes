"""Built-in feature type implementations.

All ten generic feature types are registered automatically when this module
is imported (the registry imports it lazily on first access). ``size_grid``
(clothing/shoe size tables) remains a marketplace-vertical type, NOT shipped
here — it is registered by vertical packages via
``STAPEL_ATTRIBUTES["EXTRA_TYPES"]`` or ``register_feature_type`` (see
MODULE.md for the worked example). ``convertible_unit`` (values with
convertible units — length/weight/area/volume/temperature) used to be
vertical-only alongside it; it is generic enough to ship as a built-in and
moved here.
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
from stapel_attributes.types.convertible_unit import ConvertibleUnitFeatureType

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
    'ConvertibleUnitFeatureType',
]
