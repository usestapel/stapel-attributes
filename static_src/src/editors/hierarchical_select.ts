// hierarchical_select value-editor — 1:1 port of hierarchical_select_editor.js
// (LOGIC-NOTES LN-V16..V20). Cascading dropdowns; single-option levels are
// auto-selected & locked; changing a parent truncates all descendants; DTO is
// the ordered array of node values. The "incomplete selection" branch is a
// no-op (LN-B14) — partial/branch selections are allowed.
import { html, type TemplateResult } from "lit";
import { state } from "lit/decorators.js";
import { ValueEditorElement, valueEditorFactory } from "./base.js";
import { registerValueEditor } from "../registry.js";

interface HNode { value: string; label?: string; children?: HNode[]; childrenTitle?: string; }

export class HierarchicalSelectValueEditor extends ValueEditorElement {
  @state() private _path: string[] = [];
  private _locked = new Set<number>();
  private _autoRan = false;

  private get options(): HNode[] {
    return (this.config.options as HNode[]) || [];
  }

  protected override onValueUpdated(): void {
    this._path = this._value && Array.isArray(this._value.value) ? [...(this._value.value as string[])] : [];
    this._autoRan = false; // re-run auto-select against the new value
  }

  protected override willUpdate(): void {
    if (!this._autoRan) {
      this._autoRan = true;
      this.autoSelectSingleOptions();
      this.setValueFromPath();
    }
  }

  private autoSelectSingleOptions(): void {
    this._locked.clear();
    let current = this.options;
    let depth = 0;
    while (current && current.length > 0) {
      if (current.length === 1) {
        const single = current[0];
        this._path[depth] = single.value;
        this._locked.add(depth);
        if (single.children && single.children.length > 0) { current = single.children; depth++; }
        else break;
      } else {
        const sel = this._path[depth];
        if (sel) {
          const opt = current.find((o) => o.value === sel);
          if (opt && opt.children && opt.children.length > 0) { current = opt.children; depth++; continue; }
        }
        break;
      }
    }
  }

  private autoSelectChildrenFromDepth(startDepth: number): void {
    for (const level of [...this._locked]) if (level >= startDepth) this._locked.delete(level);
    let current = this.options;
    let depth = 0;
    while (depth < startDepth && current.length > 0) {
      const sel = this._path[depth];
      if (!sel) return;
      const opt = current.find((o) => o.value === sel);
      if (!opt || !opt.children) return;
      current = opt.children;
      depth++;
    }
    while (current && current.length === 1) {
      const single = current[0];
      this._path[depth] = single.value;
      this._locked.add(depth);
      if (single.children && single.children.length > 0) { current = single.children; depth++; }
      else break;
    }
  }

  private onLevelChange(depth: number, value: string): void {
    if (value === "") {
      this._path = this._path.slice(0, depth);
    } else {
      this._path = this._path.slice(0, depth);
      this._path[depth] = value;
    }
    this.autoSelectChildrenFromDepth(depth + 1);
    this.setValueFromPath();
    this.requestUpdate();
  }

  private setValueFromPath(): void {
    this._value = this._path.length === 0 ? null : { type: "hierarchical_select", value: [...this._path] };
    this.emit();
  }

  // LN-V20: required at depth 0; min/max depth; incomplete-selection is a no-op.
  override validate(): string[] {
    this._errors = [];
    const depth = this._path.length;
    if (this.mandatory && depth === 0) {
      this._errors.push(this.i18n.t("admin.attributes.required"));
      return this._errors;
    }
    const minDepth = (this.config.minDepth as number) || 1;
    const maxDepth = this.config.maxDepth as number | undefined;
    if (depth > 0 && depth < minDepth) this._errors.push(`Select at least ${minDepth} level(s)`);
    if (maxDepth && depth > maxDepth) this._errors.push(`Select at most ${maxDepth} level(s)`);
    return this._errors;
  }

  protected renderInput(): TemplateResult {
    const levels: TemplateResult[] = [];
    let current = this.options;
    let title: string | null = null;
    let depth = 0;
    while (current && current.length > 0) {
      const selected = this._path[depth];
      const locked = this._locked.has(depth);
      const d = depth;
      const opts = current;
      levels.push(html`
        <div class="ve__row" style="flex-direction:column;align-items:flex-start">
          ${title ? html`<span style="color:var(--stapel-color-text-muted,#6b7280)">${title}</span>` : ""}
          <select ?disabled=${locked} .value=${selected ?? ""}
            @change=${(e: Event) => this.onLevelChange(d, (e.target as HTMLSelectElement).value)}>
            ${locked ? "" : html`<option value="">${this.i18n.t("admin.attributes.select_placeholder")}</option>`}
            ${opts.map((o) => html`<option value=${o.value}>${o.label ?? o.value}</option>`)}
          </select>
        </div>`);
      if (selected) {
        const opt = current.find((o) => o.value === selected);
        if (opt && opt.children && opt.children.length > 0) {
          current = opt.children;
          title = opt.childrenTitle ?? null;
          depth++;
          continue;
        }
      }
      break;
    }
    return html`<div class="ve__row" style="flex-direction:column;align-items:stretch">${levels}</div>`;
  }
}

// @stapel-auto-define:start — django self-registers here; the lib build strips
// this block (strip-auto-define.mjs) so lib imports are side-effect-free.
if (typeof customElements !== "undefined" && !customElements.get("stapel-ve-hierarchical")) {
  customElements.define("stapel-ve-hierarchical", HierarchicalSelectValueEditor);
}
registerValueEditor("hierarchical_select", valueEditorFactory(HierarchicalSelectValueEditor));
// @stapel-auto-define:end

