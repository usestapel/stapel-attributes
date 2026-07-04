// <stapel-error> — renders a StapelError envelope {localizable_error, error,
// params} through the i18n engine (LOGIC-NOTES LN-R02). Replaces every alert().
import { LitElement, html, css, type TemplateResult, type CSSResultGroup } from "lit";
import { property } from "lit/decorators.js";
import type { I18nLike } from "../types.js";
import type { ErrorEnvelope } from "./csrf.js";

export class StapelErrorView extends LitElement {
  @property({ attribute: false }) envelope: ErrorEnvelope | null = null;
  @property({ attribute: false }) i18n!: I18nLike;

  static override styles: CSSResultGroup = css`
    .err {
      color: var(--stapel-color-error, #d64545);
      background: var(--stapel-color-error-bg, #fdecec);
      border: 1px solid var(--stapel-color-error, #d64545);
      border-radius: var(--stapel-radius-sm, 4px);
      padding: var(--stapel-space-2, 8px) var(--stapel-space-3, 12px);
    }
  `;

  private message(): string {
    const e = this.envelope;
    if (!e) return "";
    if (e.localizable_error) return this.i18n.t(e.localizable_error, e.params);
    return e.error || this.i18n.t("admin.attributes.error.generic");
  }

  override render(): TemplateResult {
    return this.envelope ? html`<div class="err" role="alert">${this.message()}</div>` : html``;
  }
}

if (typeof customElements !== "undefined" && !customElements.get("stapel-error")) {
  customElements.define("stapel-error", StapelErrorView);
}
