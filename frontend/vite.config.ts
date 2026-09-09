import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
export default defineConfig({
  plugins: [react()],
  server: {
    watch: { usePolling: true, interval: 1000 },
    proxy: { "/api": process.env.API_TARGET || "http://127.0.0.1:8000" },
  },
  test: {
    include: ["src/**/*.test.tsx"],
    environment: "jsdom",
    setupFiles: ["./src/test-setup.ts"],
  },
});
