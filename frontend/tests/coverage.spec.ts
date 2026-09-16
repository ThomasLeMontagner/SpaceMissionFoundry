import { expect, test } from "@playwright/test";

test("coverage assumptions can change while stale geometry stays hidden until recalculation", async ({
  page,
  request,
}) => {
  const scenario = await (await request.get("/api/scenario")).json();
  const name = "Coverage scenario " + Date.now();
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
    const proposal: any = Object.values(m.proposals).find(
      (p: any) => p.status === "submitted",
    );
    await post(`proposals/${proposal.id}/decision`, {
      action: "accept",
      reason: "Approve explicit reference geometry for browser test",
    });
    await post("advance");
  }
  const oldContact = m.entities["selective-link-inputs"].data.inputs.contact;
  await page.goto("/");
  await page.getByRole("button", { name: name + " →", exact: true }).click();
  await page
    .getByRole("button", { name: "Coverage & access", exact: true })
    .click();
  const coverage = page.getByRole("region", {
    name: "Coverage and ground access",
    exact: true,
  });
  await expect(coverage.getByRole("img")).toBeVisible();
  await expect(
    coverage.getByText(/Delivery latency remains unverified/),
  ).toBeVisible();
  await coverage.scrollIntoViewIfNeeded();
  await page.screenshot({ path: "test-results/coverage-access.png" });
  await page.getByRole("button", { name: "Pause", exact: true }).click();
  await coverage
    .getByRole("button", { name: "Inspect or edit coverage inputs" })
    .click();
  await page.getByRole("button", { name: "Edit calculation inputs" }).click();
  await page.getByLabel("Orbit inclination", { exact: true }).fill("0");
  await page.getByRole("button", { name: "Add target", exact: true }).click();
  await page
    .getByLabel("Target 4 name", { exact: true })
    .fill("Southern test point");
  await page.getByLabel("targets / 3 / latitude", { exact: true }).fill("-35");
  await page.getByLabel("targets / 3 / longitude", { exact: true }).fill("20");
  await page
    .getByLabel("Change rationale", { exact: true })
    .fill("Evaluate equatorial geometry and a southern point target.");
  await page
    .getByRole("button", { name: "Propose change", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Approve design change", exact: true })
    .click();
  await expect(coverage.getByText(/Stale — review changes/)).toBeVisible();
  await expect(coverage.getByRole("img")).toHaveCount(0);
  await page.getByRole("button", { name: "Resume", exact: true }).click();
  await expect(coverage.getByRole("img")).toBeVisible();
  await expect(coverage.getByText("0 / 4", { exact: true })).toBeVisible();
  const revised = await (await request.get(`/api/missions/${m.id}`)).json();
  expect(revised.entities["check-req-latency-selective"].data.status).toBe(
    "unverified",
  );
  expect(revised.entities["selective-link-inputs"].data.inputs.contact).toEqual(
    oldContact,
  );
  expect(
    revised.entities["mission-access-analysis"].data.inputs.targets[3].latitude
      .value,
  ).toBe(-35);
});
