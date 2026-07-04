import { describe, it, expect } from "vitest";
import {
  registerValueEditor,
  resolveValueEditor,
  registerConfigWidget,
  resolveConfigWidget,
  registeredValueEditorTypes,
  installGlobal,
} from "./registry.js";
import { I18n } from "./runtime/i18n.js";

const i18n = new I18n("en", { en: { "admin.attributes.unsupported_type": "Unsupported type: {type}" } });

describe("registries (docs §4 seam)", () => {
  it("registered value-editor resolves; later registration wins (merge)", () => {
    const a = () => document.createElement("div");
    const b = () => document.createElement("span");
    registerValueEditor("demo", a);
    expect(resolveValueEditor("demo")).toBe(a);
    registerValueEditor("demo", b); // override
    expect(resolveValueEditor("demo")).toBe(b);
    expect(registeredValueEditorTypes()).toContain("demo");
  });

  it("unknown type falls back to UnsupportedEditor (LN-V03)", () => {
    const el = resolveValueEditor("nope")({ config: { type: "nope", value: null } as any, i18n });
    expect(el.className).toContain("value-editor--unsupported");
    expect(el.textContent).toBe("Unsupported type: nope");
    expect((el as any).getValue()).toBeNull();
  });

  it("config widgets register + resolve by kind; unknown kind -> undefined", () => {
    const w = () => document.createElement("input");
    registerConfigWidget("exotic", w);
    expect(resolveConfigWidget("exotic")).toBe(w);
    expect(resolveConfigWidget("unknown_kind")).toBeUndefined();
  });

  it("installGlobal exposes window.StapelAttributes", () => {
    installGlobal();
    expect(typeof (window as any).StapelAttributes.registerValueEditor).toBe("function");
  });
});
