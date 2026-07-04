import { describe, it, expect, beforeEach } from "vitest";
import "./bool.js";
import { BoolValueEditor } from "./bool.js";
import { I18n } from "../runtime/i18n.js";
import type { FeatureConfig } from "../types.js";

const i18n = new I18n("en", { en: { "admin.attributes.required": "This field is required" } });

function make(mandatory: boolean, config: Partial<FeatureConfig> = {}): BoolValueEditor {
  const el = new BoolValueEditor();
  el.config = { type: "bool", ...config };
  el.mandatory = mandatory;
  el.i18n = i18n;
  document.body.appendChild(el);
  return el;
}

async function tick(el: BoolValueEditor) {
  await el.updateComplete;
}

describe("BoolValueEditor (LN-V04/V05)", () => {
  beforeEach(() => (document.body.innerHTML = ""));

  it("mandatory renders two chips; selecting emits {type:bool,value}", async () => {
    let last: unknown = undefined;
    const el = make(true, { trueLabel: "Aye", falseLabel: "Nay" });
    el.onValueChange = (dto) => (last = dto);
    await tick(el);
    const chips = el.shadowRoot!.querySelectorAll("button.chip");
    expect([...chips].map((c) => c.textContent)).toEqual(["Aye", "Nay"]);
    (chips[0] as HTMLButtonElement).click();
    expect(el.getValue()).toEqual({ type: "bool", value: true });
    expect(last).toEqual({ type: "bool", value: true });
  });

  it("mandatory re-click does NOT deselect (LN-V05)", async () => {
    const el = make(true);
    await tick(el);
    const yes = el.shadowRoot!.querySelector("button.chip") as HTMLButtonElement;
    yes.click();
    expect(el.getValue()).toEqual({ type: "bool", value: true });
    await tick(el);
    (el.shadowRoot!.querySelector("button.chip") as HTMLButtonElement).click();
    expect(el.getValue()).toEqual({ type: "bool", value: true }); // still set
  });

  it("optional checkbox: checked->true, unchecked->null (never false)", async () => {
    const el = make(false);
    await tick(el);
    const cb = el.shadowRoot!.querySelector("input[type=checkbox]") as HTMLInputElement;
    cb.checked = true;
    cb.dispatchEvent(new Event("change"));
    expect(el.getValue()).toEqual({ type: "bool", value: true });
    await tick(el);
    const cb2 = el.shadowRoot!.querySelector("input[type=checkbox]") as HTMLInputElement;
    cb2.checked = false;
    cb2.dispatchEvent(new Event("change"));
    expect(el.getValue()).toBeNull(); // null, not {value:false}
  });

  it("mandatory empty fails validation with required (strict ===null)", async () => {
    const el = make(true);
    await tick(el);
    expect(el.validate()).toEqual(["This field is required"]);
  });
});
