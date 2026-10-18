import { test, expect } from "@playwright/test";
test("owner clarifies a requirement and proposes a partial deadline", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByLabel("Mission name").fill("Formalization " + Date.now());
  await page.getByRole("button", { name: "Create mission →" }).click();
  await page.getByRole("button", { name: "Approve assumptions" }).click();
  await page.getByRole("button", { name: "Advance workflow →" }).click();
  await page.getByRole("button", { name: "Approve requirements" }).click();
  await page.getByRole("button", { name: "Requirements", exact: true }).click();
  await page.getByLabel("Requirement to clarify").selectOption("req-latency");
  await page
    .getByLabel("Clarification question")
    .fill("What image quality is required?");
  await page.getByRole("button", { name: "Save clarification" }).click();
  await expect(page.getByText(/Awaiting answer/)).toBeVisible();
  await page
    .getByRole("button", { name: "Answer question", exact: true })
    .click();
  await page
    .getByLabel("Clarification answer")
    .fill("Quality needs a separate engineering assessment");
  await page.getByRole("button", { name: "Save clarification" }).click();
  await expect(page.getByText(/superseded by reply/)).toBeVisible();
  await page.getByRole("button", { name: "Use suggested deadline" }).click();
  await page
    .getByLabel("Basis and applicability")
    .fill(
      "Deadline extracted from requirement; image quality remains unresolved",
    );
  await page.getByRole("button", { name: "Propose formalization" }).click();
  await expect(
    page.getByRole("button", { name: "Propose formalization" }),
  ).toBeDisabled();
  await page
    .getByRole("button", { name: "Conflicts & review", exact: true })
    .click();
  await expect(
    page
      .getByText(
        "Deadline extracted from requirement; image quality remains unresolved",
        { exact: true },
      )
      .first(),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Approve design change", exact: true })
    .click();
  await page.getByRole("button", { name: "Requirements", exact: true }).click();
  await page.getByLabel("Requirement to clarify").selectOption("req-latency");
  await expect(page.getByLabel("Requirement to clarify")).toContainText(
    "partial",
  );
  await page.screenshot({
    path: "test-results/requirement-formalization.png",
    fullPage: true,
  });
});
