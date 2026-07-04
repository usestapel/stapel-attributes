// The customization seam (docs §4 / decision 2 — "самое главное"): two open
// merge registries mirroring the Python type registry. Built-ins are seeded at
// import; host registrations merge over them (later wins), via
// `window.StapelAttributes.register*` or the module exports. Unknown kinds/types
// fall back gracefully (UnsupportedEditor), never throw.
import type { FeatureConfig, FormFieldDecl, I18nLike } from "./types.js";

/** Options every value-editor receives (LOGIC-NOTES LN-V00). */
export interface ValueEditorOptions {
  config: FeatureConfig;
  mandatory?: boolean;
  initialValue?: unknown;
  onChange?: (dto: unknown, errors: string[]) => void;
  i18n: I18nLike;
}

/** A value-editor is a custom element tag name OR a factory returning an
 *  HTMLElement configured from options. Custom elements are the norm; a factory
 *  keeps the seam framework-agnostic. */
export type ValueEditorFactory = (opts: ValueEditorOptions) => HTMLElement;

/** A config widget renders one field-kind inside the config editor. */
export interface ConfigWidgetOptions {
  field: FormFieldDecl;
  value: unknown;
  onChange: (value: unknown) => void;
  i18n: I18nLike;
}
export type ConfigWidgetFactory = (opts: ConfigWidgetOptions) => HTMLElement;

const valueEditors = new Map<string, ValueEditorFactory>();
const configWidgets = new Map<string, ConfigWidgetFactory>();

/** Register a value-editor for a feature type slug (merge; later wins). */
export function registerValueEditor(type: string, factory: ValueEditorFactory): void {
  valueEditors.set(type, factory);
}

/** Register a config widget for a field-kind (merge; later wins). */
export function registerConfigWidget(kind: string, factory: ConfigWidgetFactory): void {
  configWidgets.set(kind, factory);
}

/** Resolve a value-editor; unknown type -> UnsupportedEditor fallback (LN-V03). */
export function resolveValueEditor(type: string | undefined): ValueEditorFactory {
  return (type && valueEditors.get(type)) || unsupportedValueEditor;
}

/** Resolve a config widget by kind; unknown kind -> undefined (config editor
 *  renders a plain text input fallback, LN-C07). */
export function resolveConfigWidget(kind: string): ConfigWidgetFactory | undefined {
  return configWidgets.get(kind);
}

/** LN-V03: yellow "Unsupported type" notice; produces no value. */
const unsupportedValueEditor: ValueEditorFactory = (opts) => {
  const el = document.createElement("div");
  el.className = "value-editor value-editor--unsupported";
  el.textContent = opts.i18n.t("admin.attributes.unsupported_type", {
    type: opts.config?.type ?? "unknown",
  });
  // Base contract: no value, only-required-if-mandatory (handled by caller).
  (el as HTMLElement & { getValue?: () => unknown }).getValue = () => null;
  return el;
};

export function registeredValueEditorTypes(): string[] {
  return [...valueEditors.keys()].sort();
}
export function registeredConfigWidgetKinds(): string[] {
  return [...configWidgets.keys()].sort();
}

/** Public global surface (docs §4): host code registers without a build step. */
export interface StapelAttributesGlobal {
  registerValueEditor: typeof registerValueEditor;
  registerConfigWidget: typeof registerConfigWidget;
  registeredValueEditorTypes: typeof registeredValueEditorTypes;
  registeredConfigWidgetKinds: typeof registeredConfigWidgetKinds;
}

export function installGlobal(): StapelAttributesGlobal {
  const api: StapelAttributesGlobal = {
    registerValueEditor,
    registerConfigWidget,
    registeredValueEditorTypes,
    registeredConfigWidgetKinds,
  };
  if (typeof window !== "undefined") {
    (window as unknown as { StapelAttributes?: StapelAttributesGlobal }).StapelAttributes = api;
  }
  return api;
}
