// <stapel-config-editor> — schema-driven config form. Renders the 13 field-kinds
// from a Python form_declarations() entry and emits the config JSON. Ports
// config_editor.js (LOGIC-NOTES §3): "validation" = silent filtering + coercion
// at output (getConfig), option values auto-derive from labels via labelToValue
// (prefix-stripped) unless manually edited, per-kind output filters preserved.
import { LitElement, html, css, type TemplateResult, type CSSResultGroup } from "lit";
import { property, state } from "lit/decorators.js";
import type { FormFieldDecl, TypeDecl, FeatureConfig, I18nLike, InlineOption } from "./types.js";
import { labelToValue, removePrefix } from "./runtime/keys.js";
import { SIMPLE_COLORS, getColorStyle, isGradient } from "./editors/colors.js";

type Row = Record<string, unknown>;

export class ConfigEditorElement extends LitElement {
  @property({ attribute: false }) declaration: TypeDecl = { label_key: "", fields: [] };
  @property({ attribute: false }) i18n!: I18nLike;
  /** category/feature name that drives the option-label prefix (LN-C16). */
  @property({ attribute: false }) prefixName = "";
  @property({ attribute: false }) translateMode: "all" | "title" | "none" = "all";
  /** The type discriminator written into every emitted config. */
  @property({ attribute: false }) typeSlug = "";
  onConfigChange?: (config: FeatureConfig) => void;

  /** Working store of field values (fieldData in the source). */
  @state() private data: Record<string, unknown> = {};
  /** Positional manual-edit latch (LN-C03), key `${field}_${idx|path}`. */
  private manual = new Set<string>();

  static override styles: CSSResultGroup = css`
    :host { display: block; color: var(--stapel-color-text, #1f2430); font: var(--stapel-font, inherit); }
    .field { margin-bottom: var(--stapel-space-3, 12px); }
    label.hd { display: block; font-weight: 600; margin-bottom: var(--stapel-space-1, 4px); }
    .req { color: var(--stapel-color-error, #d64545); }
    .row { display: flex; gap: var(--stapel-space-2, 8px); align-items: center; margin-bottom: var(--stapel-space-1, 4px); }
    input[type="text"], input[type="number"], input[type="datetime-local"], select {
      background: var(--stapel-color-bg, #fff); color: inherit;
      border: 1px solid var(--stapel-color-border, #d7dbe3); border-radius: var(--stapel-radius-sm, 4px);
      padding: var(--stapel-space-1, 4px) var(--stapel-space-2, 8px); font: inherit;
    }
    input:focus-visible, select:focus-visible, button:focus-visible {
      outline: none; box-shadow: var(--stapel-focus-ring, 0 0 0 2px #fff, 0 0 0 4px #2a90d9);
    }
    .btn {
      cursor: pointer; border: 1px solid var(--stapel-color-border, #d7dbe3);
      background: var(--stapel-color-surface, #f7f8fa); color: inherit;
      border-radius: var(--stapel-radius-sm, 4px); padding: 2px var(--stapel-space-2, 8px);
    }
    .swatch { width: 20px; height: 20px; border-radius: 50%; border: 1px solid var(--stapel-color-border, #d7dbe3); }
    .nested { margin-left: var(--stapel-space-4, 16px); border-left: 2px solid var(--stapel-color-border, #d7dbe3); padding-left: var(--stapel-space-2, 8px); }
  `;

  override willUpdate(changed: Map<string, unknown>): void {
    if (changed.has("declaration")) this.seedData();
  }

  /** Load a config into the editor. */
  setConfig(config: FeatureConfig | null): void {
    this.data = {};
    this.manual.clear();
    if (config) for (const [k, v] of Object.entries(config)) if (k !== "type") this.data[k] = v;
    this.seedData();
    this.requestUpdate();
  }

  /** Seed per-field working copies (source B5: type-specific copy depth). */
  private seedData(): void {
    for (const f of this.declaration.fields) {
      const cur = this.data[f.name];
      if (["number_options", "string_options", "timestamp_array"].includes(f.kind)) {
        this.data[f.name] = Array.isArray(cur) ? [...cur] : [];
      } else if (["color_options", "select_options_with_default"].includes(f.kind)) {
        this.data[f.name] = Array.isArray(cur) ? (cur as Row[]).map((o) => ({ ...o })) : [];
      } else if (f.kind === "hierarchical_options") {
        this.data[f.name] = Array.isArray(cur) ? JSON.parse(JSON.stringify(cur)) : [];
      }
    }
  }

  private optionPrefix(): string {
    return this.translateMode === "all" && this.prefixName ? this.prefixName + "." : "";
  }

  private emit(): void {
    this.requestUpdate();
    this.onConfigChange?.(this.getConfig());
  }

  // ---- output assembly (LN-C04..C12) ------------------------------------- //

