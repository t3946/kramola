import { defineConfig } from "vite";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";
import { mkdirSync, copyFileSync } from "fs";
import cssInjectedByJsPlugin from "vite-plugin-css-injected-by-js";
import sassGlobImports from "vite-plugin-sass-glob-import";

const __dirname = dirname(fileURLToPath(import.meta.url));

const distAdminDir = resolve(__dirname, "dist", "admin");
const projectStaticAdmin = resolve(__dirname, "..", "static", "admin");

function copyToProjectStaticPlugin() {
  return {
    name: "copy-to-project-static",
    writeBundle() {
      mkdirSync(projectStaticAdmin, { recursive: true });
      copyFileSync(
        resolve(distAdminDir, "bundle.js"),
        resolve(projectStaticAdmin, "bundle.js")
      );
    },
  };
}

export default defineConfig({
  root: __dirname,
  plugins: [sassGlobImports(), cssInjectedByJsPlugin(), copyToProjectStaticPlugin()],
  css: {
    preprocessorOptions: {
      scss: {},
    },
  },
  build: {
    outDir: distAdminDir,
    emptyOutDir: true,
    rollupOptions: {
      input: resolve(__dirname, "frontend", "js", "main.ts"),
      output: {
        format: "iife",
        entryFileNames: "bundle.js",
      },
    },
  },
});
