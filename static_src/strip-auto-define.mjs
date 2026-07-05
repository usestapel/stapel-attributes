// Shared esbuild onLoad plugin used by the *lib* build profile (and its tests).
//
// The django bundle self-registers custom elements + value-editors at import:
// each editor / component module ends with a registration tail marked by a
// `// @stapel-auto-define` sentinel. That tail is exactly what makes the module
// side-effectful. For the externalized-Lit npm lib we must ship side-effect-free
// modules (package.json `sideEffects: false`, honest tree-shaking, no implicit
// customElements.define — see review-attributes-admin.md blocker #2/#3), and let
// the host register explicitly via `defineElements()` (lib.ts).
//
// Rather than fork the sources — which would perturb esbuild's frequency-ranked
// identifier minifier and break the django bundle's byte-stability (drift gate) —
// this plugin strips the marked tail *at build time* for the lib profile only.
// The django profile never uses it, so its committed bundle is untouched.
import { readFile } from "node:fs/promises";

// Removes each `// @stapel-auto-define:start … // @stapel-auto-define:end` block
// (inclusive). Non-greedy + global so a module with the define placed mid-file
// (e.g. runtime/dialog.ts, whose openDialog export follows) keeps everything
// outside the marked block.
const BLOCK = /[ \t]*\/\/ @stapel-auto-define:start[\s\S]*?\/\/ @stapel-auto-define:end[^\n]*\n?/g;

/** @returns {import('esbuild').Plugin} */
export function stripAutoDefine() {
  return {
    name: "stapel-strip-auto-define",
    setup(build) {
      build.onLoad({ filter: /\.ts$/ }, async (args) => {
        const src = await readFile(args.path, "utf8");
        if (!src.includes("@stapel-auto-define:start")) return undefined; // not a side-effect module
        return { contents: src.replace(BLOCK, ""), loader: "ts" };
      });
    },
  };
}
