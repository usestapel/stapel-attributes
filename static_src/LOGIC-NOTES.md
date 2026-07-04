# LOGIC-NOTES — extraction inventory for the 1:1 port

Source of truth for porting the legacy-catalog admin static (`categories/static/admin/js/`)
into `stapel-attributes` schema-driven admin components. **The source logic is the
foundation, not a reference** (docs/attributes-admin-ui.md §"Что сохраняем"): every
behavior below is ported 1:1; only the rendering layer (IIFE/DOM → Lit) and the
CSRF/dialog/error plumbing (one runtime module) are rewritten. When the choice is
"cleaner vs same" → **same**; every deviation is recorded in §9 with a reason.

Each numbered item `LN-*` is a discrete behavior = one ported behavior + one vitest case.
Line citations are into the legacy source at extraction time (July 2026).

Excluded (app-layer, NOT ported): `size_grid`, `convertible_unit`, `unit_select`,
`size_systems`, `array`, unit tables. Also dropped: jQuery glue, `#id_draft` textarea
two-way state, `alert()`, inline styles, manual drag-drop (→ a11y reorder), Claude AI
dialogs, CDN asset-picker.

---

## 1. Field-kind dictionary (13 kinds) — from `feature_types.js`

The minimally-sufficient kind set referenced by the 9 generic types. Params in parens.

- **LN-K01 `number`** — numeric input. Params: `step` (1 or 0.01), optional `default`.
- **LN-K02 `text`** — raw single-line string, no i18n. Params: `placeholder`.
- **LN-K03 `checkbox`** — boolean. Params: `default` (may be **true OR false**).
- **LN-K04 `translatable_text`** — per-locale text map (i18n). Params: `placeholder` (sample).
- **LN-K05 `number_options`** — editable array of numbers. Params: `itemType:'number'`.
- **LN-K06 `string_options`** — editable array of strings. **No `itemType`.**
- **LN-K07 `color_options`** — list of `{simple,hex,label}`, palette from SIMPLE_COLORS.
- **LN-K08 `select`** — fixed inline `{value,label}[]` dropdown. Params: `options`,`required`,`default`.
- **LN-K09 `select_options_with_default`** — author-defined options `{value,label,default,icon}` with default flags.
- **LN-K10 `max_selected_dropdown`** — max-count dropdown derived from option count. Params: `default`.
- **LN-K11 `hierarchical_options`** — recursive tree `{value,label,icon,childrenTitle,children}`.
- **LN-K12 `timestamp`** — single Unix-seconds date/time. Params: `placeholder`.
- **LN-K13 `timestamp_array`** — editable list of Unix-seconds timestamps. Params: `placeholder`.

**LN-K00** Every field declaration carries at minimum `name` + `type`; labels are literal
display strings (config-form UI is **not** i18n-keyed), except `header.label`'s *value* is a
translation key. Field order within a type is preserved 1:1.

---

## 2. Per-type config-form declarations (9 generic types)

Declared as `config_form()` on each Python type (Stage 1). Field order is significant.