  getConfig(): FeatureConfig {
    const out: FeatureConfig = { type: this.typeSlug };
    for (const f of this.declaration.fields) {
      const v = this.fieldValue(f);
      if (f.kind === "max_selected_dropdown") {
        if (v !== undefined) out[f.name] = v; // LN-C12/B11: null (unlimited) IS emitted
      } else if (v !== undefined && v !== null && v !== "") {
        out[f.name] = v;
      }
    }
    return out;
  }

  private fieldValue(f: FormFieldDecl): unknown {
    const d = this.data[f.name];
    switch (f.kind) {
      case "number_options":
        return (d as unknown[] | undefined)?.filter((x) => x !== null && x !== undefined && x !== "");
      case "string_options":
        return (d as unknown[] | undefined)?.filter((x) => x !== null && x !== undefined && x !== "");
      case "timestamp_array":
        return (d as unknown[] | undefined)?.filter((x) => x !== null);
      case "color_options":
        return (d as Row[] | undefined)?.filter((o) => o.hex || o.label || o.simple);
      case "select_options_with_default":
        return (d as Row[] | undefined)?.filter((o) => o.value);
      case "hierarchical_options":
        return this.filterNodes((d as Row[]) || []);
      case "max_selected_dropdown": {
        const raw = this.data[f.name];
        if (raw === "" ) return null; // unlimited
        return raw === undefined ? undefined : parseInt(String(raw), 10);
      }
      case "checkbox":
        return d === undefined ? (f.default ?? false) : !!d;
      case "number": {
        if (d === undefined || d === "") return undefined;
        return f.params?.step === 1 ? parseInt(String(d), 10) : parseFloat(String(d));
      }
      default:
        return d === "" ? undefined : d;
    }
  }

  /** LN-C11: drop empty-value nodes (and their subtree); keep only truthy keys. */
  private filterNodes(nodes: Row[]): Row[] {
    const out: Row[] = [];
    for (const n of nodes) {
      if (!n.value) continue;
      const node: Row = { value: n.value };
      if (n.label) node.label = n.label;
      if (n.icon) node.icon = n.icon;
      if (n.childrenTitle) node.childrenTitle = n.childrenTitle;
      const kids = this.filterNodes((n.children as Row[]) || []);
      if (kids.length > 0) node.children = kids;
      out.push(node);
    }
    return out;
  }

  // ---- rendering --------------------------------------------------------- //

  override render(): TemplateResult {
    return html`${this.declaration.fields.map((f) => html`
      <div class="field">
        <label class="hd">${this.i18n.t(f.label_key)}${f.required ? html`<span class="req"> *</span>` : ""}</label>
        ${this.renderKind(f)}
      </div>`)}`;
  }

  private renderKind(f: FormFieldDecl): TemplateResult {
    switch (f.kind) {
      case "number": return this.renderNumber(f);
      case "text": case "translatable_text": return this.renderText(f);
      case "checkbox": return this.renderCheckbox(f);
      case "select": return this.renderSelect(f);
      case "timestamp": return this.renderTimestamp(f);
      case "number_options": return this.renderScalarList(f, "number");
      case "string_options": return this.renderScalarList(f, "text");
      case "timestamp_array": return this.renderTimestampArray(f);
      case "color_options": return this.renderColorOptions(f);
      case "select_options_with_default": return this.renderSelectOptions(f);
      case "max_selected_dropdown": return this.renderMaxSelected(f);
      case "hierarchical_options": return this.renderHierarchical(f);
      default: return this.renderText(f); // LN-C07 unknown-kind fallback -> text
    }
  }

  private renderNumber(f: FormFieldDecl): TemplateResult {
    const val = this.data[f.name] ?? f.default ?? "";
    return html`<input type="number" step=${f.params?.step ?? 1} .value=${String(val)}
      @input=${(e: Event) => { this.data[f.name] = (e.target as HTMLInputElement).value; this.emit(); }} />`;
  }

  private renderText(f: FormFieldDecl): TemplateResult {
    return html`<input type="text" .value=${String(this.data[f.name] ?? "")}
      placeholder=${f.params?.placeholder ?? ""}
      @input=${(e: Event) => { this.data[f.name] = (e.target as HTMLInputElement).value; this.emit(); }} />`;
  }

  private renderCheckbox(f: FormFieldDecl): TemplateResult {
    const checked = this.data[f.name] === undefined ? !!f.default : !!this.data[f.name];
    return html`<input type="checkbox" .checked=${checked}
      @change=${(e: Event) => { this.data[f.name] = (e.target as HTMLInputElement).checked; this.emit(); }} />`;
  }

