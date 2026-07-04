import { describe, it, expect } from "vitest";
import { I18n } from "./i18n.js";

const messages = {
  en: { "a.hello": "Hello {name}", "a.bye": "Bye" },
  ru: { "a.hello": "Привет {name}" }, // partial: no a.bye
  de: {}, // empty host locale
};

describe("I18n (LN-R04, decision 2)", () => {
  it("interpolates {param}", () => {
    expect(new I18n("en", messages).t("a.hello", { name: "Ann" })).toBe("Hello Ann");
  });
  it("falls back to the key for unknown keys", () => {
    expect(new I18n("en", messages).t("a.missing")).toBe("a.missing");
  });
  it("partial locale merges over en base (no fork)", () => {
    const ru = new I18n("ru", messages);
    expect(ru.t("a.hello", { name: "Аня" })).toBe("Привет Аня"); // ru override
    expect(ru.t("a.bye")).toBe("Bye"); // inherited from en
  });
  it("empty/unknown locale falls back entirely to en", () => {
    expect(new I18n("de", messages).t("a.bye")).toBe("Bye");
    expect(new I18n("fr", messages).t("a.bye")).toBe("Bye");
  });
});
