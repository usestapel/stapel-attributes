import { describe, it, expect, beforeEach } from "vitest";
import "./select.js";
import { SelectValueEditor } from "./select.js";
import { I18n } from "../runtime/i18n.js";
import type { FeatureConfig } from "../types.js";

const i18n = new I18n("en", {
  en: {
    "admin.attributes.required": "This field is required",
    "admin.attributes.select_placeholder": "-- Select --",
    "admin.attributes.add": "-- Add --",
  },
});

function make(config: Partial<FeatureConfig>, mandatory = false): SelectValueEditor {
  const el = new SelectValueEditor();
  el.config = { type: "select", uiStyle: "chips", options: [{ value: "a" }, { value: "b" }, { value: "c" }], ...config };
  el.mandatory = mandatory;
  el.i18n = i18n;
  document.body.appendChild(el);
  return el;
}

async function chip(el: SelectValueEditor, idx: number) {
  await el.updateComplete;
  (el.shadowRoot!.querySelectorAll("button.chip")[idx] as HTMLButtonElement).click();
  await el.updateComplete;
}

describe("SelectValueEditor (LN-V21..V24)", () => {
  beforeEach(() => (document.body.innerHTML = ""));

  it("DTO value is always an array; empty selection -> null (LN-V21)", async () => {
    const el = make({});
    await chip(el, 0);
    expect(el.getValue()).toEqual({ type: "select", value: ["a"] });
    await chip(el, 0); // toggle off
    expect(el.getValue()).toBeNull();
  });

  it("maxSelected===1 replaces (single-select, LN-V22)", async () => {
    const el = make({ maxSelected: 1 });
    await chip(el, 0);
    await chip(el, 1);
    expect(el.getValue()).toEqual({ type: "select", value: ["b"] });
  });

  it("at maxSelected cap, further selects are blocked (LN-V22)", async () => {
    const el = make({ maxSelected: 2 });
    await chip(el, 0);
    await chip(el, 1);
    await chip(el, 2); // blocked
    expect(el.getValue()).toEqual({ type: "select", value: ["a", "b"] });
  });

  it("validate: min enforced only when count>0; required on empty (LN-V23)", async () => {
    const el = make({ minSelected: 2 }, true);
    await el.updateComplete;
    expect(el.validate()).toEqual(["This field is required"]); // empty + mandatory
    await chip(el, 0);
    expect(el.validate()).toEqual(["Select at least 2 option(s)"]);
  });
});
