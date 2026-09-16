import { test, expect } from "@playwright/test";

test("edit duty cycle, correct downlink conflict, approve a second immutable baseline", async ({
  page,
  request,
}) => {
  let m: any;
  async function post(path: string, body: object = {}) {
    const response = await request.post(`/api/missions/${m.id}/${path}`, {
      data: { revision: m.revision, ...body },
    });
    expect(response.ok(), await response.text()).toBeTruthy();
    m = await response.json();
  }
  const brief = await (await request.get("/api/scenario")).json();
  const name = "Design iteration " + Date.now();
  m = await (
    await request.post("/api/missions", { data: { name, brief: brief.brief } })
  ).json();
  for (let i = 0; i < 3; i++) {
    const p: any = Object.values(m.proposals).find(
      (p: any) => p.status === "submitted",
    );
    await post(`proposals/${p.id}/decision`, {
      action: "accept",
      reason: "Simulated owner approval to prepare browser iteration fixture",
    });
    await post("advance");
  }
  await post("select", {
    candidate: "selective",
    weights: { science: 0.35, capacity: 0.45, simplicity: 0.2 },
    reason: "Original compliant concept",
  });
  for (let i = 0; i < 3; i++) await post("advance");
  await post("baseline", { name: "Original duty baseline", confirm: true });
  const firstId = m.baseline;
  const original = await (
    await request.get(`/api/missions/${m.id}/export/json`)
  ).json();
  await page.goto("/");
  await page.getByRole("button", { name: name + " →", exact: true }).click();
  await page
    .getByRole("button", { name: "Baselines & replay", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Reopen baseline for design changes" })
    .click();
  await page.getByRole("button", { name: "Pause", exact: true }).click();
  await page
    .getByRole("button", { name: "Design inputs", exact: true })
    .click();
  await page.getByRole("button", { name: /selective · data inputs/ }).click();
  await page.getByRole("button", { name: "Edit calculation inputs" }).click();
  await page.getByLabel("Observation duty cycle", { exact: true }).fill("0.1");
  await page
    .getByLabel("Change rationale", { exact: true })
    .fill("Increase observation time to test data delivery capacity.");
  await page
    .getByRole("button", { name: "Propose change", exact: true })
    .click();
  await expect(page.getByText("Compare proposed change")).toBeVisible();
  await page.getByRole("button", { name: "Approve design change" }).click();
  await page.getByRole("button", { name: "Overview", exact: true }).click();
  await expect(page.getByText("Stale — recalculate").first()).toBeVisible();
  await page.getByRole("button", { name: "Resume", exact: true }).click();
  await expect(page.getByText("Constraint violation")).toBeVisible();
  await page.getByRole("button", { name: "Trades", exact: true }).click();
  await expect(
    page.getByRole("button", {
      name: "Select B · Event-selective imaging + X-band",
    }),
  ).toBeDisabled();
  await page
    .getByRole("button", { name: "Conflicts & review", exact: true })
    .click();
  await page
    .getByRole("button", { name: /ReviewFinding \/ selective-conflict/ })
    .click();
  await expect(page.getByRole("dialog")).toContainText("open");
  await page.getByRole("button", { name: "Close details" }).click();
  await page
    .getByRole("button", { name: "Design inputs", exact: true })
    .click();
  await page.getByRole("button", { name: /selective · link inputs/ }).click();
  await page.getByRole("button", { name: "Edit calculation inputs" }).click();
  await page.getByLabel("Daily ground contact", { exact: true }).fill("120");
  await page
    .getByLabel("Change rationale", { exact: true })
    .fill(
      "Propose additional daily contacts; remains a ground-network assumption.",
    );
  await page
    .getByRole("button", { name: "Propose change", exact: true })
    .click();
  await page.getByRole("button", { name: "Approve design change" }).click();
  await page.getByRole("button", { name: "Trades", exact: true }).click();
  await page
    .getByRole("button", {
      name: "Select B · Event-selective imaging + X-band",
    })
    .click();
  await page.getByRole("button", { name: "Overview", exact: true }).click();
  for (const name of [
    "Run independent review",
    "Propose finding resolution",
    "Verify resolution independently",
  ])
    await page.getByRole("button", { name }).click();
  await page
    .getByRole("button", { name: "Baselines & replay", exact: true })
    .click();
  await page
    .getByLabel("Baseline name", { exact: true })
    .fill("Revised duty baseline");
  await expect(
    page.getByRole("button", { name: "Approve immutable baseline" }),
  ).toBeDisabled();
  await page.getByRole("checkbox").check();
  await page
    .getByRole("button", { name: "Approve immutable baseline" })
    .click();
  await page.getByRole("button", { name: "Load baseline history" }).click();
  await expect(
    page.getByText("Original duty baseline", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Revised duty baseline", exact: true }),
  ).toBeVisible();
  const download = page.waitForEvent("download");
  await page
    .getByRole("button", { name: "Export Original duty baseline JSON" })
    .click();
  await download;
  const preserved = await (
    await request.get(
      `/api/missions/${m.id}/export/json?baseline_id=${firstId}`,
    )
  ).json();
  expect(preserved).toEqual(original);
  const latest = await (
    await request.get(`/api/missions/${m.id}/export/json`)
  ).json();
  expect(latest.baseline).not.toBe(firstId);
  expect(latest.entities["selective-data-inputs"].data.inputs.duty.value).toBe(
    0.1,
  );
  expect(latest.entities["selective-link"].data.capacity.value).toBeCloseTo(
    50.4e9,
    0,
  );
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({
    path: "test-results/design-iteration.png",
    fullPage: true,
  });
  const comparison = page.getByRole("region", {
    name: "Baseline comparison",
    exact: true,
  });
  await comparison
    .getByLabel("From baseline", { exact: true })
    .selectOption(firstId);
  await comparison
    .getByLabel("To baseline", { exact: true })
    .selectOption(latest.baseline);
  await comparison
    .getByRole("button", { name: "Compare baselines", exact: true })
    .click();
  await expect(comparison.getByRole("status")).toBeVisible();
  await comparison
    .getByLabel("Comparison object type", { exact: true })
    .selectOption("Parameter");
  await comparison
    .getByText(/Changed · Parameter · selective · data inputs/)
    .click();
  const dutyRow = comparison
    .getByRole("row")
    .filter({ hasText: "data › inputs › duty" });
  await expect(dutyRow).toContainText("0.02 dimensionless");
  await expect(dutyRow).toContainText("0.1 dimensionless");
  await comparison.scrollIntoViewIfNeeded();
  await page.screenshot({ path: "test-results/baseline-comparison.png" });
  await comparison
    .getByLabel("From baseline", { exact: true })
    .selectOption(latest.baseline);
  await comparison
    .getByRole("button", { name: "Compare baselines", exact: true })
    .click();
  await expect(
    comparison.getByText(/No differences between these snapshots/),
  ).toBeVisible();
  expect(
    await (
      await request.get(
        `/api/missions/${m.id}/export/json?baseline_id=${firstId}`,
      )
    ).json(),
  ).toEqual(original);
  expect(
    await (
      await request.get(
        `/api/missions/${m.id}/export/json?baseline_id=${latest.baseline}`,
      )
    ).json(),
  ).toEqual(latest);
  await page
    .getByRole("button", { name: "Reopen baseline for design changes" })
    .click();
  await page.getByRole("button", { name: "Requirements", exact: true }).click();
  await page
    .getByRole("button", { name: /Requirement \/ req-latency/ })
    .click();
  await page
    .getByRole("button", { name: "Edit requirement", exact: true })
    .click();
  await page
    .getByRole("textbox", { name: "title", exact: true })
    .fill("Deliver useful imagery within 20 minutes of acquisition.");
  await page
    .getByLabel("Change rationale", { exact: true })
    .fill("Explore a tighter latency target; feasibility still unverified.");
  await page
    .getByRole("button", { name: "Propose change", exact: true })
    .click();
  await page.getByRole("button", { name: "Approve design change" }).click();
  await expect(
    page.getByRole("heading", { name: "Review affected design content" }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Confirm impact review" }),
  ).toBeDisabled();
  await page.getByRole("checkbox").check();
  await page.getByRole("button", { name: "Confirm impact review" }).click();
  await expect(
    page.getByRole("heading", { name: "Review affected design content" }),
  ).toHaveCount(0);
  await page.getByRole("button", { name: "Trades", exact: true }).click();
  await expect(
    page.getByRole("button", {
      name: "Select B · Event-selective imaging + X-band",
    }),
  ).toBeEnabled();
});
