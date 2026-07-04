import { describe, it, expect, beforeEach } from "vitest";
import "./string_number.js";
import { StringNumberValueEditor } from "./string_number.js";
import { I18n } from "../runtime/i18n.js";
import type { FeatureConfig } from "../types.js";

const i18n = new I18n("en", {
  en: {
    "admin.attributes.required": "This field is required",
    "admin.attributes.select_placeholder": "-- Select --",
    "admin.attributes.other": "Other...",
  },
});

function make(config: Partial<FeatureConfig>, mandatory = false): StringNumberValueEditor {
  const el = new StringNumberValueEditor();
  el.config = { type: "string", ...config };
  el.mandatory = mandatory;
  el.i18n = i18n;
  document.body.appendChild(el);
  return el;
}

async function type(el: StringNumberValueEditor, raw: string) {
  await el.updateComplete;
  const input = el.shadowRoot!.querySelector("input") as HTMLInputElement;
  input.value = raw;
  input.dispatchEvent(new Event("input"));
  await el.updateComplete;
}

describe("StringNumberValueEditor (LN-V25..V30)", () => {
  beforeEach(() => (document.body.innerHTML = ""));

  it("int parses via parseInt, NaN->null (LN-V26)", async () => {
    const el = make({ type: "int" });
    await type(el, "42");
    expect(el.getValue()).toEqual({ type: "int", value: 42 });
    await type(el, "abc");
    expect(el.getValue()).toBeNull();
  });

  it("float parses via parseFloat; whitespace-only -> null", async () => {
    const el = make({ type: "float" });
    await type(el, "3.14");
    expect(el.getValue()).toEqual({ type: "float", value: 3.14 });
    await type(el, "   ");
    expect(el.getValue()).toBeNull();
  });

  it("string passes through raw (trimmed empty -> null)", async () => {
    const el = make({ type: "string" });
    await type(el, "hello");
    expect(el.getValue()).toEqual({ type: "string", value: "hello" });
    await type(el, "");
    expect(el.getValue()).toBeNull();
  });

  it("int min/max validation (LN-V30)", async () => {
    const el = make({ type: "int", min: 5, max: 10 });
    await type(el, "3");
    expect(el.validate()).toEqual(["Minimum value is 5"]);
    await type(el, "12");
    expect(el.validate()).toEqual(["Maximum value is 10"]);
    await type(el, "7");
    expect(el.validate()).toEqual([]);
  });

  it("string minLength/maxLength/pattern (LN-V30)", async () => {
    const el = make({ type: "string", minLength: 3, pattern: "^[a-z]+$" });
    await type(el, "AB");
    const errs = el.validate();
    expect(errs).toContain("Minimum length is 3");
    expect(errs).toContain("Invalid format");
  });

  it("options + allowCustom default on -> dropdown has Other (LN-V27)", async () => {
    const el = make({ type: "string", options: ["a", "b"] });
    await el.updateComplete;
    const opts = [...el.shadowRoot!.querySelectorAll("option")].map((o) => o.value);
    expect(opts).toContain("__custom__");
  });

  it("single option + !allowCustom auto-selects & sets value (LN-V28)", async () => {
    const el = make({ type: "string", options: ["only"], allowCustom: false });
    await el.updateComplete;
    expect(el.getValue()).toEqual({ type: "string", value: "only" });
    const sel = el.shadowRoot!.querySelector("select") as HTMLSelectElement;
    expect(sel.disabled).toBe(true);
  });
});
