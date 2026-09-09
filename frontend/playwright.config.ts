import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./tests",
  timeout: 60000,
  use: {
    baseURL: "http://127.0.0.1:5173",
    headless: true,
    launchOptions: {
      executablePath: process.env.CHROME_PATH || "/usr/bin/google-chrome",
      args: ["--no-sandbox"],
    },
    screenshot: "only-on-failure",
  },
  webServer: [
    {
      command:
        "cd ../backend && export DATABASE_URL=sqlite:////tmp/mission-foundry-e2e.db && ../.venv/bin/alembic upgrade head && ../.venv/bin/uvicorn app.api.main:app --port 8000",
      url: "http://127.0.0.1:8000/api/scenario",
      reuseExistingServer: true,
    },
    {
      command: "npm run dev",
      url: "http://127.0.0.1:5173",
      reuseExistingServer: true,
    },
  ],
});
