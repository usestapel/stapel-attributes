"""Group (composite) Feature Type - Type Handler.

One feature that holds a small table: a list of rows, each row a set of child
features of the ordinary kinds. It exists because roughly 2 % of the Avito
attribute corpus is exactly this shape — a ``DiscountLadderList`` is
"quantity from N, discount M %", repeated — and there was no way to express it
short of inventing one type per composite.

Deliberate boundaries of v1 (all enforced in :meth:`validate_config`, none of
them a convention):

- **Nesting depth 1.** A child of a group may not itself be a group.
- **No headers inside.** A header is injected by the pipeline from the schema
  and carries no value; inside a row it would have nothing to inject into.
- **No rules on children.** The rule engine (``evaluate_rules``) reads a flat
  ``{slug: value}`` payload of *top-level* features; a row's values are not in
  that namespace, so a rule written on a child could never match and a rule
  outside the group could never see a child's value. Rather than accept such a
  rule and silently never fire it, the config is rejected. Conditional
  behaviour for a composite is expressed from outside, as a rule on the group
  feature itself (``require`` / ``show`` / ``hide`` all work normally on a
  group), which is what "rules target a group's child only from outside" means
  in practice.

Everything else is delegation: each row's cells are validated by the child's
own type through the ordinary registry entry points, so a group inherits every
kind's constraints for free, and a new kind works inside a group the day it is
registered.
"""

from dataclasses import fields as dataclass_fields
from typing import Any, Dict, List, Optional, Sequence, Tuple

from stapel_attributes.base import (
    BaseFeatureType,
    FeatureDef,
    ValidationContext,
    dataclass_to_dict_no_none,
)
from stapel_attributes.exceptions import FeatureValidationError
from stapel_attributes.registry import (
    collect_translation_keys_for_feature,
    get_feature_type,
    parse_config,
    register_feature_type,
)
from stapel_attributes.results import ValidationErrorCode
from stapel_attributes.types.group.config import (
    GroupConfig,
    GroupConfigSerializer,
    GroupRepeat,
)
from stapel_attributes.types.group.dao import GroupDao, GroupDaoSerializer
from stapel_attributes.types.group.dto import GroupDto, GroupDtoSerializer

#: Types that may not appear inside a group (see the module docstring).
FORBIDDEN_CHILD_TYPES = frozenset({'group', 'header'})


def _repeat_bounds(config: GroupConfig) -> Tuple[int, Optional[int]]:
    """``(min_rows, max_rows)`` for a config; ``repeat: null`` means one row."""
    repeat = config.repeat
    if repeat is None:
        return 0, 1
    if isinstance(repeat, GroupRepeat):
        return repeat.min or 0, repeat.max
    if isinstance(repeat, dict):
        minimum = repeat.get('min') or 0
        return minimum, repeat.get('max')
    raise FeatureValidationError(
        "'repeat' must be an object with 'min'/'max', or null",
        code=ValidationErrorCode.INVALID_CONFIG,
    )


def _child_defs(config: GroupConfig) -> List[FeatureDef]:
    """Coerce the raw ``fields`` entries into FeatureDef instances.

    Raises ``INVALID_CONFIG`` for an entry that is not a feature-def shape —
    the same failure :meth:`GroupFeatureType.validate_config` reports, so a
    malformed group fails identically wherever it is first touched.
    """
    defs: List[FeatureDef] = []
    raw_fields = config.fields
    if not isinstance(raw_fields, list):
        raise FeatureValidationError(
            "'fields' must be an array of feature definitions",
            code=ValidationErrorCode.INVALID_CONFIG,
        )
    for index, entry in enumerate(raw_fields):
        if isinstance(entry, FeatureDef):
            defs.append(entry)
            continue
        if not isinstance(entry, dict):
            raise FeatureValidationError(
                f"fields[{index}] must be a feature definition object",
                code=ValidationErrorCode.INVALID_CONFIG,
            )
        try:
            defs.append(FeatureDef.from_dict(entry))
        except ValueError as exc:
            raise FeatureValidationError(
                f"fields[{index}]: {exc}",
                code=ValidationErrorCode.INVALID_CONFIG,
            )
    return defs


