import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

// The site is published under /trainer/ on GitHub Pages, and every artifact fetch is relative to the
// base so the same bundle works from a subpath and from a preview server.
export default defineConfig({
  base: "/trainer/",
  plugins: [vue()],
  build: {
    target: "es2022",
    // A teaching tool should stay inspectable; sourcemaps are off by default so the published bundle
    // is what the browser runs.
    sourcemap: false,
  },
});
