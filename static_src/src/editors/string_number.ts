// string|int|float value-editor — 1:1 port of string_number_editor.js
// (LOGIC-NOTES LN-V25..V30). Three modes: plain input, dropdown-only,
// dropdown + "Other..." custom. Lit derives the rendered state from _value +
// _customMode instead of the source's imperative _syncFromValue.
import { html, type TemplateResult } from "lit";
import { state } from "lit/decorators.js";
import { ValueEditorElement, valueEditorFactory } from "./base.js";
import { registerValueEditor } from "../registry.js";

type Prim = string | number;
interface OptObj { value: Prim; label?: string; }
type Opt = Prim | OptObj;

const CUSTOM = "__custom__";

export class StringNumberValueEditor extends ValueEditorElement {
  @state() private _customMode = false;
  private _singleApplied = false;

  private get type(): string {
    return (this.config.type as string) || "string";
  }
  private get options(): Opt[] {
    return (this.config.options as Opt[]) || [];
  }
  private get allowCustom(): boolean {
    return this.config.allowCustom !== false; // LN-V27 default on
  }
  private optVal(o: Opt): Prim {
    return typeof o === "object" ? o.value : o;
  }
  private optLabel(o: Opt): string {
    return String(typeof o === "object" ? (o.label ?? o.value) : o);
  }

  /** LN-V26: trim; ''->null; int=parseInt/NaN->null; float=parseFloat/NaN->null. */
  private parse(raw: string): Prim | null {
    if (this.type === "int") {
      const n = parseInt(raw, 10);
      return isNaN(n) ? null : n;
    }
    if (this.type === "float") {
      const n = parseFloat(raw);
      return isNaN(n) ? null : n;
    }
    return raw;
  }

  private setFromRaw(raw: string): void {
    const t = raw.trim();
    if (t === "") {
      this._value = null;
    } else {
      const parsed = this.parse(t);
      this._value = parsed !== null ? { type: this.type, value: parsed } : null;
    }
    this.emit();
  }

  private get current(): Prim | null {
    return this._value ? (this._value.value as Prim) : null;
  }

  private inOptions(val: Prim | null): boolean {
    return this.options.some((o) => String(this.optVal(o)) === String(val));
  }

  // LN-V28: single-option dropdown auto-selects (disabled) and sets the value once.
  protected override willUpdate(): void {
    const single = this.options.length === 1 && !this.allowCustom;
    if (single && !this._singleApplied && this._value === null) {
      this._singleApplied = true;
      this._value = { type: this.type, value: this.parse(String(this.optVal(this.options[0]))) };
    }
  }

  protected override validateValue(): string[] {
    const errs: string[] = [];
    const val = this.current;
    if (val === null) return errs;
    if (this.type === "int" || this.type === "float") {
      const n = val as number;
      if (this.config.min != null && n < (this.config.min as number)) errs.push(`Minimum value is ${this.config.min}`);
      if (this.config.max != null && n > (this.config.max as number)) errs.push(`Maximum value is ${this.config.max}`);
    } else {
      const s = val as string;
      if (this.config.minLength != null && s.length < (this.config.minLength as number)) errs.push(`Minimum length is ${this.config.minLength}`);
      if (this.config.maxLength != null && s.length > (this.config.maxLength as number)) errs.push(`Maximum length is ${this.config.maxLength}`);
      if (this.config.pattern && !new RegExp(this.config.pattern as string).test(s)) errs.push("Invalid format");
    }
    return errs;
  }

  private renderPlainInput(): TemplateResult {
    const isString = this.type === "string";
    const step = this.type === "int" ? "1" : this.type === "float"
      ? String(Math.pow(10, -((this.config.precision as number) ?? 2))) : undefined;
    const numOpts = (this.type === "int" || this.type === "float") ? this.options : [];
    return html`
      <div class="ve__row">
        ${this.config.prefix ? html`<span>${this.config.prefix}</span>` : ""}
        <input
          type=${isString ? "text" : "number"}
          .value=${this.current ?? ""}
          placeholder=${this.config.placeholder ? String(this.config.placeholder) : ""}
          step=${step ?? ""}
          min=${this.config.min != null ? String(this.config.min) : ""}
          max=${this.config.max != null ? String(this.config.max) : ""}
          @input=${(e: Event) => this.setFromRaw((e.target as HTMLInputElement).value)}
        />
        ${this.config.postfix ? html`<span>${this.config.postfix}</span>` : ""}
      </div>
      ${numOpts.length ? html`<div class="ve__row">${numOpts.map((o) => html`
        <button type="button" class="chip" @click=${() => this.setFromRaw(String(this.optVal(o)))}>${this.optLabel(o)}</button>`)}
      </div>` : ""}
    `;
  }

  private renderDropdown(includeOther: boolean): TemplateResult {
    const val = this.current;
    const single = this.options.length === 1 && !includeOther; // LN-V28
    const selected = this._customMode ? CUSTOM
      : val === null ? ""
      : this.inOptions(val) ? String(val)
      : includeOther ? CUSTOM : "";
    const step = this.type === "int" ? "1" : this.type === "float"
      ? String(Math.pow(10, -((this.config.precision as number) ?? 2))) : undefined;
    return html`
      <div class="ve__row" style="flex-direction: column; align-items: stretch">
        <select ?disabled=${single} .value=${single ? String(this.optVal(this.options[0])) : selected}
          @change=${(e: Event) => this.onSelect((e.target as HTMLSelectElement).value)}>
          ${single ? "" : html`<option value="">${this.i18n.t("admin.attributes.select_placeholder")}</option>`}
          ${this.options.map((o) => html`<option value=${String(this.optVal(o))}>${this.optLabel(o)}</option>`)}
          ${includeOther ? html`<option value=${CUSTOM}>${this.i18n.t("admin.attributes.other")}</option>` : ""}
        </select>
        ${includeOther && this._customMode ? html`
          <input type=${this.type === "string" ? "text" : "number"} step=${step ?? ""}
            .value=${val !== null && !this.inOptions(val) ? String(val) : ""}
            placeholder=${this.i18n.t("admin.attributes.other")}
            @input=${(e: Event) => this.setFromRaw((e.target as HTMLInputElement).value)} />` : ""}
      </div>
    `;
  }

  private onSelect(value: string): void {
    if (value === CUSTOM) {
      this._customMode = true; // keep old value until custom filled (LN-V29)
      this.requestUpdate();
      return;
    }
    this._customMode = false;
    if (value === "") {
      this._value = null;
    } else {
      this._value = { type: this.type, value: this.parse(value) };
    }
    this.emit();
  }

  protected renderInput(): TemplateResult {
    if (this.options.length === 0) return this.renderPlainInput();
    if (!this.allowCustom) return this.renderDropdown(false);
    return this.renderDropdown(true);
  }
}

if (typeof customElements !== "undefined" && !customElements.get("stapel-ve-string-number")) {
  customElements.define("stapel-ve-string-number", StringNumberValueEditor);
}
for (const t of ["string", "int", "float"]) {
  registerValueEditor(t, valueEditorFactory(StringNumberValueEditor));
}
