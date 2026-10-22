"""OpenAPI names for the enums this library puts into a host's schema.

Every feature config and DTO carries a one-value ``type`` discriminator
(``"select"``, ``"bool"`` …). In a schema that holds several of them,
drf-spectacular sees one property name over many choice sets and falls back
to collision names (``TypeE3eEnum``) that change whenever the set of types,
another ``type`` field or the generator changes — and a generated client's
type names change with them. :func:`enum_name_overrides` names each one after
its slug, from the registry, so every library that embeds feature types
emits the same stable names.

Usage in a contract harness::

    from drf_spectacular.settings import spectacular_settings
    from stapel_attributes.openapi import enum_name_overrides

    spectacular_settings.ENUM_NAME_OVERRIDES = {
        **enum_name_overrides(), **spectacular_settings.ENUM_NAME_OVERRIDES,
    }
"""
from __future__ import annotations

import re

from .registry import get_all_type_slugs


def type_enum_name(slug: str) -> str:
    """``"ref_hierarchical_select"`` → ``"RefHierarchicalSelectTypeEnum"``."""
    return "".join(part[:1].upper() + part[1:] for part in re.split(r"[_\W]+", slug) if part) + "TypeEnum"


def enum_name_overrides() -> dict[str, list[str]]:
    """``ENUM_NAME_OVERRIDES`` entries for every registered type discriminator."""
    return {type_enum_name(slug): [slug] for slug in get_all_type_slugs()}


__all__ = ["enum_name_overrides", "type_enum_name"]
