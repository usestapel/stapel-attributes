"""Ref Select Feature Type - Type Handler."""

from typing import Any, Dict, List, Optional

from stapel_attributes.base import BaseFeatureType, FeatureDef, ValidationContext
from stapel_attributes.exceptions import FeatureValidationError
from stapel_attributes.registry import register_feature_type
from stapel_attributes.results import ValidationErrorCode
from stapel_attributes.rules import stringify
from stapel_attributes.types.ref_select.config import RefSelectConfig, RefSelectConfigSerializer
from stapel_attributes.types.ref_select.dao import RefSelectDao, RefSelectDaoSerializer
from stapel_attributes.types.ref_select.dto import RefSelectDto, RefSelectDtoSerializer
from stapel_attributes.types.refs import (
    describe_or_fail,
    ref_field,
    require_resolver,
    resolve_labels,
)
from stapel_attributes.vocabularies import get_vocabulary_resolver

UI_STYLES = ['dropdown', 'chips']


@register_feature_type
class RefSelectFeatureType(BaseFeatureType[RefSelectConfig, RefSelectDto, RefSelectDao]):
    """
    Select over one level of an external vocabulary.

    Config:
        - type: "ref_select" (required)
        - optionsRef: {vocabulary, level, parentFeature?} (required)
        - minSelected: minimum selections (default: 0)
        - maxSelected: maximum selections (default: 1; null = unlimited)
        - uiStyle: 'dropdown' or 'chips' (default: 'dropdown')

    DTO value: list of term codes.
    DAO value: codes + a ``labels`` snapshot + the vocabulary/level they came
    from, so display never re-reads the vocabulary and facets keep working on
    the codes exactly as for ``select``.

    Options are never inlined into the config — the vocabularies this exists
    for have thousands of terms per level.
    """

    slug = 'ref_select'
    name = 'Reference Select'

    config_class = RefSelectConfig
    dto_class = RefSelectDto
    dao_class = RefSelectDao

    config_serializer_class = RefSelectConfigSerializer
    dto_serializer_class = RefSelectDtoSerializer
    dao_serializer_class = RefSelectDaoSerializer

    def validate_config(self, config: RefSelectConfig) -> None:
        """Validate the ref_select configuration against the live vocabulary."""
        resolver = require_resolver(self.slug)

        vocabulary = ref_field(config.optionsRef, 'vocabulary')
        level = ref_field(config.optionsRef, 'level')
        if not vocabulary or not level:
            raise FeatureValidationError(
                "'optionsRef' must carry a 'vocabulary' and a 'level'",
                code=ValidationErrorCode.INVALID_CONFIG,
            )

        info = describe_or_fail(resolver, vocabulary)
        if info.level(level) is None:
            raise FeatureValidationError(
                f"unknown level '{level}' in vocabulary '{vocabulary}'",
                code=ValidationErrorCode.INVALID_CONFIG,
                ref_value=[lvl.name for lvl in info.levels],
            )

        if config.uiStyle not in UI_STYLES:
            raise FeatureValidationError(
                f"'uiStyle' must be one of: {', '.join(UI_STYLES)}",
                code=ValidationErrorCode.INVALID_CONFIG,
                ref_value=list(UI_STYLES),
            )

        if config.minSelected < 0:
            raise FeatureValidationError(
                "'minSelected' must be a non-negative integer",
                code=ValidationErrorCode.INVALID_CONFIG,
            )

        if config.maxSelected is not None:
            if config.maxSelected < 1:
                raise FeatureValidationError(
                    "'maxSelected' must be a positive integer",
                    code=ValidationErrorCode.INVALID_CONFIG,
                )
            if config.minSelected > config.maxSelected:
                raise FeatureValidationError(
                    "'minSelected' cannot be greater than 'maxSelected'",
                    code=ValidationErrorCode.MIN_GREATER_THAN_MAX,
                )

    def validate_dto(self, config: RefSelectConfig, dto: RefSelectDto) -> None:
        """Validate shape, cardinality and term existence (no parent context)."""
        value = dto.value

        if not isinstance(value, list):
            raise FeatureValidationError(
                "Value must be a list of term codes",
                code=ValidationErrorCode.INVALID_TYPE,
            )
        if not all(isinstance(item, str) for item in value):
            raise FeatureValidationError(
                "All term codes must be strings",
                code=ValidationErrorCode.INVALID_TYPE,
            )
        if len(value) < config.minSelected:
            raise FeatureValidationError(
                f"Select at least {config.minSelected} options",
                code=ValidationErrorCode.BELOW_MINIMUM,
                ref_value=config.minSelected,
            )
        if config.maxSelected is not None and len(value) > config.maxSelected:
            raise FeatureValidationError(
                f"Select at most {config.maxSelected} options",
                code=ValidationErrorCode.ABOVE_MAXIMUM,
                ref_value=config.maxSelected,
            )
        if len(value) != len(set(value)):
            raise FeatureValidationError(
                "Duplicate selections are not allowed",
                code=ValidationErrorCode.INVALID_FORMAT,
            )

        vocabulary = ref_field(config.optionsRef, 'vocabulary')
        level = ref_field(config.optionsRef, 'level')
        resolver = get_vocabulary_resolver()
        if resolver is None or not vocabulary or not level:
            return
        for code in value:
            if not resolver.exists(vocabulary, level, code):
                raise FeatureValidationError(
                    f"Unknown term '{code}' in {vocabulary}/{level}",
                    code=ValidationErrorCode.NOT_IN_OPTIONS,
                    ref_value=code,
                )

    def validate_dto_in_context(
        self,
        config: RefSelectConfig,
        dto: RefSelectDto,
        context: ValidationContext,
    ) -> None:
        """Existence checks, narrowed by the parent feature's selection.

        With ``parentFeature`` filled, every code must be a child of the FIRST
        parent code (a parent select is single-valued in practice, and picking
        the first keeps the check deterministic). With the parent empty the
        whole level is allowed — a soft path on purpose, so a form validates
        top-down without forcing an order on the user.
        """
        self.validate_dto(config, dto)

        parent_feature = ref_field(config.optionsRef, 'parentFeature')
        if not parent_feature or not dto.value:
            return

        parent_codes = stringify(context.values.get(parent_feature))
        if not parent_codes:
            return

        resolver = get_vocabulary_resolver()
        vocabulary = ref_field(config.optionsRef, 'vocabulary')
        level = ref_field(config.optionsRef, 'level')
        if resolver is None or not vocabulary or not level:
            return

        parent_level = self._parent_level(resolver, vocabulary, level)
        if parent_level is None:
            return

        parent_code = parent_codes[0]
        for code in dto.value:
            if not resolver.is_child(vocabulary, level, code, parent_level, parent_code):
                raise FeatureValidationError(
                    f"Term '{code}' is not a child of '{parent_code}' "
                    f"({vocabulary}/{parent_level})",
                    code=ValidationErrorCode.NOT_IN_OPTIONS,
                    ref_value=parent_code,
                )

    @staticmethod
    def _parent_level(resolver: Any, vocabulary: str, level: str) -> Optional[str]:
        info = resolver.describe(vocabulary)
        if info is None:
            return None
        found = info.level(level)
        return found.parent if found else None

    def dto_to_dao(
        self,
        config: RefSelectConfig,
        dto: RefSelectDto,
        feature: FeatureDef,
    ) -> RefSelectDao:
        """Convert to DAO, snapshotting the labels for the stored codes."""
        seen = set()
        codes: List[str] = []
        for item in dto.value:
            code = str(item)
            if code not in seen:
                seen.add(code)
                codes.append(code)

        vocabulary = ref_field(config.optionsRef, 'vocabulary')
        level = ref_field(config.optionsRef, 'level')
        return RefSelectDao(
            type=self.slug,
            value=codes,
            labels=resolve_labels(get_vocabulary_resolver(), vocabulary, level, codes),
            vocabulary=vocabulary,
            level=level,
            name=feature.name,
            title=feature.show_at_title,
            badge=feature.show_as_badge,
            translate=feature.translate if feature.translate != 'all' else None,
        )

    def normalize_dto(self, config: RefSelectConfig, dto_data: Dict[str, Any]) -> RefSelectDto:
        """Normalize a raw ref_select DTO into a de-duplicated code list."""
        value = dto_data.get('value')
        if value is None:
            return RefSelectDto(type=self.slug, value=[])
        if not isinstance(value, list):
            value = [value]

        seen = set()
        codes: List[str] = []
        for item in value:
            code = str(item)
            if code not in seen:
                seen.add(code)
                codes.append(code)
        return RefSelectDto(type=self.slug, value=codes)

    def get_default_config(self) -> Dict[str, Any]:
        """Return the default configuration."""
        return {
            'type': self.slug,
            'optionsRef': {'vocabulary': '', 'level': ''},
            'minSelected': 0,
            'maxSelected': 1,
            'uiStyle': 'dropdown',
        }

    def get_default_value(self, config: RefSelectConfig) -> List[str]:
        """A vocabulary-backed select has no config-level default."""
        return []

    def format_value(self, config: RefSelectConfig, dao: RefSelectDao) -> str:
        """Format the stored value from the DAO labels (no resolver needed)."""
        codes = getattr(dao, 'value', None) or []
        labels = getattr(dao, 'labels', None) or []
        return ', '.join(labels if len(labels) == len(codes) else codes)

    def get_translation_keys(self, config: RefSelectConfig) -> List[str]:
        """None: term labels are owned by the vocabulary, not by this schema."""
        return []
