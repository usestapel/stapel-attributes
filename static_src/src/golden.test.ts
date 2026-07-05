// Cross-language golden bridge — JS runner (spec: review-attributes-admin.md).
// Reads the SAME corpus as tests/test_golden.py and fills / checks the
// `expect.js` section of each case: for `config` cases, the <stapel-config-editor>
// re-emits the loaded config (getConfig); for `dto` cases, the value-editor's
// validity. A divergence from the Python side (recorded in each case) is
// explicit via the `divergence` field.
//
// Record mode: `GOLDEN_RECORD=1 vitest run src/golden.test.ts` rewrites
// `expect.js` from the real editors (byte-stable: sorted keys, 2-space, \n) so
// `emits` is always a fact of the live editor, never hand-written.
import { describe, it, expect } from "vitest";
import { readFileSync, writeFileSync, readdirSync } from "node:fs";
import { resolve } from "node:path";
import "./index.js"; // registers every value-editor + <stapel-config-editor>
import { ConfigEditorElement } from "./config-editor.js";
import { resolveValueEditor } from "./registry.js";
import { I18n } from "./runtime/i18n.js";
import type { TypeDecl, FeatureConfig, ValueDto } from "./types.js";

// vitest runs with cwd = static_src; the corpus lives at ../tests/golden.
const GOLDEN = resolve(process.cwd(), "..", "tests", "golden");
const CASES = `${GOLDEN}/cases`;
const RECORD = process.env.GOLDEN_RECORD === "1";

const declarations: Record<string, TypeDecl> = JSON.parse(
  readFileSync(`${GOLDEN}/declarations.json`, "utf8"),
);
const i18n = new I18n("en", {});

interface Case {
  id: string;
  type: string;
  kind: "config" | "dto";
  mandatory?: boolean;
  config: FeatureConfig;
  dto?: ValueDto;
  expect: { python: unknown; js: Record<string, unknown> };
  divergence: unknown;
  [k: string]: unknown;
}

function sortKeys(v: unknown): unknown {
  if (Array.isArray(v)) return v.map(sortKeys);
  if (v && typeof v === "object") {
    const out: Record<string, unknown> = {};
    for (const k of Object.keys(v as object).sort()) out[k] = sortKeys((v as Record<string, unknown>)[k]);
    return out;
  }
  return v;
}
function dump(obj: unknown): string {
  return JSON.stringify(sortKeys(obj), null, 2) + "\n";
}

function loadCases(): { path: string; case: Case }[] {
  return readdirSync(CASES)
    .filter((f) => f.endsWith(".json"))
    .sort()
    .map((f) => ({ path: `${CASES}/${f}`, case: JSON.parse(readFileSync(`${CASES}/${f}`, "utf8")) as Case }));
}

async function runConfig(c: Case): Promise<Record<string, unknown>> {
  const el = new ConfigEditorElement();
  el.declaration = declarations[c.type] ?? { label_key: "", fields: [] };
  el.typeSlug = c.type;
  el.i18n = i18n;
  document.body.appendChild(el);
  el.setConfig(c.config);
  await el.updateComplete;
  const emits = el.getConfig();
  el.remove();
  return { emits };
}

function runDto(c: Case): Record<string, unknown> {
  const factory = resolveValueEditor(c.type);
  const el = factory({ config: c.config, mandatory: !!c.mandatory, i18n }) as HTMLElement & {
    setValue(dto: ValueDto | null): void;
    validate(): string[];
  };
  document.body.appendChild(el);
  el.setValue(c.dto ?? null);
  const errors = el.validate();
  el.remove();
  return { valid: errors.length === 0 };
}

describe("golden cross-language bridge (JS side)", () => {
  for (const { path, case: c } of loadCases()) {
    it(c.id, async () => {
      const actual = c.kind === "config" ? await runConfig(c) : runDto(c);

      if (RECORD) {
        c.expect.js = actual;
        writeFileSync(path, dump(c));
        return;
      }

      expect(c.expect.js, `${c.id}: no recorded js expectation (run GOLDEN_RECORD=1)`).toBeTruthy();
      expect(actual).toEqual(c.expect.js);
    });
  }
});
