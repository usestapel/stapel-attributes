import { describe, it, expect } from "vitest";
import "./header.js";
import { HeaderValueEditor } from "./header.js";
import { I18n } from "../runtime/i18n.js";

const i18n = new I18n("en", {});

describe("HeaderValueEditor (LN-V10)", () => {
  it("is display-only: never a value, empty validation", async () => {
    const el = new HeaderValueEditor();
    el.config = { type: "header", style: "l", title: "General" };
    el.i18n = i18n;
    el.mandatory = true; // even mandatory -> no value, no error
    document.body.appendChild(el);
    await el.updateComplete;
    expect(el.getValue()).toBeNull();
    expect(el.validate()).toEqual([]);
    expect(el.shadowRoot!.querySelector(".ve__header")!.textContent).toBe("General");
  });
});
