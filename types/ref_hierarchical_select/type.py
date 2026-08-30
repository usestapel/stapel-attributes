"""Ref Hierarchical Select Feature Type - Type Handler."""

from typing import Any, Dict, List

from stapel_attributes.base import BaseFeatureType, FeatureDef
from stapel_attributes.exceptions import FeatureValidationError
from stapel_attributes.registry import register_feature_type
from stapel_attributes.results import ValidationErrorCode
from stapel_attributes.types.ref_hierarchical_select.config import (
    RefHierarchicalSelectConfig,
    RefHierarchicalSelectConfigSerializer,
)
from stapel_attributes.types.ref_hierarchical_select.dao import (
    RefHierarchicalSelectDao,
    RefHierarchicalSelectDaoSerializer,
)
from stapel_attributes.types.ref_hierarchical_select.dto import (
    RefHierarchicalSelectDto,
    RefHierarchicalSelectDtoSerializer,
)
from stapel_attributes.types.refs import describe_or_fail, require_resolver, resolve_labels
from stapel_attributes.vocabularies import get_vocabulary_resolver


@register_feature_type
class RefHierarchicalSelectFeatureType(
    BaseFeatureType[RefHierarchicalSelectConfig, RefHierarchicalSelectDto, RefHierarchicalSelectDao]
):
    """
    Cascading select down a chain of vocabulary levels.

    Config:
        - type: "ref_hierarchical_select" (required)
        - vocabulary: vocabulary slug (required)
        - levels: root-to-leaf level chain (required); each level after the
          first must have the previous one as its vocabulary ``parent``
        - minDepth: shortest accepted path (default: 1)
        - maxDepth: longest accepted path (None = the full chain)

    DTO/DAO value: the term codes along ``levels``, root first. The DAO also
    snapshots ``labels`` so a stored path renders without the vocabulary.
    """

    slug = 'ref_hierarchical_select'
    name = 'Reference Hierarchical Select'

    config_class = RefHierarchicalSelectConfig
    dto_class = RefHierarchicalSelectDto
    dao_class = RefHierarchicalSelectDao

    config_serializer_class = RefHierarchicalSelectConfigSerializer
    dto_serializer_class = RefHierarchicalSelectDtoSerializer
    dao_serializer_class = RefHierarchicalSelectDaoSerializer

    def validate_config(self, config: RefHierarchicalSelectConfig) -> None:
        """Validate the level chain against the live vocabulary."""
        resolver = require_resolver(self.slug)

        if not config.vocabulary:
            raise FeatureValidationError(
                "'vocabulary' is required for ref_hierarchical_select",
                code=ValidationErrorCode.INVALID_CONFIG,
            )
        if not config.levels:
            raise FeatureValidationError(
                "'levels' cannot be empty",
                code=ValidationErrorCode.INVALID_CONFIG,
            )

        info = describe_or_fail(resolver, config.vocabulary)
        previous = None
        for name in config.levels:
            level = info.level(name)
            if level is None:
                raise FeatureValidationError(
                    f"unknown level '{name}' in vocabulary '{config.vocabulary}'",
                    code=ValidationErrorCode.INVALID_CONFIG,
                    ref_value=[lvl.name for lvl in info.levels],
                )
            if previous is not None and level.parent != previous:
                raise FeatureValidationError(
                    f"level '{name}' does not descend from '{previous}' — "
                    "'levels' must be a parent chain",
                    code=ValidationErrorCode.INVALID_CONFIG,
                    ref_value=list(config.levels),
                )
            previous = name

        if config.minDepth < 1:
            raise FeatureValidationError(
                "'minDepth' must be at least 1",
                code=ValidationErrorCode.INVALID_CONFIG,
            )
        if config.minDepth > len(config.levels):
            raise FeatureValidationError(
                "'minDepth' cannot exceed the number of levels",
                code=ValidationErrorCode.INVALID_CONFIG,
                ref_value=len(config.levels),
            )
        if config.maxDepth is not None:
            if config.maxDepth < config.minDepth:
                raise FeatureValidationError(
                    "'maxDepth' cannot be less than 'minDepth'",
                    code=ValidationErrorCode.MIN_GREATER_THAN_MAX,
                )
            if config.maxDepth > len(config.levels):
                raise FeatureValidationError(
                    "'maxDepth' cannot exceed the number of levels",
                    code=ValidationErrorCode.INVALID_CONFIG,
                    ref_value=len(config.levels),
                )

    def validate_dto(
        self,
        config: RefHierarchicalSelectConfig,
        dto: RefHierarchicalSelectDto,
    ) -> None:
        """Validate the code path: depth, existence, and the parent chain."""
        path = dto.value

        if not isinstance(path, list):
            raise FeatureValidationError(
                "'value' must be an array of term codes",
                code=ValidationErrorCode.INVALID_TYPE,
            )
        if not all(isinstance(code, str) for code in path):
            raise FeatureValidationError(
                "All term codes must be strings",
                code=ValidationErrorCode.INVALID_TYPE,
            )
        if not path:
            if config.minDepth > 0:
                raise FeatureValidationError(
                    f"Selection must have at least {config.minDepth} level(s)",
                    code=ValidationErrorCode.BELOW_MINIMUM,
                    ref_value=config.minDepth,
                )
            return

        if len(path) < config.minDepth:
            raise FeatureValidationError(
                f"Selection must have at least {config.minDepth} level(s)",
                code=ValidationErrorCode.BELOW_MINIMUM,
                ref_value=config.minDepth,
            )
        max_depth = config.maxDepth if config.maxDepth is not None else len(config.levels)
        if len(path) > max_depth:
            raise FeatureValidationError(
                f"Selection cannot exceed {max_depth} level(s)",
                code=ValidationErrorCode.ABOVE_MAXIMUM,
                ref_value=max_depth,
            )

        resolver = get_vocabulary_resolver()
        if resolver is None or not config.vocabulary:
            return

        for depth, code in enumerate(path):
            level = config.levels[depth]
            if not resolver.exists(config.vocabulary, level, code):
                raise FeatureValidationError(
                    f"Unknown term '{code}' in {config.vocabulary}/{level}",
                    code=ValidationErrorCode.NOT_IN_OPTIONS,
                    ref_value=code,
                )
            if depth and not resolver.is_child(
                config.vocabulary, level, code, config.levels[depth - 1], path[depth - 1]
            ):
                raise FeatureValidationError(
                    f"Term '{code}' is not a child of '{path[depth - 1]}' "
                    f"({config.vocabulary}/{config.levels[depth - 1]})",
                    code=ValidationErrorCode.NOT_IN_OPTIONS,
                    ref_value=path[depth - 1],
                )

    def dto_to_dao(
        self,
        config: RefHierarchicalSelectConfig,
        dto: RefHierarchicalSelectDto,
        feature: FeatureDef,
    ) -> RefHierarchicalSelectDao:
        """Convert to DAO, snapshotting one label per level of the path."""
        resolver = get_vocabulary_resolver()
        path = [str(code) for code in dto.value]
        labels: List[str] = []
        for depth, code in enumerate(path):
            level = config.levels[depth] if depth < len(config.levels) else None
            labels.extend(resolve_labels(resolver, config.vocabulary, level, [code]))

        return RefHierarchicalSelectDao(
            type=self.slug,
            value=path,
            labels=labels,
            vocabulary=config.vocabulary,
            levels=list(config.levels),
            name=feature.name,
            title=feature.show_at_title,
            badge=feature.show_as_badge,
            translate=feature.translate if feature.translate != 'all' else None,
        )

    def normalize_dto(
        self,
        config: RefHierarchicalSelectConfig,
        dto_data: Dict[str, Any],
    ) -> RefHierarchicalSelectDto:
        """Normalize a raw DTO into a list of string codes."""
        value = dto_data.get('value')
        if not isinstance(value, list):
            value = [] if value is None else [value]
        return RefHierarchicalSelectDto(
            type=self.slug,
            value=[str(code) for code in value if code not in (None, '')],
        )

    def get_default_config(self) -> Dict[str, Any]:
        """Return the default configuration."""
        return {
            'type': self.slug,
            'vocabulary': '',
            'levels': [],
            'minDepth': 1,
            'maxDepth': None,
        }

    def get_default_value(self, config: RefHierarchicalSelectConfig) -> List[str]:
        """A vocabulary-backed cascade has no config-level default."""
        return []

    def format_value(
        self,
        config: RefHierarchicalSelectConfig,
        dao: RefHierarchicalSelectDao,
    ) -> str:
        """Format the stored path from the DAO labels (no resolver needed)."""
        codes = getattr(dao, 'value', None) or []
        labels = getattr(dao, 'labels', None) or []
        return ' / '.join(labels if len(labels) == len(codes) else codes)

    def get_translation_keys(self, config: RefHierarchicalSelectConfig) -> List[str]:
        """None: term labels are owned by the vocabulary, not by this schema."""
        return []
