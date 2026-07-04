import { describe, it, expect, beforeEach } from "vitest";
import "./date.js";
import { DateValueEditor } from "./date.js";
import { I18n } from "../runtime/i18n.js";
import type { FeatureConfig } from "../types.js";

const i18n = new I18n("en", { en: { "admin.attributes.required": "This field is required" } });

function make(config: Partial<FeatureConfig>, mandatory = false): DateValueEditor {
  const el = new DateValueEditor();
  el.config = { type: "date", ...config };
  el.mandatory = mandatory;
  el.i18n = i18n;
  document.body.appendChild(el);
  return el;
}

async function change(el: DateValueEditor, raw: string) {
  await el.updateComplete;
  const input = el.shadowRoot!.querySelector("input") as HTMLInputElement;
  input.value = raw;
  input.dispatchEvent(new Event("change"));
  await el.updateComplete;
}

describe("DateValueEditor (LN-V06..V09)", () => {
  beforeEach(() => (document.body.innerHTML = ""));

  it("stores Unix seconds; date precision round-trips via UTC (LN-V07)", async () => {
    const el = make({ precision: "date" });
    await change(el, "2026-07-04");
    const ts = (el.getValue() as any).value;
    expect(ts).toBe(Math.floor(Date.UTC(2026, 6, 4) / 1000));
    expect(el.getValue()!.type).toBe("date");
  });

  it("year precision uses local Jan 1 (LN-B08 preserved)", async () => {
    const el = make({ precision: "year" });
    await change(el, "2030");
    const ts = (el.getValue() as any).value;
    expect(ts).toBe(Math.floor(new Date(2030, 0, 1).getTime() / 1000)); // local
    const input = el.shadowRoot!.querySelector("input") as HTMLInputElement;
    expect(input.type).toBe("number");
  });

  it("empty input -> null", async () => {
    const el = make({ precision: "date" });
    await change(el, "2026-01-01");
    expect(el.getValue()).not.toBeNull();
    await change(el, "");
    expect(el.getValue()).toBeNull();
  });

  it("validate min/max/future/past (LN-V09)", async () => {
    const min = Math.floor(Date.UTC(2026, 0, 1) / 1000);
    const el = make({ precision: "date", minDate: min, allowFuture: false });
    await change(el, "2025-06-01"); // before min
    expect(el.validate()).toContain("Date is too early");
    // a far-future date -> future not allowed
    await change(el, "2999-01-01");
    expect(el.validate()).toContain("Future dates not allowed");
  });
});
