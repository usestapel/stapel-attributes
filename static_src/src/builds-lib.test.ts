// vitest on the *lib* build: the externalized-Lit ESM bundle must be
// side-effect-free on import — no custom elements defined, no value-editors
// registered — until the host calls defineElements(). Proves the strip plugin
// removed every `@stapel-auto-define` tail and that defineElements() is the sole
// registrar. The artifact is built by vitest.globalSetup.mjs (Node env).
import { describe, it, expect, beforeAll } from "vitest";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";

const OUT = resolve(__dirname, "..", "dist", "_libtest.mjs");

// Parity with what the django bundle self-registers (builds-django.test.ts
// asserts the same sets against the django side).
const EXPECTED_TYPES = [
  "bool", "date", "float", "header", "hex_color",
  "hierarchical_select", "int", "select", "string",
];
const EXPECTED_TAGS = [
  "stapel-config-editor", "stapel-dialog", "stapel-error",
  "stapel-ve-bool", "stapel-ve-date", "stapel-ve-header", "stapel-ve-hex-color",
  "stapel-ve-hierarchical", "stapel-ve-select", "stapel-ve-string-number",
];

interface Lib {
  defineElements(): void;
  registeredValueEditorTypes(): string[];
}
let lib: Lib;

beforeAll(async () => {
  // @vite-ignore — load the pre-built artifact natively, bypassing vite transform.
  lib = (await import(/* @vite-ignore */ pathToFileURL(OUT).href)) as unknown as Lib;
});

describe("lib build — side-effect-free import", () => {
  it("registers nothing on import", () => {
    // No stapel-* custom element is defined merely by importing the lib.
    for (const tag of EXPECTED_TAGS) expect(customElements.get(tag)).toBeUndefined();
    // No value-editor is in the registry yet.
    expect(lib.registeredValueEditorTypes()).toEqual([]);
  });

  it("defineElements() registers all built-ins (and is idempotent)", () => {
    lib.defineElements();
    lib.defineElements(); // second call must not throw (guarded define / Map)
    for (const tag of EXPECTED_TAGS) expect(customElements.get(tag)).toBeDefined();
    expect(lib.registeredValueEditorTypes()).toEqual(EXPECTED_TYPES);
  });
});
