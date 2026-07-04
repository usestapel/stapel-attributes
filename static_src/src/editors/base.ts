// Base value-editor — Lit port of legacy value_editor.js (LOGIC-NOTES LN-V00).
// Contract preserved 1:1: `getValue()` returns the DTO or null verbatim; empty
// maps to the WHOLE value being null; the required check is strict `=== null`;
// the sole output is onChange(dto, errors). Rendering is Lit; styling is
// var(--stapel-*) only (shadow DOM; CSS vars pierce the boundary).
import { LitElement, html, css, type TemplateResult, type CSSResultGroup } from "lit";
import { property, state } from "lit/decorators.js";
import type { FeatureConfig, ValueDto, I18nLike } from "../types.js";
import type { ValueEditorOptions } from "../registry.js";

export abstract class ValueEditorElement extends LitElement {
  @property({ attribute: false }) config: FeatureConfig = { type: "unknown" };
  @property({ attribute: false }) mandatory = false;
  @property({ attribute: false }) i18n!: I18nLike;

  /** Callback set by the factory (mirrors the source onChange). */
  onValueChange?: (dto: ValueDto | null, errors: string[]) => void;

  @state() protected _value: ValueDto | null = null;
  @state() protected _errors: string[] = [];

  static override styles: CSSResultGroup = css`
    :host {
      display: block;
      font: var(--stapel-font, inherit);
      color: var(--stapel-color-text, #1f2430);
    }
    .ve__errors {
      display: flex;
      flex-direction: column;
      gap: var(--stapel-space-1, 4px);
      margin-top: var(--stapel-space-1, 4px);
    }
    .ve__error {
      color: var(--stapel-color-error, #d64545);
      font-size: 0.85em;
    }
    .ve__row {
      display: flex;
      flex-wrap: wrap;
      gap: var(--stapel-space-2, 8px);
      align-items: center;
    }
    button,
    input,
    select {
      font: inherit;
      color: inherit;
    }
    input[type="text"],
    input[type="number"],
    input[type="date"],
    input[type="month"],
    input[type="datetime-local"],
    select {
      background: var(--stapel-color-bg, #fff);
      border: 1px solid var(--stapel-color-border, #d7dbe3);
      border-radius: var(--stapel-radius-sm, 4px);
      padding: var(--stapel-space-1, 4px) var(--stapel-space-2, 8px);
    }
    input:focus-visible,
    select:focus-visible,
    button:focus-visible {
      outline: none;
      box-shadow: var(--stapel-focus-ring, 0 0 0 2px #fff, 0 0 0 4px #2a90d9);
    }
    .chip {
      cursor: pointer;
      border: 1px solid var(--stapel-color-border, #d7dbe3);
      background: var(--stapel-color-surface, #f7f8fa);
      color: var(--stapel-color-text, #1f2430);
      border-radius: var(--stapel-radius-lg, 12px);
      padding: var(--stapel-space-1, 4px) var(--stapel-space-3, 12px);
    }
    .chip--selected {
      background: var(--stapel-color-primary, #2a90d9);
      color: var(--stapel-color-primary-contrast, #fff);
      border-color: var(--stapel-color-primary, #2a90d9);
    }
  `;

  /** LN-V00: DTO or null verbatim. */
  getValue(): ValueDto | null {
    return this._value;
  }

  setValue(dto: ValueDto | null): void {
    this._value = dto;
    this.onValueUpdated();
    this.requestUpdate();
  }

  getErrors(): string[] {
    return this._errors;
  }

  /** Base required check (strict `=== null`) + subclass value validation. */
  validate(): string[] {
    this._errors = [];
    if (this.mandatory && this._value === null) {
      this._errors.push(this.i18n.t("admin.attributes.required"));
    }
    if (this._value !== null) {
      this._errors.push(...this.validateValue());
    }
    return this._errors;
  }

  /** Subclass hook — value-specific checks (only called when value !== null). */
  protected validateValue(): string[] {
    return [];
  }

  /** Subclass hook — sync internal render state after an external setValue. */
  protected onValueUpdated(): void {}

  /** Emit change: validate, re-render, fire onChange + a DOM event. */
  protected emit(): void {
    this.validate();
    this.requestUpdate();
    this.onValueChange?.(this._value, this._errors);
    this.dispatchEvent(
      new CustomEvent("value-change", {
        detail: { value: this._value, errors: this._errors },
        bubbles: true,
        composed: true,
      }),
    );
  }

  protected abstract renderInput(): TemplateResult;

  override render(): TemplateResult {
    return html`
      <div class="ve" part="editor">${this.renderInput()}</div>
      <div class="ve__errors">
        ${this._errors.map((e) => html`<span class="ve__error">${e}</span>`)}
      </div>
    `;
  }
}

/** Bridge a ValueEditorElement subclass to the registry's factory contract. */
export function valueEditorFactory(
  ctor: new () => ValueEditorElement,
): (opts: ValueEditorOptions) => HTMLElement {
  return (opts) => {
    const el = new ctor();
    el.config = opts.config;
    el.mandatory = opts.mandatory ?? false;
    el.i18n = opts.i18n;
    el.onValueChange = opts.onChange;
    if (opts.initialValue !== undefined) {
      el.setValue((opts.initialValue as ValueDto | null) ?? null);
    }
    return el;
  };
}
