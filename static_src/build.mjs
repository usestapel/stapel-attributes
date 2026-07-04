// Build the committed admin bundle. Deterministic output so the CI drift gate
// (rebuild must not change static/) holds. No sourcemaps, no timestamps.
import { build } from "esbuild";
import { cpSync, mkdirSync, readdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const OUT_DIR = join(here, "..", "static", "stapel_attributes");
mkdirSync(join(OUT_DIR, "locales"), { recursive: true });

await build({
  entryPoints: [join(here, "src", "index.ts")],
  bundle: true,
  format: "esm",
  target: "es2022",
  minify: true,
  legalComments: "none",
  sourcemap: false,
  charset: "utf8",
  outfile: join(OUT_DIR, "attributes-admin.js"),
  banner: { js: "/* stapel-attributes admin — generated from static_src/, do not edit */" },
});

// Static assets shipped alongside the bundle.
cpSync(join(here, "src", "tokens", "admin-tokens.css"), join(OUT_DIR, "admin-tokens.css"));
for (const f of readdirSync(join(here, "src", "locales"))) {
  cpSync(join(here, "src", "locales", f), join(OUT_DIR, "locales", f));
}

console.log("built ->", OUT_DIR);