- **LN-T-int** (8 fields): `min`(number step1), `max`(number step1), `options`(number_options itemType=number), `allowCustom`(checkbox **default true**), `prefix`(translatable_text ph `$`), `postfix`(translatable_text ph `km`), `postfix1000`(translatable_text ph `k`), `placeholder`(translatable_text). No `precision`.
- **LN-T-float** (9 fields): int's set but `min`/`max` step **0.01**, plus `precision`(number **default 2** step1); postfix example `m²`.
- **LN-T-string** (8 fields): `minLength`(number), `maxLength`(number), `pattern`(**text**, not translatable), `options`(string_options, **no itemType**), `allowCustom`(checkbox default true), `prefix`/`postfix`(translatable_text), `placeholder`(translatable_text). **No `postfix1000`.**
- **LN-T-bool** (2 fields): `trueLabel`(translatable_text ph `yes`), `falseLabel`(translatable_text ph `no`).
- **LN-T-hex_color** (2 fields): `options`(color_options), `allowCustom`(checkbox **default FALSE** — the only allowCustom defaulting false).
- **LN-T-select** (5 fields): `options`(select_options_with_default), `uiStyle`(select required **default `chips`**, values chips|checkboxes|dropdown), `minSelected`(number **default 0**), `maxSelected`(max_selected_dropdown **default 1**), `lockUserInput`(checkbox, no default).
- **LN-T-hierarchical_select** (1 field): `options`(hierarchical_options).
- **LN-T-date** (9 fields): `precision`(select required **default `date`**, year|month|date|datetime), `minDate`/`maxDate`(timestamp), `allowFuture`(checkbox default true), `allowPast`(checkbox default true), `default`(timestamp — field literally named `default`), `options`(timestamp_array), `lockInput`(checkbox — **note name `lockInput`, not `lockUserInput`**), `placeholder`(**text**, not translatable).
- **LN-T-header** (2 fields): `style`(select required **default `h2`** — see LN-B01), `label`(**text** required, ph `section.general`, value is a translation key).

---

## 3. Config-editor behaviors — from `config_editor.js`

**META (LN-C00):** there is **no explicit validation layer** — no throw, no error keys.
"Validation" = silent filtering + coercion at output (`getConfig`/`_getFieldValue`). The
port's config editor reproduces this: empty/invalid entries are *dropped*, required is
cosmetic (`*` suffix). (Real validation is the Python side — declarations + structured
errors; JS only mirrors UX. docs §4 row "Строгость/валидация".)

### Option-key generation
- **LN-C01 `labelToValue(label)`** = `label.toLowerCase().replace(/\s+/g,'_').replace(/[^\p{L}\p{N}_]/gu,'')`. Unicode-aware; **no dedup, no uniqueness, no repeated-`_` collapse, no edge-trim**; all-symbol label → `''`; collisions possible. (utils.js L60; config_editor L1469.)
- **LN-C02** Value auto-derives from label **only when value not manually edited**, and the label is **prefix-stripped before slugify** (`_labelToValue(_removePrefix(label))`) → emitted value never carries the prefix. Applies to `select_options_with_default` and `hierarchical_options`.
- **LN-C03** Manual-edit latch is **positional** (`fieldName+'_'+idx` / `+'_'+path`); typing in a value input latches `true`. Remove/reorder does NOT remap keys → stale flags (LN-B04, preserve).

### Output filtering (per kind) — `_getFieldValue`
- **LN-C04 number/text/select/timestamp/array/translatable_text**: empty string → `undefined` (dropped). number coercion keyed on step: `step===1 ? parseInt(v) : parseFloat(v)` (parseInt no radix).
- **LN-C05 checkbox**: outputs `checked` else `false` (never dropped).
- **LN-C06 number_options**: per-row empty→`null` kept in array while editing; output filters `v !== null && !== undefined && !== ''`.
- **LN-C07 string_options**: raw strings (no slugify); output drops null/undefined/''.
- **LN-C08 timestamp_array**: output filters `t !== null`. Default new row = **Jan 1 current year 12:00 UTC** (`Date.UTC(y,0,1,12,0,0)/1000`).
- **LN-C09 color_options**: row `{hex,label,simple}`; output keeps a row if **any** of hex/label/simple truthy (`o.hex||o.label||o.simple`).
- **LN-C10 select_options_with_default**: row `{value,label,default,icon}`; output keeps rows with truthy **`value`**; `label`/`icon`/`default` pass through **untouched even when empty/false** (asymmetric vs hierarchical). **No mutual exclusion on `default`** — multiple `default:true` allowed & emitted (LN-B02).
- **LN-C11 hierarchical_options** `_filterEmptyNodes`: `nodes.filter(n=>n.value)` — a node with empty `value` is dropped **with its entire subtree** (never recursed) (LN-B03). Surviving nodes rebuilt with only-truthy keys (value always; label/icon/childrenTitle if truthy); `children` attached only if non-empty.
- **LN-C12 max_selected_dropdown**: option count from `fieldData['options']||config.options||[]`; `n=max(len,1)`; options `1..n`, value `1` labeled `(single select)`, unlimited = value `''`. Restore chain `prev || current || field.default || '1'`. Clamp `parseInt(val)>n → n` (empty bypasses). Output: `''→null`, else `parseInt`. **Only kind that emits `null`** (unlimited); getConfig includes it when `value!==undefined` (LN-B11).

