import { expect, test } from "@playwright/test";

test("baseline sensitivity study compares trials and exports evidence without altering the design", async ({
  page,
  request,
}) => {
  const scenario = await (await request.get("/api/scenario")).json();
  const name = "Sensitivity scenario " + Date.now();
  let m = await (
    await request.post("/api/missions", {
      data: { name, brief: scenario.brief },
    })
  ).json();
  async function post(path: string, body: object = {}) {
    const response = await request.post(`/api/missions/${m.id}/${path}`, {
      data: { revision: m.revision, ...body },
    });
    expect(response.ok(), await response.text()).toBeTruthy();
    m = await response.json();
  }
  for (let i = 0; i < 3; i++) {
    const p: any = Object.values(m.proposals).find(
      (p: any) => p.status === "submitted",
    );
    await post(`proposals/${p.id}/decision`, {
      action: "accept",
      reason: "Prepare sensitivity browser fixture",
    });
    await post("advance");
  }
  await post("select", {
    candidate: "selective",
    weights: { science: 0.35, capacity: 0.45, simplicity: 0.2 },
    reason: "Choose reference concept",
  });
  for (let i = 0; i < 3; i++) await post("advance");
  await post("baseline", { name: "Sensitivity source", confirm: true });
  const original = await (
    await request.get(`/api/missions/${m.id}/export/json`)
  ).json();
  await page.goto("/");
  await page.getByRole("button", { name: name + " →", exact: true }).click();
  await page
    .getByRole("button", { name: "Sensitivity analysis", exact: true })
    .click();
  const region = page.getByRole("region", {
    name: "Delivery sensitivity analysis",
  });
  await region.getByLabel("Trial values", { exact: true }).fill("0, 2, 60");
  await region.getByRole("button", { name: "Run sensitivity study" }).click();
  await expect(region.getByRole("table")).toBeVisible();
  await expect(region.getByRole("row")).toHaveCount(5);
  await expect(region.getByText(/pass ·/).first()).toBeVisible();
  await expect(region.getByText(/fail ·/).first()).toBeVisible();
  const download = page.waitForEvent("download");
  await region.getByRole("button", { name: "Export sensitivity JSON" }).click();
  expect((await download).suggestedFilename()).toContain(
    "delivery-sensitivity-selective",
  );
  await region.scrollIntoViewIfNeeded();
  await page.screenshot({
    path: "test-results/sensitivity.png",
    fullPage: true,
  });
  expect(await (await request.get(`/api/missions/${m.id}`)).json()).toEqual(m);
  expect(
    await (await request.get(`/api/missions/${m.id}/export/json`)).json(),
  ).toEqual(original);
});