def _raw_cell(row: Dict[str, Any], slug: str) -> Any:
    """The value a row carries for *slug* (DTO envelope or bare value)."""
    return row.get(slug)


def _cell_value(raw: Any) -> Any:
    """Unwrap a DTO envelope down to the bare value."""
    if isinstance(raw, dict) and 'value' in raw:
        return raw.get('value')
    return raw


def _is_empty(value: Any) -> bool:
    """The pipeline's notion of an absent value (see validation.py B4)."""
    return value is None or value == '' or value == []


def _child_dto_data(raw: Any, type_slug: str) -> Dict[str, Any]:
    """Normalize a cell into the ``{type, value}`` dict a child type expects."""
    if isinstance(raw, dict) and ('value' in raw or 'type' in raw):
        return {**raw, 'type': type_slug}
    return {'type': type_slug, 'value': raw}


def _format_cell(child: Optional[FeatureDef], cell: Any) -> str:
    """Format one stored cell through the child's own ``format_value``.

    A cell is a plain dict (that is how DAOs are stored), while every type's
    ``format_value`` takes its DAO dataclass — so the dict is rehydrated first.
    A cell whose child the config no longer declares, or whose stored shape no
    longer fits the dataclass, degrades to the raw value rather than raising:
    formatting is a display path, and stored data outlives a schema edit.
    """
    raw = cell.get('value') if isinstance(cell, dict) else cell
    fallback = '' if raw is None else str(raw)
    if child is None or not isinstance(cell, dict):
        return fallback
    try:
        child_config = parse_config(child.config)
        child_type = get_feature_type(child_config.type)
        dao_fields = {f.name for f in dataclass_fields(child_type.dao_class)}
        dao = child_type.dao_class(**{k: v for k, v in cell.items() if k in dao_fields})
        return child_type.format_value(child_config, dao)
    except (FeatureValidationError, TypeError, ValueError, KeyError, AttributeError):
        return fallback