### Defaults / selection
- **LN-C13 select input default**: option selected when `current===opt.value || (!current && field.default===opt.value)` — falsy `current` (0/''/false) lets `field.default` win (LN-B07).
- **LN-C14 number/text/checkbox default fallback**: `current ?? field.default ?? ''` (checkbox `current!==undefined ? current : field.default||false`).
- **LN-C15** Add-buttons for number_options/string_options/color_options/select_options **do NOT fire onChange** (render only) — an added empty row is silent until a later edit. timestamp_array add + hierarchical add + all removes DO fire (LN-B10).

### Prefix logic (config-editor internal)
- **LN-C16 `_getPrefix`** (option labels) = `categoryName + '.'` only when `translateMode==='all'` AND name truthy; else `''`.
- **LN-C17 `_getUiFieldPrefix`** (translatable_text, childrenTitle) = prefix when `translateMode!=='none'` AND name truthy.
- **LN-C18 `_addPrefix`/`_removePrefix`**: add no-ops if already prefixed; remove strips only if `startsWith(prefix)`.
- **LN-C19 `setTranslateMode`**: applies `_updateAllPrefixes` only if mode changed; per option skip if `labelManuallyEdited`; all→prepend, non-all→strip; recurses hierarchical. Hardcodes field name `'options'` (LN-B06).

### Reorder
- **LN-C20** Drop guard `fromIdx===toIdx → return`; reorder = splice-out + splice-in; then re-render + onChange. (Port: a11y reorder element, same array semantics — deviation LN-D02.)

---

## 4. Value-editor behaviors — from `value_editors/*` + `value_editor.js`

**Base contract:**
- **LN-V00** ctor reads `{config, mandatory, onChange, initialValue}`; `_value = initialValue || null`. `getValue()` → `_value` verbatim. Empty maps to **whole `_value = null`**, never `{value:null}`. `validate()` base pushes required only when `mandatory && _value === null` (strict `=== null`). Sole output: `onChange(_value, errors)`.
- **LN-V01** No editor reads `config.default`; only preload channel is `initialValue`. (Python `get_default_value` → caller converts to `initialValue`.)

### Dispatch (`index.js`)
- **LN-V02** `switch(config.type)`: string|int|float→StringNumber; bool→Bool; select→Select; hierarchical_select→Hierarchical; hex_color→HexColor; date→Date; header→Header. Each guarded `if(Editor) return new Editor()`.
- **LN-V03** `UnsupportedEditor` fallback triggers on unknown type **OR** unregistered class; renders notice `Unsupported type: <type>`; inherits base (getValue→null; required-if-mandatory).

### bool
- **LN-V04** DTO `{type:'bool', value:<bool>}` or null. Mandatory→two chips; optional→single checkbox. `trueLabel`/`falseLabel` default `Yes`/`No`.
- **LN-V05** Mandatory chips: re-clicking selected chip does **not** deselect (guard `!mandatory` false). Optional checkbox: unchecked → `null` (can only ever emit `true` or `null`, never `false`).

