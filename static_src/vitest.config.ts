import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "jsdom",
    globals: true,
    include: ["src/**/*.test.ts"],
    // Builds the lib bundle (Node env) so builds-lib.test.ts can load the artifact.
    globalSetup: ["./vitest.globalSetup.mjs"],
  },
  esbuild: {
    // Lit decorators
    target: "es2022",
  },
});
