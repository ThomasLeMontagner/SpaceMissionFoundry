import { test, expect } from "@playwright/test";
test("mission brief to approved concept, export and replay", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.getByLabel("Mission name")).not.toHaveValue("");
  await page.getByLabel("Mission name").fill("Pyra E2E " + Date.now());
  await page.getByRole("button", { name: "Create mission →" }).click();
  await page.getByRole("button", { name: "Pause", exact: true }).click();
  await page.getByRole("button", { name: "Resume", exact: true }).click();
  await page.getByRole("button", { name: "Challenge", exact: true }).click();
  await page.getByRole("button", { name: "Approve assumptions" }).click();
  await page.getByRole("button", { name: "Advance workflow →" }).click();
  await page.getByRole("button", { name: "Approve requirements" }).click();
  await page.getByRole("button", { name: "Advance workflow →" }).click();
  await page.getByRole("button", { name: "Approve architectures" }).click();
  await page.getByRole("button", { name: "Advance workflow →" }).click();
  await page.getByRole("button", { name: "Inspect trade study →" }).click();
  await page
    .getByRole("button", {
      name: "Select B · Event-selective imaging + X-band",
    })
    .click();
  await page.getByRole("button", { name: "Overview", exact: true }).click();
  await page.getByRole("button", { name: "Run independent review" }).click();
  await page
    .getByRole("button", { name: "Propose finding resolution" })
    .click();
  await page
    .getByRole("button", { name: "Verify resolution independently" })
    .click();
  await page.getByRole("button", { name: "Open baseline workspace →" }).click();
  await expect(
    page.getByRole("button", { name: "Approve immutable baseline" }),
  ).toBeDisabled();
  await page.getByRole("checkbox").check();
  await page
    .getByRole("button", { name: "Approve immutable baseline" })
    .click();
  await expect(page.getByText("Immutable conceptual baseline")).toBeVisible();
  const download = page.waitForEvent("download");
  await page.getByRole("button", { name: "Export JSON" }).click();
  expect((await download).suggestedFilename()).toBe("mission-concept.json");
  await page.getByRole("button", { name: "Load replay timeline" }).click();
  await page.getByLabel("Historical revision").selectOption("0");
  await expect(
    page.getByRole("heading", { name: "Revision 0 · Brief" }),
  ).toBeVisible();
  await page.screenshot({
    path: "test-results/baseline-replay.png",
    fullPage: true,
  });
  for (const tab of [
    "Brief & assumptions",
    "Requirements",
    "Architectures",
    "Interfaces",
    "Budgets",
    "Trades",
    "Claims & evidence",
    "Conflicts & review",
    "Agent activity",
    "Decisions",
  ]) {
    await page.getByRole("button", { name: tab, exact: true }).click();
    const cards = page.locator(".object-card");
    if (await cards.count()) {
      await cards.first().click();
      await expect(page.getByRole("dialog")).toBeVisible();
      await page.keyboard.press("Escape");
      await expect(page.getByRole("dialog")).toHaveCount(0);
    }
    await page
      .getByPlaceholder("ID, text, owner, state…")
      .fill("nonexistent-query");
    await expect(page.locator(".object-card")).toHaveCount(0);
    await page.getByPlaceholder("ID, text, owner, state…").fill("");
  }
  await page.getByRole("button", { name: "Overview", exact: true }).click();
  await page.screenshot({ path: "test-results/workbench.png", fullPage: true });
  await page
    .getByRole("button", { name: "Baselines & replay", exact: true })
    .click();
  for (const format of ["MD", "CSV"]) {
    const file = page.waitForEvent("download");
    await page.getByRole("button", { name: "Export " + format }).click();
    await file;
  }
  await page.getByRole("button", { name: "Load replay timeline" }).click();
  await page.getByLabel("Historical revision").selectOption("0");
  page.once("dialog", (dialog) => dialog.accept());
  await page.getByRole("button", { name: "Restore as new revision" }).click();
  await page.getByRole("button", { name: "Overview", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Approve assumptions" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Reject", exact: true }).click();
  await page.getByRole("button", { name: "Advance workflow →" }).click();
  await expect(
    page.getByRole("button", { name: "Approve assumptions" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Switch mission" }).click();
  await expect(
    page.getByRole("heading", { name: "Saved missions" }),
  ).toBeVisible();
});