### date
- **LN-V06** DTO `{type:'date', value:<unix seconds int>}`. precision (`year|month|datetime|date`) drives input type; `year`→number(1900..2100).
- **LN-V07** `_timestampToInputValue`: `year`→`getFullYear()`; else `toISOString().slice` (UTC) for month(7)/datetime(16)/date(10). `_inputValueToTimestamp`: `year`→`new Date(y,0,1)` (**local**), else `new Date(input)`; `floor(getTime()/1000)`. TZ asymmetry preserved (LN-B08).
- **LN-V08** empty→null; no NaN guard (`floor(NaN/1000)=NaN` stored — preserve/flag). Quick-option buttons from `config.options`.
- **LN-V09** validate: `minDate`/`maxDate` via `!=null` (all precisions) → 'too early'/'too late'; `allowFuture===false && val>now` → future not allowed; `allowPast===false && val<now` → past not allowed (now=`floor(Date.now()/1000)`).

### header
- **LN-V10** Display-only: forces `mandatory=false`, `_value=null` always; hides error display; `getValue()`→null; `validate()`→[]. **Emits no DTO** — excluded from produced value map.

### hex_color
- **LN-V11** DTO `{type:'hex_color', value:{...}}` with **only config-present fields** copied (`simple`/`hex`/`label` each iff `!==undefined`). Never synthesize hex/label from palette. Custom → `{simple:'custom', hex:<input>}`.
- **LN-V12** `_getDisplayOptions`: empty options → full palette minus `custom`, mapped `{simple,_displayLabel}`. `_display*` are render-only, never in DTO.
- **LN-V13** Auto-select single: `options.length===1 && !allowCustom && _value===null` → auto-select + lock (no click handler).
- **LN-V14** `_isExactMatch`: `simple` exact, `hex` **case-insensitive**, `label` exact; all three match → checkmark/selected. Toggle-off (`wasSelected`) → `_value=null`.
- **LN-V15** validate: hex present must match `/^#[0-9A-Fa-f]{6}$/` or `/^#[0-9A-Fa-f]{3}$/`.

### hierarchical_select
- **LN-V16** DTO `{type:'hierarchical_select', value:[...path]}` — ordered node `value`s root→deepest; empty→null. `_initFromValue`: array→copy else [].
- **LN-V17** Auto-select single-option levels (lock); a level with multiple options but one already in path descends into it. Locked levels: disabled, omit `-- Select --`.
- **LN-V18** Cascade shows one `<select>` per selected depth + one for next level if last selected node has children. `childrenTitle` labels the child level. Node label falls back to `value`.
- **LN-V19** `_onLevelChange`: `''` → `path.slice(0,depth)` (clear this+below); else `slice(0,depth)` then set — **changing a parent truncates all descendants**; then auto-select single children from depth+1.
- **LN-V20** validate: required when `mandatory && depth===0`; `minDepth` default 1; `depth>0 && depth<minDepth` → 'at least N'; `maxDepth && depth>maxDepth` → 'at most N'. The "incomplete selection" block is a **no-op** — partial/branch selections allowed (preserve, LN-B14).

### select
- **LN-V21** DTO `{type:'select', value:[...values]}` — **always array**, even single-select; empty→null. uiStyle default `chips`.
- **LN-V22** `_toggleValue`: already selected → splice out; else `maxSelected===1` → **replace** (single-select); else `maxSelected && len>=maxSelected` → **return without adding** (silent hard cap at entry); else push.
- **LN-V23** validate: required when `mandatory && count===0`; `minSelected` default 0, enforced only when `count>0` (`count<minSelected` → 'at least N'); `maxSelected && count>maxSelected` → 'at most N'.
- **LN-V24** dropdown single vs multi: single = one `<select>`; multi = "add" select of not-yet-selected + removable chips. checkboxes/chips per option; option `icon` prepended 16×16.

