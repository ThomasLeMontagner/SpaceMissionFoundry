import { expect, test } from "@playwright/test";

test("archive a saved mission, cancel safely and restore its pending workflow", async ({
  page,
  request,
}) => {
  const scenario = await (await request.get("/api/scenario")).json();
  const name = "Archive workflow " + Date.now();
  const mission = await (
    await request.post("/api/missions", {
      data: { name, brief: scenario.brief },
    })
  ).json();
  await page.goto("/");
  page.once("dialog", (dialog) => dialog.dismiss());
  await page
    .getByRole("button", { name: "Archive " + name, exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: name + " →", exact: true }),
  ).toBeVisible();
  page.once("dialog", (dialog) => dialog.accept());
  await page
    .getByRole("button", { name: "Archive " + name, exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: name + " →", exact: true }),
  ).toHaveCount(0);
  await page.getByLabel("Show archived missions", { exact: true }).check();
  await expect(
    page.getByRole("button", { name: "Restore " + name, exact: true }),
  ).toBeVisible();
  await page.reload();
  await page.getByLabel("Show archived missions", { exact: true }).check();
  await page
    .getByRole("button", { name: "Restore " + name, exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Restore " + name, exact: true }),
  ).toHaveCount(0);
  await page.getByLabel("Show archived missions", { exact: true }).uncheck();
  await page.getByRole("button", { name: name + " →", exact: true }).click();
  await page
    .getByRole("button", { name: "Approve assumptions", exact: true })
    .click();
  await expect(
    page.getByText("Needs defined", { exact: true }).first(),
  ).toBeVisible();
  page.once("dialog", (dialog) => dialog.accept());
  await page
    .getByRole("button", { name: "Archive mission", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Saved missions", exact: true }),
  ).toBeVisible();
  await page.getByLabel("Show archived missions", { exact: true }).check();
  await expect(
    page.getByRole("button", { name: "Restore " + name, exact: true }),
  ).toBeVisible();
  expect(
    (await (await request.get(`/api/missions/${mission.id}`)).json()).archived,
  ).toBe(true);
});
