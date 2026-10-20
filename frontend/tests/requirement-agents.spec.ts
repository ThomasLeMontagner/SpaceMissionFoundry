import { test, expect } from "@playwright/test";
test("agents clarify, review and submit a partial requirement for human approval", async ({
  page,
}) => {
  await page.goto("/");
  await page
    .getByLabel("Mission name")
    .fill("Agent requirements " + Date.now());
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
  await panel.getByLabel("Requirement for agents").selectOption("req-latency");
  await panel
    .getByRole("button", {
      name: "Start requirement collaboration",
      exact: true,
    })
    .click();
  await panel
    .getByRole("button", { name: "Run Mission clarification", exact: true })
    .click();
  await expect(panel.getByText("Owner clarification answers")).toBeVisible();
  await panel
    .getByLabel(
      "Which parts of this requirement are outside the proposed numeric check?",
    )
    .fill("Image quality and operational workload still need assessment");
  await panel
    .getByRole("button", { name: "Record answers and continue" })
    .click();
  await panel
    .getByRole("button", {
      name: "Run Systems criterion proposal",
      exact: true,
    })
    .click();
  await panel
    .getByRole("button", { name: "Run Independent review", exact: true })
    .click();
  await expect(panel.getByText("Independent reviewer: submit")).toBeVisible();
  await expect(panel.getByText(/Accounted tokens: 0/)).toBeVisible();
  await panel
    .getByRole("button", {
      name: "Submit partial criterion for human approval",
    })
    .click();
  await page
    .getByRole("button", { name: "Conflicts & review", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Approve design change", exact: true })
    .click();
  await page.getByRole("button", { name: "Requirements", exact: true }).click();
  await page.getByLabel("Requirement to clarify").selectOption("req-latency");
  await expect(page.getByLabel("Requirement to clarify")).toContainText(
    "partial",
  );
  await page
    .getByRole("button", { name: "Agent collaboration", exact: true })
    .click();
  await panel
    .getByRole("heading", { name: "Recorded agent exchanges" })
    .scrollIntoViewIfNeeded();
  await page.screenshot({
    path: "test-results/requirement-agents.png",
    fullPage: true,
  });
});
