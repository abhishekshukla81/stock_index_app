import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Relative base: works under a GitHub Pages sub-path (/<repo>/) and locally.
export default defineConfig({
  base: "./",
  plugins: [react()],
  server: { host: "127.0.0.1", port: 5174, strictPort: true },
  preview: { host: "127.0.0.1", port: 5174, strictPort: true },
});
