import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Relative base so the bundle also works behind the Colab proxy.
export default defineConfig({
  base: "./",
  plugins: [react()],
  server: {
    host: "127.0.0.1",
    port: 5173,
    strictPort: true,
    proxy: { "/api": "http://127.0.0.1:5000" },
  },
});