### string_number (string|int|float)
- **LN-V25** DTO `{type:<config.type||'string'>, value:<parsed>}`; number for int/float, string for string; empty/invalid→null.
- **LN-V26** `_parseValue`: int→`parseInt(raw,10)` NaN→null; float→`parseFloat` NaN→null; string→raw. Input change trims; empty→null; whitespace-only→null.
- **LN-V27** `allowCustom` defaults **on** (`!== false`). Mode: no options→plain input; options && !allowCustom→dropdown only; options && allowCustom→dropdown + "Other..." + custom input.
- **LN-V28** Auto-select single: `options.length===1 && !includeOther` → no placeholder, disabled, immediately sets `_value` = parsed single. Options may be objects `{value,label}` or primitives.
- **LN-V29** `_syncFromValue`: in-options match via `String(optVal)===String(val)` (loose); out-of-list value routes to `__custom__` + custom input.
- **LN-V30** validate: int/float `min`/`max` via `!=null` → 'Minimum/Maximum value is X'; string `minLength`/`maxLength` on `.length`; `pattern` → `new RegExp(pattern).test(val)` fail → 'Invalid format'.

---

## 5. Runtime primitives (one consolidated module)

- **LN-R01 CSRF**: `getCsrfToken()` = `legacyUtils.getCsrfToken` or cookie `csrftoken=([^;]+)`; sent `X-CSRFToken` on POST; re-synced after fetch. (Consolidate — was duplicated.)
- **LN-R02 Error envelope**: replace all `alert()` (5 sites) with a StapelError component parsing `{localizable_error, error, params}` (docs §4 / decision 4).
- **LN-R03 Dialog**: one `<stapel-dialog>` = overlay + Escape-close + overlay-click-close + returned close fn (consolidates legacyUI.showModal [no close] + addEscapeHandler + inline test-dialog variant).
- **LN-R04 i18n**: mini engine = dict + `{param}` interpolation + fallback to key; catalogs en+ru; partial locale merges over en (docs decision 2). Config-form UI labels are literal (LN-K00); only component chrome/messages are keyed `admin.attributes.*`.
- **LN-R05 Prefix-injection P1** (payload-time, from `category_feature_editor.js`): `if (translate==='all' && config && name)` → `prefix = name + '.'`; applied to option **`label`** only (not value/icon) for `select`/`hierarchical_select` with array `options`, recursing `children`, **only if `!label.startsWith(prefix)`** (idempotent). `'title'`/`'none'` → no option prefixing. Operates on a deep clone (payload-only).
- **LN-R06 Title-key gen P3** `slugToTranslationKey(slug)` = `'feature.' + slug.toLowerCase().replace(/[\s-]+/g,'_')`; fires for `'all'`||`'title'` (not `'none'`); name manual-edit latch.
- **LN-R07 Convert P2** string→select: each option `{value:opt, label: slug ? 'feature.'+slug+'.'+opt : opt}`; select→string extracts `opt.value`, drops labels. Idempotent with P1 via startsWith.
- **LN-R08 formatSlug** = `value.toLowerCase().replace(/\s+/g,'_').replace(/[^a-z0-9_-]/g,'')`.
- **LN-R09 labelToValue** = LN-C01 (shared with config-editor).

---

## 6. Ancillary constants (color kind)

- **LN-X01** `SIMPLE_COLORS` = 18 tokens incl. `custom` (…, clear, multicolor, custom).
- **LN-X02** Two copies exist and DIFFER (re-checked at source): `feature_types.js` `SIMPLE_COLOR_STYLES` maps 17 (no `custom`); but the value-editor uses **`color_mappings.js`**, whose `SIMPLE_COLOR_STYLES` maps all **18** — `custom` = `conic-gradient(red,yellow,lime,aqua,blue,magenta,red)`. `silver/gold/clear/multicolor` linear-gradient, rest solid hex. **The port uses the `color_mappings.js` table** (custom has a style). `getColorStyle(opt)`: `hex` → hex; else `simple` in styles → style; else `#CCCCCC`. `isGradient` = includes `'gradient'`.
- **LN-X03** `_applySwatchStyle`: clears bg; `hex` matching `/^#([0-9A-Fa-f]{3}|{6})$/` → backgroundColor (3/6 only, not 8); else `simple` in styles → gradient uses `background` else `backgroundColor`; else fallback `#ffffff`.

---

## 7. Closed-bug / edge-case matrix → each gets a vitest case

