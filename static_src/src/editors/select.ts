// select value-editor — 1:1 port of select_editor.js (LOGIC-NOTES LN-V21..V24).
// The DTO array IS the source of truth (value: [...values], always an array).
import { html, type TemplateResult } from "lit";
import { ValueEditorElement, valueEditorFactory } from "./base.js";
import { registerValueEditor } from "../registry.js";

interface SelOpt { value: string; label?: string; icon?: string; }

export class SelectValueEditor extends ValueEditorElement {
  private get options(): SelOpt[] {
    return (this.config.options as SelOpt[]) || [];
  }
  private get selected(): string[] {
    return this._value && Array.isArray(this._value.value) ? [...(this._value.value as string[])] : [];
  }
  private get maxSelected(): number | undefined {
    return this.config.maxSelected as number | undefined;
  }
  private label(o: SelOpt): string {
    return String(o.label ?? o.value);
  }

  /** LN-V21: empty -> null, else {type:'select', value:[...]}. */
  private setSelected(vals: string[]): void {
    this._value = vals.length === 0 ? null : { type: "select", value: vals };
    this.emit();
  }

  /** LN-V22 toggle: deselect if present; else max===1 replace; else at-cap block; else push. */
  private toggle(value: string): void {
    const sel = this.selected;
    const i = sel.indexOf(value);
    if (i >= 0) {
      sel.splice(i, 1);
      this.setSelected(sel);
      return;
    }
    if (this.maxSelected === 1) {
      this.setSelected([value]);
      return;
    }
    if (this.maxSelected && sel.length >= this.maxSelected) {
      return; // silent hard cap
    }
    sel.push(value);
    this.setSelected(sel);
  }

  protected override validateValue(): string[] {
    const errs: string[] = [];
    const count = this.selected.length;
    const minSelected = (this.config.minSelected as number) || 0;
    if (count > 0 && count < minSelected) errs.push(`Select at least ${minSelected} option(s)`);
    if (this.maxSelected && count > this.maxSelected) errs.push(`Select at most ${this.maxSelected} option(s)`);
    return errs;
  }

  // LN-V23: required is on empty selection, not strict _value===null.
  override validate(): string[] {
    this._errors = [];
    const count = this.selected.length;
    if (this.mandatory && count === 0) {
      this._errors.push(this.i18n.t("admin.attributes.required"));
      return this._errors;
    }
    this._errors.push(...this.validateValue());
    return this._errors;
  }

  private renderChips(): TemplateResult {
    const sel = this.selected;
    return html`<div class="ve__row">
      ${this.options.map((o) => html`
        <button type="button" class="chip ${sel.includes(o.value) ? "chip--selected" : ""}"
          @click=${() => this.toggle(o.value)}>
          ${o.icon ? html`<img src=${o.icon} width="16" height="16" style="vertical-align:middle;margin-right:4px" />` : ""}${this.label(o)}
        </button>`)}
    </div>`;
  }

  private renderCheckboxes(): TemplateResult {
    const sel = this.selected;
    return html`<div class="ve__row" style="flex-direction:column;align-items:flex-start">
      ${this.options.map((o) => html`
        <label class="ve__row" style="cursor:pointer">
          <input type="checkbox" .checked=${sel.includes(o.value)} @change=${() => this.toggle(o.value)} />
          <span>${this.label(o)}</span>
        </label>`)}
    </div>`;
  }

  private renderDropdown(): TemplateResult {
    const sel = this.selected;
    if (this.maxSelected === 1) {
      return html`<select .value=${sel[0] ?? ""} @change=${(e: Event) => {
        const v = (e.target as HTMLSelectElement).value;
        this.setSelected(v ? [v] : []);
      }}>
        <option value="">${this.i18n.t("admin.attributes.select_placeholder")}</option>
        ${this.options.map((o) => html`<option value=${o.value}>${this.label(o)}</option>`)}
      </select>`;
    }
    // Multi: add-select (unselected only) + removable chips.
    const remaining = this.options.filter((o) => !sel.includes(o.value));
    return html`<div class="ve__row" style="flex-direction:column;align-items:stretch">
      <select .value=${""} @change=${(e: Event) => {
        const v = (e.target as HTMLSelectElement).value;
        if (v) this.setSelected([...sel, v]);
      }}>
        <option value="">${this.i18n.t("admin.attributes.add")}</option>
        ${remaining.map((o) => html`<option value=${o.value}>${this.label(o)}</option>`)}
      </select>
      ${sel.length ? html`<div class="ve__row">${sel.map((v) => {
        const o = this.options.find((x) => x.value === v);
        return html`<span class="chip chip--selected">${o ? this.label(o) : v}
          <button type="button" style="background:none;border:none;cursor:pointer;color:inherit"
            @click=${() => this.toggle(v)}>×</button></span>`;
      })}</div>` : ""}
    </div>`;
  }

  protected renderInput(): TemplateResult {
    switch (this.config.uiStyle) {
      case "checkboxes": return this.renderCheckboxes();
      case "dropdown": return this.renderDropdown();
      default: return this.renderChips();
    }
  }
}

// @stapel-auto-define:start — django self-registers here; the lib build strips
// this block (strip-auto-define.mjs) so lib imports are side-effect-free.
if (typeof customElements !== "undefined" && !customElements.get("stapel-ve-select")) {
  customElements.define("stapel-ve-select", SelectValueEditor);
}
registerValueEditor("select", valueEditorFactory(SelectValueEditor));
// @stapel-auto-define:end

