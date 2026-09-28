import path from "node:path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  root: path.resolve(__dirname, "src/companion"),
  plugins: [react()],
  build: { sourcemap: false, outDir: path.resolve(__dirname, ".vite/renderer/companion_window"), emptyOutDir: true },
  server: { host: "127.0.0.1", strictPort: true }
});
