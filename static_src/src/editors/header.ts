// header value-editor — 1:1 port of header_editor.js (LOGIC-NOTES LN-V10).
// Display-only: never mandatory, never holds a value, emits no DTO.
import { html, css, type TemplateResult } from "lit";
import { ValueEditorElement, valueEditorFactory } from "./base.js";
import { registerValueEditor } from "../registry.js";

export class HeaderValueEditor extends ValueEditorElement {
  static override styles = [
    ValueEditorElement.styles,
    css`
      .ve__header {
        font-weight: 600;
        color: var(--stapel-color-text, #1f2430);
        border-bottom: 1px solid var(--stapel-color-border, #d7dbe3);
        padding-bottom: var(--stapel-space-1, 4px);
      }
      .ve__header--l { font-size: 1.3em; }
      .ve__header--m { font-size: 1.1em; }
    `,
  ];

  override getValue(): null {
    return null; // LN-V10: never a value
  }
  override validate(): string[] {
    this._errors = [];
    return this._errors;
  }

  protected renderInput(): TemplateResult {
    const style = String(this.config.style ?? "l");
    const text = String(this.config.title ?? this.config.name ?? "Section");
    return html`<div class="ve__header ve__header--${style}">${text}</div>`;
  }
}

if (typeof customElements !== "undefined" && !customElements.get("stapel-ve-header")) {
  customElements.define("stapel-ve-header", HeaderValueEditor);
}
registerValueEditor("header", valueEditorFactory(HeaderValueEditor));