  private renderSelect(f: FormFieldDecl): TemplateResult {
    const cur = this.data[f.name];
    const opts = (f.params?.options as InlineOption[]) || [];
    return html`<select @change=${(e: Event) => { this.data[f.name] = (e.target as HTMLSelectElement).value; this.emit(); }}>
      ${opts.map((o) => html`<option value=${o.value} ?selected=${cur === o.value || (!cur && f.default === o.value)}>${o.label}</option>`)}
    </select>`;
  }

  private renderTimestamp(f: FormFieldDecl): TemplateResult {
    const ts = this.data[f.name] as number | undefined;
    const val = ts != null ? new Date(ts * 1000).toISOString().slice(0, 16) : "";
    return html`<div class="row">
      <input type="datetime-local" .value=${val} @change=${(e: Event) => {
        const iv = (e.target as HTMLInputElement).value;
        this.data[f.name] = iv ? Math.floor(new Date(iv).getTime() / 1000) : undefined;
        this.emit();
      }} />
      <button type="button" class="btn" @click=${() => { this.data[f.name] = undefined; this.emit(); }}>${this.i18n.t("admin.attributes.clear")}</button>
    </div>`;
  }

  private moveRow(arr: unknown[], from: number, to: number): void {
    if (to < 0 || to >= arr.length || from === to) return;
    const [m] = arr.splice(from, 1);
    arr.splice(to, 0, m);
  }

  private reorderControls(arr: unknown[], idx: number): TemplateResult {
    return html`
      <button type="button" class="btn" aria-label=${this.i18n.t("admin.attributes.move_up")}
        ?disabled=${idx === 0} @click=${() => { this.moveRow(arr, idx, idx - 1); this.emit(); }}>↑</button>
      <button type="button" class="btn" aria-label=${this.i18n.t("admin.attributes.move_down")}
        ?disabled=${idx === arr.length - 1} @click=${() => { this.moveRow(arr, idx, idx + 1); this.emit(); }}>↓</button>`;
  }

  private renderScalarList(f: FormFieldDecl, inputType: "number" | "text"): TemplateResult {
    const arr = (this.data[f.name] as unknown[]) || [];
    return html`<div>
      ${arr.map((v, i) => html`<div class="row">
        <input type=${inputType} .value=${v == null ? "" : String(v)} @input=${(e: Event) => {
          const raw = (e.target as HTMLInputElement).value;
          arr[i] = inputType === "number" ? (raw === "" ? null : parseFloat(raw)) : raw;
          this.emit();
        }} />
        ${this.reorderControls(arr, i)}
        <button type="button" class="btn" @click=${() => { arr.splice(i, 1); this.emit(); }}>×</button>
      </div>`)}
      <button type="button" class="btn" @click=${() => { arr.push(inputType === "number" ? null : ""); this.requestUpdate(); }}>+ ${this.i18n.t("admin.attributes.add")}</button>
    </div>`;
  }

  private renderTimestampArray(f: FormFieldDecl): TemplateResult {
    const arr = (this.data[f.name] as (number | null)[]) || [];
    return html`<div>
      ${arr.map((ts, i) => html`<div class="row">
        <input type="datetime-local" .value=${ts != null ? new Date(ts * 1000).toISOString().slice(0, 16) : ""}
          @change=${(e: Event) => { const iv = (e.target as HTMLInputElement).value; arr[i] = iv ? Math.floor(new Date(iv).getTime() / 1000) : null; this.emit(); }} />
        ${this.reorderControls(arr, i)}
        <button type="button" class="btn" @click=${() => { arr.splice(i, 1); this.emit(); }}>×</button>
      </div>`)}
      <button type="button" class="btn" @click=${() => {
        const y = new Date().getUTCFullYear();
        arr.push(Math.floor(Date.UTC(y, 0, 1, 12, 0, 0) / 1000)); this.emit();
      }}>+ ${this.i18n.t("admin.attributes.add")}</button>
    </div>`;
  }

  private renderColorOptions(f: FormFieldDecl): TemplateResult {
    const arr = (this.data[f.name] as Row[]) || [];
    return html`<div>
      ${arr.map((o, i) => html`<div class="row">
        <span class="swatch" style=${isGradient(getColorStyle(o)) ? `background:${getColorStyle(o)}` : `background-color:${getColorStyle(o)}`}></span>
        <select @change=${(e: Event) => { o.simple = (e.target as HTMLSelectElement).value; this.emit(); }}>
          <option value="">${this.i18n.t("admin.attributes.simple_placeholder")}</option>
          ${SIMPLE_COLORS.map((c) => html`<option value=${c} ?selected=${o.simple === c}>${c}</option>`)}
        </select>
        <input type="text" placeholder="#RRGGBB" .value=${String(o.hex ?? "")} @input=${(e: Event) => { o.hex = (e.target as HTMLInputElement).value; this.emit(); }} />
        <input type="text" placeholder="label" .value=${String(o.label ?? "")} @input=${(e: Event) => { o.label = (e.target as HTMLInputElement).value; this.emit(); }} />
        ${this.reorderControls(arr, i)}
        <button type="button" class="btn" @click=${() => { arr.splice(i, 1); this.emit(); }}>×</button>
      </div>`)}
      <button type="button" class="btn" @click=${() => { arr.push({ hex: "", label: "", simple: "" }); this.requestUpdate(); }}>+ ${this.i18n.t("admin.attributes.add")}</button>
    </div>`;
  }

