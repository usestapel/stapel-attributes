// bool value-editor — 1:1 port of bool_editor.js (LOGIC-NOTES LN-V04/V05).
import { html, type TemplateResult } from "lit";
import { ValueEditorElement, valueEditorFactory } from "./base.js";
import { registerValueEditor } from "../registry.js";

export class BoolValueEditor extends ValueEditorElement {
  private get current(): boolean | null {
    return this._value ? (this._value.value as boolean) : null;
  }

  /** LN-V05 toggle: re-click same value clears it ONLY when not mandatory. */
  private setBool(b: boolean): void {
    if (this.current === b && !this.mandatory) {
      this._value = null;
    } else {
      this._value = { type: "bool", value: b };
    }
    this.emit();
  }

  protected renderInput(): TemplateResult {
    const trueLabel = String(this.config.trueLabel ?? "Yes");
    if (this.mandatory) {
      // Mandatory -> two chips.
      const falseLabel = String(this.config.falseLabel ?? "No");
      return html`
        <div class="ve__row">
          <button
            type="button"
            class="chip ${this.current === true ? "chip--selected" : ""}"
            @click=${() => this.setBool(true)}
          >${trueLabel}</button>
          <button
            type="button"
            class="chip ${this.current === false ? "chip--selected" : ""}"
            @click=${() => this.setBool(false)}
          >${falseLabel}</button>
        </div>
      `;
    }
    // Optional -> checkbox; checked=true or unchecked=null (never false, LN-V05).
    return html`
      <label class="ve__row" style="cursor: pointer">
        <input
          type="checkbox"
          .checked=${this.current === true}
          @change=${(e: Event) => {
            this._value = (e.target as HTMLInputElement).checked ? { type: "bool", value: true } : null;
            this.emit();
          }}
        />
        <span>${trueLabel}</span>
      </label>
    `;
  }
}

if (typeof customElements !== "undefined" && !customElements.get("stapel-ve-bool")) {
  customElements.define("stapel-ve-bool", BoolValueEditor);
}
registerValueEditor("bool", valueEditorFactory(BoolValueEditor));
