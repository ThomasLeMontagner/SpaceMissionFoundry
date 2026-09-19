import { expect, test } from "@playwright/test";

test("review an interface contract, expose stale checks, block mismatch and correct compatible units", async ({
  page,
  request,
}) => {
  const scenario = await (await request.get("/api/scenario")).json();
  const name = "Interface study " + Date.now();
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
      reason: "Prepare interface test",
    });
    await post("advance");
  }
  await page.goto("/");
  await page.getByRole("button", { name: name + " →", exact: true }).click();
  await page.getByRole("button", { name: "Interfaces", exact: true }).click();
  const checks = page.getByRole("region", {
    name: "Interface consistency checks",
  });
  await expect(checks.getByText(/contract: unverified/)).toBeVisible();
  await page.getByRole("button", { name: "Pause", exact: true }).click();
  await checks
    .getByRole("button", { name: "Inspect or edit interface contract" })
    .click();
  await page
    .getByRole("button", { name: "Edit interface data contract" })
    .click();
  await page.getByLabel("Sender protocol", { exact: true }).fill("SpaceWire");
  await page.getByLabel("Receiver protocol", { exact: true }).fill("SpaceWire");
  await page.getByLabel("Sender peak rate", { exact: true }).fill("20");
  await page.getByLabel("Receiver capacity", { exact: true }).fill("10000");
  await page
    .getByLabel("Receiver capacity unit", { exact: true })
    .fill("kbit/s");
  await page
    .getByLabel("Change rationale", { exact: true })
    .fill("Compare declared sender throughput with receiver capacity");
  await page
    .getByRole("button", { name: "Propose change", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Resume", exact: true }),
  ).toBeEnabled();
  await page.getByRole("button", { name: "Trades", exact: true }).click();
  await expect(
    page.getByText("Resolve pending proposals before selecting a concept."),
  ).toBeVisible();
  await expect(
    page.getByRole("button", {
      name: "Select B · Event-selective imaging + X-band",
      exact: true,
    }),
  ).toBeDisabled();
  await page.getByRole("button", { name: "Interfaces", exact: true }).click();
  await page
    .getByRole("button", { name: "Approve design change", exact: true })
    .click();
  await expect(checks.getByText(/Stale — review changes/)).toBeVisible();
  await page.getByRole("button", { name: "Resume", exact: true }).click();
  await expect(checks.getByText(/rate: fail/)).toBeVisible();
  await page.getByRole("button", { name: "Trades", exact: true }).click();
  await expect(
    page.getByRole("button", {
      name: "Select B · Event-selective imaging + X-band",
      exact: true,
    }),
  ).toBeDisabled();
  await page.getByRole("button", { name: "Interfaces", exact: true }).click();
  await checks
    .getByRole("button", { name: "Inspect or edit interface contract" })
    .click();
  await page
    .getByRole("button", { name: "Edit interface data contract" })
    .click();
  await page.getByLabel("Receiver capacity", { exact: true }).fill("20000");
  await page
    .getByLabel("Change rationale", { exact: true })
    .fill("Match the approved sender peak rate in compatible units");
  await page
    .getByRole("button", { name: "Propose change", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Approve design change", exact: true })
    .click();
  await expect(checks.getByText(/rate: pass/)).toBeVisible();
  await expect(checks.getByText(/protocol: pass/)).toBeVisible();
  await page.screenshot({
    path: "test-results/interface-checks.png",
    fullPage: true,
  });
  await page.getByRole("button", { name: "Trades", exact: true }).click();
  await expect(
    page.getByRole("button", {
      name: "Select B · Event-selective imaging + X-band",
      exact: true,
    }),
  ).toBeEnabled();
});