@register_feature_type
class GroupFeatureType(BaseFeatureType[GroupConfig, GroupDto, GroupDao]):
    """
    Composite feature type handler — a repeatable subform of child features.

    Config:
        - type: "group" (required)
        - fields: array of feature definitions (children), non-empty, unique
          slugs, none of them a ``group`` or a ``header``, none carrying rules
        - repeat: ``{"min": N, "max": M|null}`` for a repeatable group, or
          ``null`` for a single-row group

    DTO value: list of rows, each row ``{child_slug: value or {type, value}}``
    DAO value: list of rows, each row ``{child_slug: <child DAO with DaoMeta>}``
    """

    slug = 'group'
    name = 'Group'

    # Dataclass types
    config_class = GroupConfig
    dto_class = GroupDto
    dao_class = GroupDao

    # Serializer classes (auto-generated from dataclasses)
    config_serializer_class = GroupConfigSerializer
    dto_serializer_class = GroupDtoSerializer
    dao_serializer_class = GroupDaoSerializer

    # -- config -----------------------------------------------------------

    def validate_config(self, config: GroupConfig) -> None:
        """Validate the composite configuration and every child's own config."""
        children = _child_defs(config)
        if not children:
            raise FeatureValidationError(
                "'fields' is required for group type and cannot be empty",
                code=ValidationErrorCode.INVALID_CONFIG,
            )

        seen: set = set()
        for child in children:
            if child.slug in seen:
                raise FeatureValidationError(
                    f"Duplicate child slug '{child.slug}' in group fields",
                    code=ValidationErrorCode.DUPLICATE_SLUG,
                    ref_value=child.slug,
                )
            seen.add(child.slug)

            if child.rules:
                raise FeatureValidationError(
                    f"Child '{child.slug}' carries rules; rules on a group child are "
                    f"not supported — put the rule on the group feature itself",
                    code=ValidationErrorCode.INVALID_CONFIG,
                    ref_value=child.slug,
                )

            child_config = parse_config(child.config)
            if child_config.type in FORBIDDEN_CHILD_TYPES:
                raise FeatureValidationError(
                    f"Child '{child.slug}' has type '{child_config.type}', which cannot "
                    f"appear inside a group (nesting depth is 1)",
                    code=ValidationErrorCode.INVALID_CONFIG,
                    ref_value=child_config.type,
                )
            get_feature_type(child_config.type).validate_config(child_config)

        min_rows, max_rows = _repeat_bounds(config)
        if min_rows < 0:
            raise FeatureValidationError(
                "'repeat.min' cannot be negative",
                code=ValidationErrorCode.INVALID_CONFIG,
            )
        if max_rows is not None:
            if max_rows < 1:
                raise FeatureValidationError(
                    "'repeat.max' must be at least 1",
                    code=ValidationErrorCode.INVALID_CONFIG,
                )
            if max_rows < min_rows:
                raise FeatureValidationError(
                    "'repeat.max' cannot be less than 'repeat.min'",
                    code=ValidationErrorCode.MIN_GREATER_THAN_MAX,
                    ref_value=max_rows,
                )

    # -- value ------------------------------------------------------------

    def validate_dto(self, config: GroupConfig, dto: GroupDto) -> None:
        """Validate row count, then every cell through its own child type."""
        rows = dto.value

        if not isinstance(rows, list):
            raise FeatureValidationError(
                "'value' must be an array of rows",
                code=ValidationErrorCode.INVALID_TYPE,
            )

        if not rows:
            # An empty composite is an absent value: requiredness is the
            # pipeline's business (static mandatory or a `require` rule).
            return

        min_rows, max_rows = _repeat_bounds(config)
        if len(rows) < min_rows:
            raise FeatureValidationError(
                f"At least {min_rows} row(s) required, got {len(rows)}",
                code=ValidationErrorCode.BELOW_MINIMUM,
                ref_value=min_rows,
            )
        if max_rows is not None and len(rows) > max_rows:
            raise FeatureValidationError(
                f"At most {max_rows} row(s) allowed, got {len(rows)}",
                code=ValidationErrorCode.ABOVE_MAXIMUM,
                ref_value=max_rows,
            )

        children = _child_defs(config)
        known = {child.slug for child in children}

        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                raise FeatureValidationError(
                    f"rows[{index}] must be an object keyed by child slug",
                    code=ValidationErrorCode.INVALID_FORMAT,
                    ref_value=index,
                )
            unknown = sorted(str(key) for key in row if key not in known)
            if unknown:
                raise FeatureValidationError(
                    f"rows[{index}] has unknown field(s): {', '.join(unknown)}",
                    code=ValidationErrorCode.INVALID_FORMAT,
                    ref_value=unknown,
                )
            self._validate_row(index, row, children)

    def _validate_row(
        self,
        index: int,
        row: Dict[str, Any],
        children: Sequence[FeatureDef],
    ) -> None:
        """Validate one row: mandatory children present, each cell valid.

        The row is its own value namespace — a child whose validity depends on
        a sibling (``ref_select`` narrowing by ``parentFeature``) reads that
        sibling from the *same row*, which is the only reading that makes sense
        for a repeatable table.
        """
        context = ValidationContext(values=row, feature_defs=list(children))
        for child in children:
            raw = _raw_cell(row, child.slug)
            if _is_empty(_cell_value(raw)):
                if child.mandatory:
                    raise FeatureValidationError(
                        f"rows[{index}].{child.slug}: mandatory field '{child.name}' is required",
                        code=ValidationErrorCode.MANDATORY_MISSING,
                        params={'row': index, 'child': child.slug},
                    )
                continue

            child_config = parse_config(child.config)
            child_type = get_feature_type(child_config.type)
            data = _child_dto_data(raw, child_config.type)
            try:
                child_dto = child_type.normalize_dto(child_config, data)
                child_type.validate_dto_in_context(child_config, child_dto, context)
            except FeatureValidationError as exc:
                message = exc.messages[0] if exc.messages else str(exc)
                raise FeatureValidationError(
                    f"rows[{index}].{child.slug}: {message}",
                    code=exc.error_code,
                    ref_value=exc.ref_value,
                    params={**exc.error_params, 'row': index, 'child': child.slug},
                )
            except (TypeError, KeyError, AttributeError, ValueError, IndexError) as exc:
                raise FeatureValidationError(
                    f"rows[{index}].{child.slug}: invalid value ({exc})",
                    code=ValidationErrorCode.INVALID_TYPE,
                    params={'row': index, 'child': child.slug},
                )

    def normalize_dto(self, config: GroupConfig, dto_data: Dict[str, Any]) -> GroupDto:
        """Normalize raw DTO data: keep only object rows."""
        value = dto_data.get('value', [])
        if not isinstance(value, list):
            value = []
        return GroupDto(type='group', value=[row for row in value if isinstance(row, dict)])

    def dto_to_dao(
        self,
        config: GroupConfig,
        dto: GroupDto,
        feature: FeatureDef,
    ) -> GroupDao:
        """Convert the composite DTO to a DAO of rows of child DAOs."""
        children = _child_defs(config)
        rows: List[Dict[str, Any]] = []

        for row in dto.value or []:
            if not isinstance(row, dict):
                continue
            cells: Dict[str, Any] = {}
            for order, child in enumerate(children):
                raw = _raw_cell(row, child.slug)
                if _is_empty(_cell_value(raw)):
                    continue
                child_config = parse_config(child.config)
                child_type = get_feature_type(child_config.type)
                data = _child_dto_data(raw, child_config.type)
                child_dto = child_type.normalize_dto(child_config, data)
                child_dao = child_type.dto_to_dao(child_config, child_dto, child)
                cell = dataclass_to_dict_no_none(child_dao)
                cell['order'] = order
                cells[child.slug] = cell
            if cells:
                rows.append(cells)

        return GroupDao(
            type='group',
            value=rows,
            name=feature.name,
            title=feature.show_at_title,
            badge=feature.show_as_badge,
            translate=feature.translate if feature.translate != 'all' else None,
        )

    # -- misc -------------------------------------------------------------

    def get_default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {'type': self.slug, 'fields': [], 'repeat': None}

    def get_default_value(self, config: GroupConfig) -> List[Dict[str, Any]]:
        """A composite starts empty; a row is added by the editor."""
        return []

    def format_value(self, config: GroupConfig, dao: GroupDao) -> str:
        """Format the stored rows for display.

        ``"Quantity: 5, Discount: 10; Quantity: 10, Discount: 20"`` — cells
        within a row joined by ``", "``, rows by ``"; "``. Labels come from the
        stored child DaoMeta, so no schema lookup is needed for a cell the
        config no longer declares.
        """
        rows = dao.value if not isinstance(dao, dict) else dao.get('value')
        if not rows:
            return ''

        by_slug = {child.slug: child for child in _child_defs(config)}
        parts: List[str] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            cells: List[str] = []
            for slug, cell in row.items():
                child = by_slug.get(slug)
                label = (cell.get('name') if isinstance(cell, dict) else None) or (
                    child.name if child else slug
                )
                cells.append(f"{label}: {_format_cell(child, cell)}")
            if cells:
                parts.append(', '.join(cells))
        return '; '.join(parts)

    def get_translation_keys(self, config: GroupConfig) -> List[str]:
        """Aggregate the children's translation keys.

        A child is not a catalog row — nothing else walks it — so its ``name``
        is collected here alongside whatever its own type contributes (option
        labels, header titles, …). Order follows ``fields``; duplicates are
        dropped, keeping the first occurrence.
        """
        keys: List[str] = []
        try:
            children = _child_defs(config)
        except FeatureValidationError:
            return []
        for child in children:
            if child.name:
                keys.append(child.name)
            keys.extend(collect_translation_keys_for_feature(child.config))
        seen: set = set()
        unique: List[str] = []
        for key in keys:
            if key not in seen:
                seen.add(key)
                unique.append(key)
        return unique
