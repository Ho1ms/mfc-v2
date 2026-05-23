import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { fileURLToPath, URL } from "node:url";

const apiUrl = process.env.VITE_API_URL || "http://localhost:8000";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/api": { target: apiUrl, changeOrigin: true },
      "/ws": { target: apiUrl.replace(/^http/, "ws"), ws: true, changeOrigin: true },
    },
  },
});
