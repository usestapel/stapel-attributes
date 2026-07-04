// hex_color value-editor — 1:1 port of hex_color_editor.js (LOGIC-NOTES
// LN-V11..V15). DTO carries ONLY the fields present in the config option
// (never the display-only palette label). Exact-match checkmark on all three.
import { html, css, type TemplateResult, type CSSResultGroup } from "lit";
import { ValueEditorElement, valueEditorFactory } from "./base.js";
import { registerValueEditor } from "../registry.js";
import { SIMPLE_COLORS, getColorStyle, isGradient, type ColorOption } from "./colors.js";

interface DisplayOpt extends ColorOption { _displayLabel?: string; }

export class HexColorValueEditor extends ValueEditorElement {
  private _locked = false;

  static override styles: CSSResultGroup = [
    ValueEditorElement.styles,
    css`
      .swatches { display: flex; flex-wrap: wrap; gap: var(--stapel-space-3, 12px); }
      .swatch { display: flex; flex-direction: column; align-items: center; gap: var(--stapel-space-1, 4px); width: 56px; }
      .circle {
        width: 32px; height: 32px; border-radius: 50%;
        border: 1px solid var(--stapel-color-border, #d7dbe3);
        cursor: pointer; position: relative; padding: 0;
      }
      .circle--selected { box-shadow: var(--stapel-focus-ring, 0 0 0 2px #fff, 0 0 0 4px #2a90d9); }
      .check { position: absolute; inset: 0; display: grid; place-items: center; color: #fff; }
      .name { font-size: 0.8em; color: var(--stapel-color-text-muted, #6b7280); text-align: center; }
    `,
  ];

  // LN-V13: single explicit option + !allowCustom + no value -> auto-select & lock.
  protected override willUpdate(): void {
    const options = (this.config.options as ColorOption[]) || [];
    if (options.length === 1 && !this.config.allowCustom && this._value === null && !this._locked) {
      this._locked = true;
      this._value = { type: "hex_color", value: this.copyConfigFields(options[0]) };
    }
  }

  /** LN-V11: copy only defined simple/hex/label. */
  private copyConfigFields(opt: ColorOption): ColorOption {
    const v: ColorOption = {};
    if (opt.simple !== undefined) v.simple = opt.simple;
    if (opt.hex !== undefined) v.hex = opt.hex;
    if (opt.label !== undefined) v.label = opt.label;
    return v;
  }

  private displayOptions(): DisplayOpt[] {
    const options = (this.config.options as ColorOption[]) || [];
    if (options.length === 0) {
      return SIMPLE_COLORS.filter((c) => c !== "custom").map((simple) => ({
        simple,
        _displayLabel: simple.charAt(0).toUpperCase() + simple.slice(1),
      }));
    }
    return options;
  }

  private get current(): ColorOption | null {
    return this._value ? (this._value.value as ColorOption) : null;
  }

  /** LN-V14: simple exact, hex case-insensitive, label exact — all must match. */
  private isExactMatch(opt: DisplayOpt, cur: ColorOption | null): boolean {
    if (!cur) return false;
    if ((opt.simple || null) !== (cur.simple || null)) return false;
    const oh = opt.hex ? opt.hex.toLowerCase() : null;
    const ch = cur.hex ? cur.hex.toLowerCase() : null;
    if (oh !== ch) return false;
    if ((opt.label || null) !== (cur.label || null)) return false;
    return true;
  }

  private select(opt: DisplayOpt, wasSelected: boolean): void {
    this._value = wasSelected ? null : { type: "hex_color", value: this.copyConfigFields(opt) };
    this.emit();
  }

  protected override validateValue(): string[] {
    const hex = this.current?.hex;
    if (hex && !/^#[0-9A-Fa-f]{6}$/.test(hex) && !/^#[0-9A-Fa-f]{3}$/.test(hex)) {
      return ["Invalid hex color format"];
    }
    return [];
  }

  protected renderInput(): TemplateResult {
    const cur = this.current;
    const light = ["white", "beige", "yellow", "clear"];
    return html`
      <div class="swatches">
        ${this.displayOptions().map((opt) => {
          const selected = this.isExactMatch(opt, cur);
          const style = getColorStyle(opt);
          const label = opt.label ?? opt._displayLabel ?? opt.simple ?? "";
          const bg = isGradient(style) ? `background:${style}` : `background-color:${style}`;
          return html`<div class="swatch">
            <button type="button" class="circle ${selected ? "circle--selected" : ""}"
              style=${bg} ?disabled=${this._locked}
              @click=${() => this.select(opt, selected)}>
              ${selected ? html`<span class="check" style=${light.includes(opt.simple ?? "") ? "color:#333" : ""}>✓</span>` : ""}
            </button>
            <span class="name">${label}</span>
          </div>`;
        })}
      </div>
      ${this.config.allowCustom ? html`
        <div class="ve__row" style="margin-top:var(--stapel-space-2,8px)">
          <input type="color" .value=${cur?.hex ?? "#000000"} @change=${(e: Event) => {
            this._value = { type: "hex_color", value: { simple: "custom", hex: (e.target as HTMLInputElement).value } };
            this.emit();
          }} />
        </div>` : ""}
    `;
  }
}

if (typeof customElements !== "undefined" && !customElements.get("stapel-ve-hex-color")) {
  customElements.define("stapel-ve-hex-color", HexColorValueEditor);
}
registerValueEditor("hex_color", valueEditorFactory(HexColorValueEditor));
