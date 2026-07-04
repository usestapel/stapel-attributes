// Entry point — registers every built-in editor + component and installs the
// public global. esbuild bundles this to static/stapel_attributes/attributes-admin.js.

// Side-effect imports: each registers its value-editor with the registry.
import "./editors/bool.js";
import "./editors/string_number.js";
import "./editors/header.js";
import "./editors/select.js";
import "./editors/date.js";
import "./editors/hex_color.js";
import "./editors/hierarchical_select.js";
// Components
import "./config-editor.js";
import "./runtime/dialog.js";
import "./runtime/error-view.js";

import { installGlobal, resolveValueEditor, type ValueEditorOptions } from "./registry.js";
import { I18n } from "./runtime/i18n.js";
import { ConfigEditorElement } from "./config-editor.js";
import { openTestDialog } from "./test-dialog.js";
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

/** Mount a <stapel-config-editor> into `host` (called by the Django widget). */
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

const api = installGlobal();
const extended = Object.assign(api, {
  I18n,
  mountConfigEditor,
  createValueEditor,
  openTestDialog,
  ConfigEditor: ConfigEditorElement,
});
if (typeof window !== "undefined") {
  (window as unknown as { StapelAttributes: typeof extended }).StapelAttributes = extended;
}

export { I18n, resolveValueEditor, ConfigEditorElement, openTestDialog };
export type { TypeDecl, FeatureConfig } from "./types.js";