  private renderSelectOptions(f: FormFieldDecl): TemplateResult {
    const arr = (this.data[f.name] as Row[]) || [];
    const pfx = this.optionPrefix();
    return html`<div>
      ${arr.map((o, i) => {
        const key = `${f.name}_${i}`;
        return html`<div class="row">
          <input type="text" placeholder="label" .value=${String(o.label ?? "")} @input=${(e: Event) => {
            const label = (e.target as HTMLInputElement).value;
            o.label = label;
            if (!this.manual.has(key)) o.value = labelToValue(removePrefix(label, pfx)); // LN-C02
            this.emit();
          }} />
          <input type="text" placeholder="value" .value=${String(o.value ?? "")} @input=${(e: Event) => {
            o.value = (e.target as HTMLInputElement).value; this.manual.add(key); this.emit(); // LN-C03 latch
          }} />
          <label class="row"><input type="checkbox" .checked=${!!o.default} @change=${(e: Event) => { o.default = (e.target as HTMLInputElement).checked; this.emit(); }} /> def</label>
          ${this.reorderControls(arr, i)}
          <button type="button" class="btn" @click=${() => { arr.splice(i, 1); this.manual.delete(key); this.emit(); }}>×</button>
        </div>`;
      })}
      <button type="button" class="btn" @click=${() => { arr.push({ value: "", label: "", default: false }); this.requestUpdate(); }}>+ ${this.i18n.t("admin.attributes.add")}</button>
    </div>`;
  }

  private renderMaxSelected(f: FormFieldDecl): TemplateResult {
    const optionsData = (this.data["options"] as unknown[]) || [];
    const n = Math.max(optionsData.length, 1); // LN-C12
    const cur = this.data[f.name];
    const selected = cur !== undefined && cur !== null ? String(cur) : (f.default !== undefined ? String(f.default) : "1");
    return html`<select @change=${(e: Event) => { this.data[f.name] = (e.target as HTMLSelectElement).value; this.emit(); }}>
      ${Array.from({ length: n }, (_, k) => k + 1).map((i) => html`<option value=${String(i)} ?selected=${selected === String(i)}>${i}${i === 1 ? " " + this.i18n.t("admin.attributes.single_select") : ""}</option>`)}
      <option value="" ?selected=${selected === ""}>${this.i18n.t("admin.attributes.unlimited")}</option>
    </select>`;
  }

  private renderHierarchical(f: FormFieldDecl, nodes?: Row[], path = ""): TemplateResult {
    const arr = nodes ?? ((this.data[f.name] as Row[]) || []);
    const pfx = this.optionPrefix();
    return html`<div>
      ${arr.map((n, i) => {
        const np = path === "" ? String(i) : `${path}.${i}`;
        const key = `${f.name}_${np}`;
        const kids = (n.children as Row[]) || [];
        return html`<div>
          <div class="row">
            ${path ? html`<span>↳</span>` : ""}
            <input type="text" placeholder="label" .value=${String(n.label ?? "")} @input=${(e: Event) => {
              const label = (e.target as HTMLInputElement).value; n.label = label;
              if (!this.manual.has(key)) n.value = labelToValue(removePrefix(label, pfx)); this.emit();
            }} />
            <input type="text" placeholder="value" .value=${String(n.value ?? "")} @input=${(e: Event) => {
              n.value = (e.target as HTMLInputElement).value; this.manual.add(key); this.emit();
            }} />
            ${this.reorderControls(arr, i)}
            <button type="button" class="btn" @click=${() => { if (!n.children) n.children = []; (n.children as Row[]).push({ value: "", label: "", children: [] }); this.emit(); }}>+ child</button>
            <button type="button" class="btn" @click=${() => { arr.splice(i, 1); this.emit(); }}>×</button>
          </div>
          ${kids.length ? html`<div class="nested">${this.renderHierarchical(f, kids, np)}</div>` : ""}
        </div>`;
      })}
      ${path === "" ? html`<button type="button" class="btn" @click=${() => { arr.push({ value: "", label: "", children: [] }); this.requestUpdate(); }}>+ ${this.i18n.t("admin.attributes.add")}</button>` : ""}
    </div>`;
  }
}

if (typeof customElements !== "undefined" && !customElements.get("stapel-config-editor")) {
  customElements.define("stapel-config-editor", ConfigEditorElement);
}
