// Dual build from ONE source tree:
//
//  1. django  — the committed admin bundle in static/stapel_attributes/. Lit is
//     inlined; output is deterministic so the CI drift gate (rebuild must not
//     change static/) holds byte-for-byte. Entry: index.ts (self-registering).
//
//  2. lib     — the externalized-Lit ESM package for npm consumers
//     (@stapel/attributes-react). Lit is a peerDependency (external), the
//     `@stapel-auto-define` registration tails are stripped so imports are
//     side-effect-free, and .d.ts types are emitted. Entry: lib.ts. Output goes
//     to dist/ (gitignored, not committed, not published here). Never touches
//     the django bundle — separate outfile, separate profile.
//
// `node build.mjs`      builds the django bundle only (the drift-gated default,
//                        so CI `npm run build` semantics are unchanged).
// `node build.mjs lib`   builds the npm lib only.
// `node build.mjs all`   builds both.
import { build } from "esbuild";
import { cpSync, mkdirSync, readdirSync, rmSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { execFileSync } from "node:child_process";
import { stripAutoDefine } from "./strip-auto-define.mjs";

const here = dirname(fileURLToPath(import.meta.url));
const STATIC_DIR = join(here, "..", "static", "stapel_attributes");
const DIST_DIR = join(here, "dist");

/** The committed Django admin bundle. MUST stay byte-stable (drift gate). */
export async function buildDjango() {
  mkdirSync(join(STATIC_DIR, "locales"), { recursive: true });
  await build({
    entryPoints: [join(here, "src", "index.ts")],
    bundle: true,
    format: "esm",
    target: "es2022",
    minify: true,
    legalComments: "none",
    sourcemap: false,
    charset: "utf8",
    // The package declares `sideEffects: false` for the npm lib (tree-shaking).
    // The django entry deliberately relies on side-effect imports (each editor
    // self-registers), so ignore that annotation here — otherwise esbuild prunes
    // the registrations, shrinking/breaking the bundle. Keeps it byte-stable.
    ignoreAnnotations: true,
    outfile: join(STATIC_DIR, "attributes-admin.js"),
    banner: { js: "/* stapel-attributes admin — generated from static_src/, do not edit */" },
  });
  // Static assets shipped alongside the bundle.
  cpSync(join(here, "src", "tokens", "admin-tokens.css"), join(STATIC_DIR, "admin-tokens.css"));
  for (const f of readdirSync(join(here, "src", "locales"))) {
    cpSync(join(here, "src", "locales", f), join(STATIC_DIR, "locales", f));
  }
  console.log("built django ->", STATIC_DIR);
}

/** esbuild options for the lib bundle. Lit is externalized (peerDependency) and
 *  the `@stapel-auto-define` tails are stripped so the bundle is side-effect-free.
 *  Reused by builds.test.ts (which builds to a temp outfile). */
export function libEsbuildOptions(outfile) {
  return {
    entryPoints: [join(here, "src", "lib.ts")],
    bundle: true,
    format: "esm",
    target: "es2022",
    minify: false, // readable; consumers minify. sideEffects:false enables tree-shaking.
    legalComments: "none",
    sourcemap: true,
    charset: "utf8",
    external: ["lit", "lit/*"], // peerDependency, not inlined
    plugins: [stripAutoDefine()],
    outfile,
  };
}

/** The externalized-Lit npm bundle (@stapel/attributes-admin). */
export async function buildLib() {
  rmSync(DIST_DIR, { recursive: true, force: true });
  mkdirSync(join(DIST_DIR, "locales"), { recursive: true });
  await build(libEsbuildOptions(join(DIST_DIR, "lib.mjs")));
  // Assets exported via the package "exports" map.
  cpSync(join(here, "src", "tokens", "admin-tokens.css"), join(DIST_DIR, "admin-tokens.css"));
  for (const f of readdirSync(join(here, "src", "locales"))) {
    cpSync(join(here, "src", "locales", f), join(DIST_DIR, "locales", f));
  }
  // Type declarations.
  execFileSync("npx", ["tsc", "-p", "tsconfig.lib.json"], { cwd: here, stdio: "inherit" });
  console.log("built lib ->", DIST_DIR);
}

// CLI dispatch — only when run directly (`node build.mjs [lib|all]`), never on
// import (builds.test.ts imports the functions above).
if (import.meta.url === pathToFileURL(process.argv[1] ?? "").href) {
  const which = process.argv[2];
  if (which === "lib") await buildLib();
  else if (which === "all") {
    await buildDjango();
    await buildLib();
  } else await buildDjango();
}
