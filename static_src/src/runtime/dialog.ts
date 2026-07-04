// <stapel-dialog> — one consolidated modal primitive (LOGIC-NOTES LN-R03):
// overlay + Escape-to-close + overlay-click-to-close + a returned close fn.
// Replaces the three competing dialog helpers in the source.
import { LitElement, html, css, type TemplateResult, type CSSResultGroup } from "lit";

export class StapelDialog extends LitElement {
  static override styles: CSSResultGroup = css`
    .overlay {
      position: fixed; inset: 0; background: var(--stapel-color-overlay, rgba(20, 24, 33, 0.45));
      display: grid; place-items: center; z-index: 1000; padding: var(--stapel-space-4, 16px);
    }
    .dialog {
      background: var(--stapel-color-bg, #fff); color: var(--stapel-color-text, #1f2430);
      border-radius: var(--stapel-radius-lg, 12px); box-shadow: var(--stapel-elevation-2, 0 4px 12px rgba(0,0,0,.16));
      max-width: min(560px, 100%); max-height: 90vh; overflow: auto; padding: var(--stapel-space-5, 24px);
    }
  `;

  private _onKey = (e: KeyboardEvent) => {
    if (e.key === "Escape") this.close();
  };

  override connectedCallback(): void {
    super.connectedCallback();
    document.addEventListener("keydown", this._onKey);
  }
  override disconnectedCallback(): void {
    super.disconnectedCallback();
    document.removeEventListener("keydown", this._onKey);
  }

  close(): void {
    this.dispatchEvent(new CustomEvent("close", { bubbles: true, composed: true }));
    this.remove();
  }

  override render(): TemplateResult {
    return html`
      <div class="overlay" @click=${(e: Event) => { if (e.target === e.currentTarget) this.close(); }}>
        <div class="dialog" role="dialog" aria-modal="true"><slot></slot></div>
      </div>
    `;
  }
}

if (typeof customElements !== "undefined" && !customElements.get("stapel-dialog")) {
  customElements.define("stapel-dialog", StapelDialog);
}

/** Open `content` in a modal; returns a close fn (LN-R03). */
export function openDialog(content: Node): () => void {
  const dlg = new StapelDialog();
  dlg.appendChild(content);
  document.body.appendChild(dlg);
  return () => dlg.close();
}
