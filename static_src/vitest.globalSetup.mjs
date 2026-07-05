// Builds the externalized-Lit lib bundle once, in the Node runner (esbuild can't
// run inside the jsdom test environment). builds-lib.test.ts then imports the
// produced artifact to assert it is side-effect-free on import.
import { build } from "esbuild";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { libEsbuildOptions } from "./build.mjs";

const here = dirname(fileURLToPath(import.meta.url));

export async function setup() {
  await build(libEsbuildOptions(resolve(here, "dist", "_libtest.mjs")));
}
