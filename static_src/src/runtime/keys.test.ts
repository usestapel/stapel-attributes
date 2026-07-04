import { describe, it, expect } from "vitest";
import {
  labelToValue,
  slugToTranslationKey,
  formatSlug,
  addPrefix,
  removePrefix,
  addPrefixToOptions,
} from "./keys.js";

describe("labelToValue (LN-C01 / LN-R09)", () => {
  it("lowercases, collapses whitespace runs to _, strips non letter/number/_", () => {
    expect(labelToValue("Hello World")).toBe("hello_world");
    expect(labelToValue("A  B\tC")).toBe("a_b_c");
    expect(labelToValue("Price ($)!")).toBe("price_");
  });
  it("is Unicode-aware — non-Latin letters survive (LN-C01)", () => {
    expect(labelToValue("Красный Цвет")).toBe("красный_цвет");
    expect(labelToValue("日本語")).toBe("日本語");
  });
  it("LN-B09: no dedup, no repeated-_ collapse, no edge trim, all-symbol -> ''", () => {
    expect(labelToValue("!!!")).toBe(""); // all symbols
    expect(labelToValue("a__b")).toBe("a__b"); // repeated _ kept
    expect(labelToValue("  x  ")).toBe("_x_"); // leading/trailing not trimmed
  });
});

describe("slugToTranslationKey (LN-R06)", () => {
  it("prefixes feature. and collapses whitespace/hyphen runs to _", () => {
    expect(slugToTranslationKey("Brand-New Thing")).toBe("feature.brand_new_thing");
    expect(slugToTranslationKey("color")).toBe("feature.color");
  });
});

describe("formatSlug (LN-R08)", () => {
  it("lowercases, spaces->_, strips non [a-z0-9_-]", () => {
    expect(formatSlug("My Feature!")).toBe("my_feature");
    expect(formatSlug("keep-this_1")).toBe("keep-this_1");
  });
});

describe("add/removePrefix (LN-C18)", () => {
  it("adds only when not already prefixed; empty label/prefix no-op", () => {
    expect(addPrefix("color", "feature.x.")).toBe("feature.x.color");
    expect(addPrefix("feature.x.color", "feature.x.")).toBe("feature.x.color");
    expect(addPrefix("", "feature.x.")).toBe("");
    expect(addPrefix("color", "")).toBe("color");
  });
  it("removes only when present", () => {
    expect(removePrefix("feature.x.color", "feature.x.")).toBe("color");
    expect(removePrefix("color", "feature.x.")).toBe("color");
  });
});

describe("addPrefixToOptions — P1 (LN-R05)", () => {
  it("prefixes label only (not value/icon), recurses children, idempotent", () => {
    const opts = [
      { value: "red", label: "red", icon: "r.png" },
      { value: "grp", label: "grp", children: [{ value: "sub", label: "sub" }] },
      { value: "keep", label: "feature.f.keep" }, // already prefixed
    ];
    addPrefixToOptions(opts, "feature.f.");
    expect(opts[0]).toEqual({ value: "red", label: "feature.f.red", icon: "r.png" });
    expect((opts[1].children as any)[0].label).toBe("feature.f.sub");
    expect(opts[2].label).toBe("feature.f.keep"); // not double-prefixed
    // idempotent: second pass changes nothing
    const snapshot = JSON.stringify(opts);
    addPrefixToOptions(opts, "feature.f.");
    expect(JSON.stringify(opts)).toBe(snapshot);
  });
});

describe("i18n merge behaviour is covered in i18n.test.ts", () => {
  it("placeholder", () => expect(true).toBe(true));
});
