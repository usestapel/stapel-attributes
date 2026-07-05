// vitest on the *django* entry: importing index.ts (the admin bundle's entry)
// self-registers every custom element and installs the window global — the
// behaviour the Django admin page relies on. This is the counterpart to
// builds-lib.test.ts (which proves the lib entry does NOT do this on import).
import { describe, it, expect, beforeAll } from "vitest";

const EXPECTED_TYPES = [
  "bool", "date", "float", "header", "hex_color",
  "hierarchical_select", "int", "select", "string",
];
const EXPECTED_TAGS = [
  "stapel-config-editor", "stapel-dialog", "stapel-error",
  "stapel-ve-bool", "stapel-ve-date", "stapel-ve-header", "stapel-ve-hex-color",
  "stapel-ve-hierarchical", "stapel-ve-select", "stapel-ve-string-number",
];

interface Global {
  mountConfigEditor: unknown;
  createValueEditor: unknown;
  registerValueEditor: unknown;
  registeredValueEditorTypes(): string[];
}

beforeAll(async () => {
  await import("./index.js"); // runs the django entry's self-registration
});

describe("django entry — self-registering admin bundle", () => {
  it("defines every custom element at import", () => {
    for (const tag of EXPECTED_TAGS) expect(customElements.get(tag)).toBeDefined();
  });

  it("installs window.StapelAttributes with the mount API + parity registry", () => {
    const g = (globalThis as unknown as { StapelAttributes: Global }).StapelAttributes;
    expect(typeof g.mountConfigEditor).toBe("function");
    expect(typeof g.createValueEditor).toBe("function");
    expect(typeof g.registerValueEditor).toBe("function");
    // Same value-editor set the lib registers via defineElements (builds-lib.test.ts).
    expect(g.registeredValueEditorTypes()).toEqual(EXPECTED_TYPES);
  });
});
