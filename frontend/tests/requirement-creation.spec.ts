import { test, expect } from "@playwright/test";

test("new requirement remains a proposal until owner approval", async ({
  page,
}) => {
  const missionName = "Manual requirement " + Date.now();
  await page.goto("/");
  await expect(page.getByLabel("Natural-language mission brief")).toHaveValue(
    /Design a 12U CubeSat/,
  );
  await page.getByLabel("Mission name").fill(missionName);
  await page.getByRole("button", { name: "Create mission →" }).click();
  await page.getByRole("button", { name: "Approve assumptions" }).click();
  await page.getByRole("button", { name: "Advance workflow →" }).click();
  await page.getByRole("button", { name: "Approve requirements" }).click();
  await page.getByRole("button", { name: "Requirements", exact: true }).click();
  const form = page.getByRole("region", {
    name: "Create requirement",
    exact: true,
  });
  await form.getByText("Add a requirement", { exact: true }).click();
  const statement = "The mission shall provide a daily observation report.";
  await form.getByLabel("New requirement statement").fill(statement);
  await form
    .getByLabel("Requirement rationale")
    .fill("Support operations planning");
  await form.getByLabel("Requirement source").fill("Owner operations need");
  await form.getByRole("checkbox", { name: /^objective —/ }).check();
  await form
    .getByRole("button", { name: "Propose new requirement for approval" })
    .click();
  await expect(
    page
      .getByLabel("Requirement to clarify")
      .getByRole("option", { name: new RegExp(statement) }),
  ).toHaveCount(0);
  await page.getByRole("button", { name: /Conflicts.*review/i }).click();
  await expect(page.getByText(statement, { exact: true })).toBeVisible();
  await page
    .getByRole("button", { name: "Approve manual requirement", exact: true })
    .click();
  await page.getByRole("button", { name: "Requirements", exact: true }).click();
  const option = page
    .getByLabel("Requirement to clarify")
    .getByRole("option", { name: new RegExp(statement) });
  const id = await option.getAttribute("value");
  await page.getByLabel("Requirement to clarify").selectOption(id!);
  await expect(
    page.getByLabel("Unresolved questions (one per line, maximum ten)"),
  ).toHaveValue(
    "Which criterion, conditions and evidence will verify this requirement?",
  );
  await page.reload();
  await page
    .getByRole("button", { name: missionName + " →", exact: true })
    .click();
  await page.getByRole("button", { name: "Requirements", exact: true }).click();
  await expect(
    page
      .getByLabel("Requirement to clarify")
      .getByRole("option", { name: new RegExp(statement) }),
  ).toHaveCount(1);
  await page.getByLabel("Requirement to clarify").selectOption(id!);
  await page.screenshot({
    path: "test-results/requirement-creation.png",
    fullPage: true,
  });
});
