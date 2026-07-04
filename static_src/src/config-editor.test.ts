import { describe, it, expect, beforeEach } from "vitest";
import "./config-editor.js";
import { ConfigEditorElement } from "./config-editor.js";
import { I18n } from "./runtime/i18n.js";
import type { TypeDecl } from "./types.js";

const i18n = new I18n("en", {
  en: {
    "admin.attributes.add": "Add", "admin.attributes.clear": "Clear",
    "admin.attributes.unlimited": "Unlimited", "admin.attributes.single_select": "(single)",
    "admin.attributes.simple_placeholder": "-- Simple --",
  },
});

const SELECT_DECL: TypeDecl = {
  label_key: "admin.attributes.type.select",
  fields: [
    { name: "options", kind: "select_options_with_default", label_key: "k.options" },
    { name: "minSelected", kind: "number", label_key: "k.min", default: 0, params: { step: 1 } },
    { name: "maxSelected", kind: "max_selected_dropdown", label_key: "k.max", default: 1 },
    { name: "lockUserInput", kind: "checkbox", label_key: "k.lock" },
  ],
};

function make(decl: TypeDecl, slug: string): ConfigEditorElement {
  const el = new ConfigEditorElement();
  el.declaration = decl;
  el.typeSlug = slug;
  el.i18n = i18n;
  document.body.appendChild(el);
  return el;
}

describe("ConfigEditorElement output filtering (LN-C)", () => {
  beforeEach(() => (document.body.innerHTML = ""));

  it("select_options keeps truthy-value rows; label/default pass through (LN-C10, LN-B02)", async () => {
    const el = make(SELECT_DECL, "select");
    el.setConfig({
      type: "select",
      options: [
        { value: "a", label: "A", default: true },
        { value: "", label: "empty" }, // dropped: no value
        { value: "b", label: "", default: true }, // both defaults allowed (LN-B02)
      ],
      maxSelected: "", // unlimited
    });
    await el.updateComplete;
    const cfg = el.getConfig();
    expect(cfg.options).toEqual([
      { value: "a", label: "A", default: true },
      { value: "b", label: "", default: true }, // multiple defaults kept
    ]);
    expect(cfg.maxSelected).toBeNull(); // LN-C12/B11: null emitted for unlimited
    expect("minSelected" in cfg).toBe(false); // default 0 -> not emitted (empty/undefined)
  });

  it("max_selected emits parsed int when a count is chosen", async () => {
    const el = make(SELECT_DECL, "select");
    el.setConfig({ type: "select", options: [{ value: "a" }, { value: "b" }], maxSelected: 2 });
    await el.updateComplete;
    expect(el.getConfig().maxSelected).toBe(2);
  });

  it("hierarchical drops empty-value nodes with their subtree; keeps truthy keys (LN-C11)", async () => {
    const decl: TypeDecl = { label_key: "k", fields: [{ name: "options", kind: "hierarchical_options", label_key: "k.o" }] };
    const el = make(decl, "hierarchical_select");
    el.setConfig({
      type: "hierarchical_select",
      options: [
        { value: "", label: "orphan", children: [{ value: "lost", label: "x" }] }, // whole subtree dropped
        { value: "keep", label: "", icon: "", children: [{ value: "child", label: "C" }] },
      ],
    });
    await el.updateComplete;
    expect(el.getConfig().options).toEqual([
      { value: "keep", children: [{ value: "child", label: "C" }] }, // empty label/icon stripped, child kept
    ]);
  });

  it("scalar options filter empties (LN-C06/07)", async () => {
    const decl: TypeDecl = { label_key: "k", fields: [{ name: "options", kind: "number_options", label_key: "k.o", params: { itemType: "number" } }] };
    const el = make(decl, "int");
    el.setConfig({ type: "int", options: [1, null as unknown as number, 2] });
    await el.updateComplete;
    expect(el.getConfig().options).toEqual([1, 2]);
  });
});

describe("ConfigEditor option-key generation (LN-C02/C03)", () => {
  beforeEach(() => (document.body.innerHTML = ""));

  it("value auto-derives from label until value is manually edited", async () => {
    const el = make(SELECT_DECL, "select");
    el.setConfig({ type: "select", options: [{ value: "", label: "" }] });
    await el.updateComplete;
    const [labelInput, valueInput] = el.shadowRoot!.querySelectorAll("input[type=text]");
    (labelInput as HTMLInputElement).value = "Hello World";
    labelInput.dispatchEvent(new Event("input"));
    await el.updateComplete;
    expect(el.getConfig().options).toEqual([{ value: "hello_world", label: "Hello World" }]);
    // now manually edit the value -> latched; further label edits don't overwrite
    (valueInput as HTMLInputElement).value = "custom_key";
    valueInput.dispatchEvent(new Event("input"));
    (labelInput as HTMLInputElement).value = "Changed";
    labelInput.dispatchEvent(new Event("input"));
    await el.updateComplete;
    expect((el.getConfig().options as any)[0].value).toBe("custom_key");
  });
});
