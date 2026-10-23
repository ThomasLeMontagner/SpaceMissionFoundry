import { test, expect } from "@playwright/test";

test("quality findings filter and navigate to clarification", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByLabel("Mission name").fill("Quality " + Date.now());
  await page.getByRole("button", { name: "Create mission →" }).click();
  await page.getByRole("button", { name: "Approve assumptions" }).click();
  await page.getByRole("button", { name: "Advance workflow →" }).click();
  await page.getByRole("button", { name: "Approve requirements" }).click();
  await page.getByRole("button", { name: "Requirements", exact: true }).click();
  const panel = page.getByRole("region", {
    name: "Requirement quality checks",
  });
  await expect(panel.getByText(/advisory findings across/)).toBeVisible();
  await panel
    .getByLabel("Quality finding type")
    .selectOption("ambiguous_wording");
  await expect(panel.getByText(/Flagged text/)).toBeVisible();
  await panel
    .getByRole("button", { name: "Review req-latency", exact: true })
    .click();
  await expect(page.getByLabel("Requirement to clarify")).toHaveValue(
    "req-latency",
  );
  await expect(
    page.getByText(/Suggested deadline from the statement/),
  ).toBeVisible();
  await page.screenshot({
    path: "test-results/requirement-quality.png",
    fullPage: true,
  });
});
