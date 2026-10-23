import { test, expect } from "@playwright/test";
test("decomposition adds linked children only after owner approval", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByLabel("Mission name").fill("Decomposition " + Date.now());
  await page.getByRole("button", { name: "Create mission →" }).click();
  await page.getByRole("button", { name: "Approve assumptions" }).click();
  await page.getByRole("button", { name: "Advance workflow →" }).click();
  await page.getByRole("button", { name: "Approve requirements" }).click();
  await page
    .getByRole("button", { name: "Agent collaboration", exact: true })
    .click();
  const panel = page.getByRole("region", {
    name: "Requirement agent collaboration",
    exact: true,
  });
  await panel
    .getByLabel("Requirement assistance type")
    .selectOption("decomposition");
  await panel.getByLabel("Requirement for agents").selectOption("req-latency");
  await panel
    .getByRole("button", {
      name: "Start requirement collaboration",
      exact: true,
    })
    .click();
  await panel
    .getByRole("button", { name: "Run until owner action", exact: true })
    .click();
  await panel
    .getByLabel(
      "Which obligations and conditions must remain unresolved when separating delivery timing from the rest of this requirement?",
    )
    .fill(
      "Image quality, processing and workload require further engineering assessment",
    );
  await panel
    .getByRole("button", { name: "Record answers and continue" })
    .click();
  await panel
    .getByRole("button", { name: "Run until owner action", exact: true })
    .click();
  await expect(
    panel.getByRole("heading", { name: "Proposed child requirements" }),
  ).toBeVisible();
  await expect(
    panel.getByText(/No supported criterion — unresolved/),
  ).toBeVisible();
  await panel
    .getByRole("button", {
      name: "Submit child requirements for human approval",
    })
    .click();
  await page.getByRole("button", { name: "Requirements", exact: true }).click();
  await page.getByLabel("Requirement to clarify").selectOption("req-latency");
  await expect(
    page.getByRole("heading", { name: "Derived requirements" }),
  ).toHaveCount(0);
  await page
    .getByRole("button", { name: "Conflicts & review", exact: true })
    .click();
  await page
    .getByRole("button", {
      name: "Approve requirement decomposition",
      exact: true,
    })
    .click();
  await page.getByRole("button", { name: "Requirements", exact: true }).click();
  await page.getByLabel("Requirement to clarify").selectOption("req-latency");
  await expect(
    page.getByRole("heading", { name: "Derived requirements" }),
  ).toBeVisible();
  await page
    .getByRole("button", {
      name: "within 30 minutes of acquisition",
      exact: true,
    })
    .click();
  await expect(page.getByText("Parent requirement:")).toBeVisible();
  await expect(page.getByLabel("Threshold", { exact: true })).toHaveValue("30");
  await page.screenshot({
    path: "test-results/requirement-decomposition.png",
    fullPage: true,
  });
});
