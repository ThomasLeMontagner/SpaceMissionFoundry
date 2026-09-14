import { existsSync } from "node:fs";
import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./tests",
  timeout: 90000,
  use: {
    baseURL: "http://127.0.0.1:5174",
    headless: true,
    launchOptions: {
      executablePath:
        process.env.CHROME_PATH ||
        (existsSync("/usr/bin/google-chrome")
          ? "/usr/bin/google-chrome"
          : undefined),
      args: ["--no-sandbox"],
    },
    screenshot: "only-on-failure",
  },
  webServer: [
    {
      command:
        "cd ../backend && export DATABASE_URL=sqlite:////tmp/mission-foundry-iteration-e2e.db && ../.venv/bin/alembic upgrade head && ../.venv/bin/uvicorn app.api.main:app --port 8011",
      url: "http://127.0.0.1:8011/api/scenario",
      reuseExistingServer: false,
    },
    {
      command: "npm run dev -- --port 5174 --strictPort",
      env: { API_TARGET: "http://127.0.0.1:8011" },
      url: "http://127.0.0.1:5174",
      reuseExistingServer: false,
    },
  ],
});
