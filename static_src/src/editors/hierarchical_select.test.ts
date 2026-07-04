import { describe, it, expect, beforeEach } from "vitest";
import "./hierarchical_select.js";
import { HierarchicalSelectValueEditor } from "./hierarchical_select.js";
import { I18n } from "../runtime/i18n.js";
import type { FeatureConfig } from "../types.js";

const i18n = new I18n("en", {
  en: { "admin.attributes.required": "This field is required", "admin.attributes.select_placeholder": "-- Select --" },
});

const TREE = [
  { value: "veh", label: "Vehicles", children: [
    { value: "car", label: "Car", children: [{ value: "sedan", label: "Sedan" }, { value: "suv", label: "SUV" }] },
    { value: "bike", label: "Bike" },
  ] },
  { value: "prop", label: "Property" },
];

function make(config: Partial<FeatureConfig>, mandatory = false): HierarchicalSelectValueEditor {
  const el = new HierarchicalSelectValueEditor();
  el.config = { type: "hierarchical_select", options: TREE, ...config };
  el.mandatory = mandatory;
  el.i18n = i18n;
  document.body.appendChild(el);
  return el;
}

async function pick(el: HierarchicalSelectValueEditor, levelIdx: number, value: string) {
  await el.updateComplete;
  const sel = el.shadowRoot!.querySelectorAll("select")[levelIdx] as HTMLSelectElement;
  sel.value = value;
  sel.dispatchEvent(new Event("change"));
  await el.updateComplete;
}

describe("HierarchicalSelectValueEditor (LN-V16..V20)", () => {
  beforeEach(() => (document.body.innerHTML = ""));

  it("DTO is the ordered path array; empty -> null (LN-V16)", async () => {
    const el = make({});
    await pick(el, 0, "veh");
    await pick(el, 1, "car");
    await pick(el, 2, "suv");
    expect(el.getValue()).toEqual({ type: "hierarchical_select", value: ["veh", "car", "suv"] });
  });

  it("changing a parent truncates all descendants (LN-V19)", async () => {
    const el = make({});
    await pick(el, 0, "veh");
    await pick(el, 1, "car");
    await pick(el, 2, "sedan");
    expect(el.getValue()!.value).toEqual(["veh", "car", "sedan"]);
    await pick(el, 1, "bike"); // change level 1 -> drop level 2
    expect(el.getValue()!.value).toEqual(["veh", "bike"]);
  });

  it("single-option level auto-selects & locks (LN-V17)", async () => {
    const single = [{ value: "root", children: [{ value: "a" }, { value: "b" }] }];
    const el = make({ options: single });
    await el.updateComplete;
    // root is the only option -> auto-selected into the path
    expect((el.getValue()!.value as string[])[0]).toBe("root");
    expect((el.shadowRoot!.querySelectorAll("select")[0] as HTMLSelectElement).disabled).toBe(true);
  });

  it("validate: required at depth 0; minDepth enforced (LN-V20)", async () => {
    const el = make({ minDepth: 2 }, true);
    await el.updateComplete;
    expect(el.validate()).toEqual(["This field is required"]);
    await pick(el, 0, "prop"); // depth 1, below minDepth 2
    expect(el.validate()).toEqual(["Select at least 2 level(s)"]);
  });
});