- **LN-B01** `header.style` default `'h2'` matches no option (`l`/`m`) — preserve verbatim (latent bug).
- **LN-B02** `select_options_with_default`: no mutual exclusion — multiple `default:true` emitted.
- **LN-B03** `_filterEmptyNodes` drops empty-`value` node **and its whole valid subtree**.
- **LN-B04** manual-edit latch positional keys not remapped on remove/reorder → stale flags.
- **LN-B05** `_updateAllPrefixes` mutates fieldData then re-seeds from stale config — prefix change may be discarded (reproduce).
- **LN-B06** `max_selected_dropdown` + `_updateAllPrefixes` hardcode field name `'options'`.
- **LN-B07** falsy-guard defaults: `!current` (select) and `'1'` fallback (max_selected) treat `0`/`''` as unset.
- **LN-B08** timestamp display UTC (`toISOString`) but parse local (`new Date`) — round-trip TZ drift; `year` writes local Jan 1.
- **LN-B09** `labelToValue` no uniqueness/dedup, can yield `''`/collisions, no `_` collapse/trim.
- **LN-B10** "Add" on 4 option editors doesn't fire onChange until later edit.
- **LN-B11** only `max_selected_dropdown` emits `null`; all others drop null/''.
- **LN-B12** hierarchical mutations guarded `if(nodeInfo && nodeInfo.node)` — lookup miss = silent no-op.
- **LN-B13** (app-layer size_systems, not ported) — noted only.
- **LN-B14** hierarchical value-editor "incomplete selection" block is a no-op — branch/partial selections allowed.
- **LN-B15** `hex_color.allowCustom` defaults **false** (only allowCustom that does).
- **LN-B16** `date.default` field is literally named `default`; `date.lockInput` vs `select.lockUserInput` naming.
- **LN-B17** `string_options` has no `itemType`; `postfix1000` only int/float; `date.placeholder` is `text`.

---

## 8. Ownership boundary (docs §"Разделение собственности")

In scope for **stapel-attributes**: field-kind dictionary + schema-driven config-editor +
value-editor registry + Test dialog + Django Widget classes. **Out** (stapel-categories):
feature-editor screen (keep/add/edit/inherit/remove/create/replace, draft→apply,
child propagation), children-editor, replace dialog, convert-type screen. The prefix/convert
*logic* (P1/P2/P3, LN-R05..R08) is a runtime primitive attributes exposes; the *screens*
that drive it live in categories. size_grid/convertible_unit → app-layer worked example.

---

## 9. Deliberate deviations (choice was "cleaner", recorded per docs rule)

- **LN-D01** Rendering IIFE/DOM → Lit 3 reactive templates (mandated by docs decision/§1).
- **LN-D02** Manual HTML5 drag-drop → keyboard-accessible reorder element; array reorder
  semantics (splice-out/in, `from===to` no-op) preserved identically (LN-C20).
- **LN-D03** 5× `alert()` → StapelError envelope component (LN-R02); dialogs consolidated to
  one `<stapel-dialog>` (LN-R03); CSRF/prefix/dialog dedup into one runtime module.
- **LN-D04** Config-form UI validation stays cosmetic (LN-C00) — authoritative validation is
  the Python declarations + structured errors (docs §4). JS mirrors UX only.
- **LN-D05** Positional manual-edit latch bugs (LN-B04) reproduced 1:1 (not "fixed") — the
  fix belongs upstream in a separate change with its own test, not silently in the port.
- **LN-D06** Latent bugs LN-B01/B03/B05/B08 preserved verbatim with a test asserting the
  *current* behavior + a `// LN-Bxx: latent, preserved 1:1` comment, so a future fix is a
  visible, tested decision.

---

_Inventory total: 13 kinds, 9 type declarations, ~30 config-editor behaviors (LN-C*),
~30 value-editor behaviors (LN-V*), 9 runtime primitives (LN-R*), 17 closed-bug guards
(LN-B*). Every LN-* → a vitest case in `static_src/**/__tests__` (or a py test for §1–2)._
