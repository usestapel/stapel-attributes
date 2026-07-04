// date value-editor — 1:1 port of date_editor.js (LOGIC-NOTES LN-V06..V09).
// Stores Unix SECONDS. TZ asymmetry preserved: reads via UTC toISOString;
// `year` writes construct a LOCAL Date(y,0,1) (LN-V07 / LN-B08).
import { html, type TemplateResult } from "lit";
import { ValueEditorElement, valueEditorFactory } from "./base.js";
import { registerValueEditor } from "../registry.js";

type Precision = "year" | "month" | "datetime" | "date";

export class DateValueEditor extends ValueEditorElement {
  private get precision(): Precision {
    return (this.config.precision as Precision) || "date";
  }
  private get ts(): number | null {
    return this._value ? (this._value.value as number) : null;
  }

  private tsToInput(ts: number, p: Precision): string {
    const d = new Date(ts * 1000);
    switch (p) {
      case "year": return d.getFullYear().toString();
      case "month": return d.toISOString().substring(0, 7);
      case "datetime": return d.toISOString().substring(0, 16);
      default: return d.toISOString().substring(0, 10);
    }
  }

  private inputToTs(input: string, p: Precision): number {
    let d: Date;
    switch (p) {
      case "year": d = new Date(parseInt(input, 10), 0, 1); break; // local (LN-B08)
      case "month": d = new Date(input + "-01"); break;
      default: d = new Date(input); break;
    }
    return Math.floor(d.getTime() / 1000);
  }

  private formatTs(ts: number, p: Precision): string {
    const d = new Date(ts * 1000);
    switch (p) {
      case "year": return d.getFullYear().toString();
      case "month": return d.toLocaleDateString(undefined, { year: "numeric", month: "short" });
      case "datetime": return d.toLocaleString();
      default: return d.toLocaleDateString();
    }
  }

  private onInput(inputValue: string): void {
    this._value = inputValue ? { type: "date", value: this.inputToTs(inputValue, this.precision) } : null;
    this.emit();
  }

  protected override validateValue(): string[] {
    const errs: string[] = [];
    const val = this.ts;
    if (val === null) return errs;
    const now = Math.floor(Date.now() / 1000);
    if (this.config.minDate != null && val < (this.config.minDate as number)) errs.push("Date is too early");
    if (this.config.maxDate != null && val > (this.config.maxDate as number)) errs.push("Date is too late");
    if (this.config.allowFuture === false && val > now) errs.push("Future dates not allowed");
    if (this.config.allowPast === false && val < now) errs.push("Past dates not allowed");
    return errs;
  }

  protected renderInput(): TemplateResult {
    const p = this.precision;
    const inputType = p === "year" ? "number" : p === "month" ? "month" : p === "datetime" ? "datetime-local" : "date";
    const val = this.ts !== null ? this.tsToInput(this.ts, p) : "";
    const min = this.config.minDate && p !== "year" ? this.tsToInput(this.config.minDate as number, p) : "";
    const max = this.config.maxDate && p !== "year" ? this.tsToInput(this.config.maxDate as number, p) : "";
    const quick = (this.config.options as number[]) || [];
    return html`
      <input
        type=${inputType}
        .value=${val}
        min=${p === "year" ? "1900" : min}
        max=${p === "year" ? "2100" : max}
        placeholder=${p === "year" ? "YYYY" : String(this.config.placeholder ?? "")}
        @change=${(e: Event) => this.onInput((e.target as HTMLInputElement).value)}
      />
      ${quick.length ? html`<div class="ve__row">${quick.map((ts) => html`
        <button type="button" class="chip" @click=${() => { this._value = { type: "date", value: ts }; this.emit(); }}>
          ${this.formatTs(ts, p)}</button>`)}
      </div>` : ""}
    `;
  }
}

if (typeof customElements !== "undefined" && !customElements.get("stapel-ve-date")) {
  customElements.define("stapel-ve-date", DateValueEditor);
}
registerValueEditor("date", valueEditorFactory(DateValueEditor));
