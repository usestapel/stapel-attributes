// @stapel/attributes-admin — externalized-Lit ESM entry (npm consumers, e.g.
// @stapel/attributes-react). Companion to index.ts (the Django admin bundle).
//
// Contract: importing this module registers NOTHING — no customElements.define,
// no window global, no value-editor registration. That is what lets the package
// declare `sideEffects: false` and tree-shake honestly. The host opts in with an
// explicit `defineElements()` call. Lit is a peerDependency here (externalized by
// the build), not inlined.
//
// In the shipped bundle the editor/component modules are side-effect-free: the
// lib build strips their `// @stapel-auto-define` tails (see strip-auto-define.mjs),
// so the ONLY place that defines elements / registers value-editors is
// defineElements() below. (The django build keeps those tails; see index.ts.)
import { I18n } from "./runtime/i18n.js";
import {
  registerValueEditor,
  resolveValueEditor,
  type ValueEditorOptions,
} from "./registry.js";
import { valueEditorFactory, type ValueEditorElement } from "./editors/base.js";
import { ConfigEditorElement } from "./config-editor.js";
import { openTestDialog } from "./test-dialog.js";
import { StapelDialog } from "./runtime/dialog.js";
import { StapelErrorView } from "./runtime/error-view.js";
import { BoolValueEditor } from "./editors/bool.js";
import { StringNumberValueEditor } from "./editors/string_number.js";
import { HeaderValueEditor } from "./editors/header.js";
import { SelectValueEditor } from "./editors/select.js";
import { DateValueEditor } from "./editors/date.js";
import { HexColorValueEditor } from "./editors/hex_color.js";
import { HierarchicalSelectValueEditor } from "./editors/hierarchical_select.js";
import type { TypeDecl, FeatureConfig, Locale } from "./types.js";

export interface MountOptions {
  declaration: TypeDecl;
  slug: string;
  config?: FeatureConfig | null;
  locale?: string;
  messages?: Record<string, Locale>;
  prefixName?: string;
  translateMode?: "all" | "title" | "none";
  onChange?: (config: FeatureConfig) => void;
}

/** Custom-element tag ↔ class table. Single source of truth for defineElements
 *  in the lib profile (mirrors the per-module `@stapel-auto-define` tails that
 *  the django bundle uses). builds.test.ts asserts the two agree. */
const ELEMENTS: ReadonlyArray<readonly [string, CustomElementConstructor]> = [
  ["stapel-config-editor", ConfigEditorElement],
  ["stapel-dialog", StapelDialog],
  ["stapel-error", StapelErrorView],
  ["stapel-ve-bool", BoolValueEditor],
  ["stapel-ve-string-number", StringNumberValueEditor],
  ["stapel-ve-header", HeaderValueEditor],
  ["stapel-ve-select", SelectValueEditor],
  ["stapel-ve-date", DateValueEditor],
  ["stapel-ve-hex-color", HexColorValueEditor],
  ["stapel-ve-hierarchical", HierarchicalSelectValueEditor],
];

/** Feature-type slug ↔ value-editor class (a class may serve several slugs). */
const VALUE_EDITORS: ReadonlyArray<readonly [string, new () => ValueEditorElement]> = [
  ["bool", BoolValueEditor],
  ["string", StringNumberValueEditor],
  ["int", StringNumberValueEditor],
  ["float", StringNumberValueEditor],
  ["header", HeaderValueEditor],
  ["select", SelectValueEditor],
  ["date", DateValueEditor],
  ["hex_color", HexColorValueEditor],
  ["hierarchical_select", HierarchicalSelectValueEditor],
];

/**
 * Register all built-in custom elements and value-editors. Idempotent and safe
 * to call more than once (customElements.define is guarded; registry is a Map).
 * Call this once, early, in a host app. Not called on import.
 */
export function defineElements(): void {
  if (typeof customElements !== "undefined") {
    for (const [tag, ctor] of ELEMENTS) {
      if (!customElements.get(tag)) customElements.define(tag, ctor);
    }
  }
  for (const [slug, ctor] of VALUE_EDITORS) {
    registerValueEditor(slug, valueEditorFactory(ctor));
  }
}

/** Mount a <stapel-config-editor> into `host`. Requires defineElements() first. */
export function mountConfigEditor(host: HTMLElement, opts: MountOptions): ConfigEditorElement {
  const i18n = new I18n(opts.locale ?? "en", opts.messages ?? {});
  const el = new ConfigEditorElement();
  el.declaration = opts.declaration;
  el.typeSlug = opts.slug;
  el.i18n = i18n;
  el.prefixName = opts.prefixName ?? "";
  el.translateMode = opts.translateMode ?? "all";
  el.onConfigChange = opts.onChange;
  host.appendChild(el);
  if (opts.config) el.setConfig(opts.config);
  return el;
}

/** Create a standalone value-editor element (listings / test surfaces). */
export function createValueEditor(opts: MountOptions & ValueEditorOptions): HTMLElement {
  return resolveValueEditor(opts.config.type)(opts);
}

export {
  I18n,
  openTestDialog,
  registerValueEditor,
  resolveValueEditor,
  valueEditorFactory,
  ConfigEditorElement,
  StapelDialog,
  StapelErrorView,
  BoolValueEditor,
  StringNumberValueEditor,
  HeaderValueEditor,
  SelectValueEditor,
  DateValueEditor,
  HexColorValueEditor,
  HierarchicalSelectValueEditor,
};
export {
  registerConfigWidget,
  resolveConfigWidget,
  registeredValueEditorTypes,
  registeredConfigWidgetKinds,
  BUILTIN_CONFIG_WIDGET,
  BUILTIN_CONFIG_WIDGET_KINDS,
} from "./registry.js";
export { ValidationErrorCode, VALIDATION_ERROR_CODES } from "./error-codes.js";
export type {
  TypeDecl,
  FeatureConfig,
  ValueDto,
  FormDeclarations,
  FormFieldDecl,
  FieldKind,
  Locale,
  I18nLike,
} from "./types.js";
export type { ValueEditorOptions, ValueEditorFactory, ConfigWidgetFactory } from "./registry.js";
