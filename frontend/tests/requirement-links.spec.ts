import { test, expect } from "@playwright/test";

test("owner proposes and separately approves a parent change", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByLabel("Mission name").fill("Parent links " + Date.now());
  await page.getByRole("button", { name: "Create mission →" }).click();
  await page.getByRole("button", { name: "Approve assumptions" }).click();
  await page.getByRole("button", { name: "Advance workflow →" }).click();
  await page.getByRole("button", { name: "Approve requirements" }).click();
  await page.getByRole("button", { name: "Requirements", exact: true }).click();
  await page.getByLabel("Requirement to clarify").selectOption("req-latency");
  const form = page.getByRole("form", {
    name: "Edit requirement parent links",
  });
  await form.getByLabel(/^objective —/).uncheck();
  await form.getByLabel(/^req-observe —/).check();
  await form
    .getByLabel("Parent-link change rationale")
    .fill("Latency derives from observation need");
  await form
    .getByRole("button", { name: "Propose parent links for approval" })
    .click();
  await expect(form.getByText(/^Current parents: objective/)).toBeVisible();
  await page.getByRole("button", { name: /Conflicts.*review/i }).click();
  await page
    .getByRole("button", { name: "Approve design change", exact: true })
    .click();
  await page.getByRole("button", { name: "Requirements", exact: true }).click();
  await page.getByLabel("Requirement to clarify").selectOption("req-latency");
  await expect(form.getByText(/^Current parents: req-observe/)).toBeVisible();
  await expect(
    page.getByText(
      "Does the criterion cover the revised parent context and all inherited obligations?",
    ),
  ).toBeVisible();
  await page.screenshot({
    path: "test-results/requirement-links.png",
    fullPage: true,
  });
});
