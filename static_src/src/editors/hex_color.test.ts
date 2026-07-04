import { describe, it, expect, beforeEach } from "vitest";
import "./hex_color.js";
import { HexColorValueEditor } from "./hex_color.js";
import { I18n } from "../runtime/i18n.js";
import type { FeatureConfig } from "../types.js";

const i18n = new I18n("en", { en: { "admin.attributes.required": "This field is required" } });

function make(config: Partial<FeatureConfig>, mandatory = false): HexColorValueEditor {
  const el = new HexColorValueEditor();
  el.config = { type: "hex_color", ...config };
  el.mandatory = mandatory;
  el.i18n = i18n;
  document.body.appendChild(el);
  return el;
}

describe("HexColorValueEditor (LN-V11..V15)", () => {
  beforeEach(() => (document.body.innerHTML = ""));

  it("empty options -> full palette minus 'custom' (LN-V12)", async () => {
    const el = make({ options: [] });
    await el.updateComplete;
    const names = [...el.shadowRoot!.querySelectorAll(".name")].map((n) => n.textContent);
    expect(names).toContain("Black");
    expect(names.map((s) => s?.toLowerCase())).not.toContain("custom");
  });

  it("selecting copies ONLY config-present fields (LN-V11)", async () => {
    const el = make({ options: [{ simple: "red" }, { simple: "blue", hex: "#0000FF", label: "Blue" }] });
    await el.updateComplete;
    (el.shadowRoot!.querySelectorAll("button.circle")[0] as HTMLButtonElement).click();
    expect(el.getValue()).toEqual({ type: "hex_color", value: { simple: "red" } }); // no hex/label synthesized
  });

  it("toggle off returns null; hex match is case-insensitive (LN-V14)", async () => {
    const el = make({ options: [{ simple: "x", hex: "#AABBCC" }] });
    el.setValue({ type: "hex_color", value: { simple: "x", hex: "#aabbcc" } });
    await el.updateComplete;
    // exact match (case-insensitive) -> shows selected; clicking toggles off
    const circle = el.shadowRoot!.querySelector("button.circle") as HTMLButtonElement;
    expect(circle.classList.contains("circle--selected")).toBe(true);
    circle.click();
    expect(el.getValue()).toBeNull();
  });

  it("single explicit option + !allowCustom auto-selects & locks (LN-V13)", async () => {
    const el = make({ options: [{ simple: "only" }], allowCustom: false });
    await el.updateComplete;
    expect(el.getValue()).toEqual({ type: "hex_color", value: { simple: "only" } });
    expect((el.shadowRoot!.querySelector("button.circle") as HTMLButtonElement).disabled).toBe(true);
  });

  it("invalid hex fails validation (LN-V15)", () => {
    const el = make({ allowCustom: true });
    el.setValue({ type: "hex_color", value: { simple: "custom", hex: "#XYZ" } });
    expect(el.validate()).toContain("Invalid hex color format");
  });
});
