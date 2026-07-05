// The TS ValidationErrorCode mirror must match the Python enum exactly. Both
// sides read the same committed snapshot (tests/golden/error_codes.json, written
// by the Python golden runner). A code added to one language but not the other
// turns this red — the py↔ts sync gate for the error-code contract.
import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { VALIDATION_ERROR_CODES } from "./error-codes.js";

const SNAPSHOT = resolve(process.cwd(), "..", "tests", "golden", "error_codes.json");

describe("ValidationErrorCode py↔ts mirror", () => {
  it("matches the Python-generated snapshot", () => {
    const py: string[] = JSON.parse(readFileSync(SNAPSHOT, "utf8"));
    expect([...VALIDATION_ERROR_CODES]).toEqual(py);
  });

  it("includes the NOT_ALLOWED / UNKNOWN_FEATURE follow-up codes", () => {
    expect(VALIDATION_ERROR_CODES).toContain("not_allowed");
    expect(VALIDATION_ERROR_CODES).toContain("unknown_feature");
  });
});
