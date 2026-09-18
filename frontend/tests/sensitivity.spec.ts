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
  await region
    .getByLabel("Study name", { exact: true })
    .fill("Baseline delays");
  await region.getByRole("button", { name: "Save study", exact: true }).click();
  await expect(
    region.getByRole("button", { name: "Study saved", exact: true }),
  ).toBeDisabled();
  await region.getByLabel("Exploratory deadline (minutes, optional)").fill("1");
  await region.getByRole("button", { name: "Run sensitivity study" }).click();
  await expect(region.getByRole("table")).toBeVisible();
  await region
    .getByLabel("Study name", { exact: true })
    .fill("Tighter deadline");
  await region.getByRole("button", { name: "Save study", exact: true }).click();
  await expect(
    region.getByRole("button", { name: "Study saved", exact: true }),
  ).toBeDisabled();
  await page.reload();
  await page.getByRole("button", { name: name + " →", exact: true }).click();
  await page
    .getByRole("button", { name: "Sensitivity analysis", exact: true })
    .click();
  const saved = await (
    await request.get(`/api/missions/${m.id}/sensitivity-studies`)
  ).json();
  expect(saved).toHaveLength(2);
  await region
    .getByLabel("View saved study", { exact: true })
    .selectOption(saved.find((s: any) => s.name === "Baseline delays").id);
  await region
    .getByLabel("Compare with study (optional)")
    .selectOption(saved.find((s: any) => s.name === "Tighter deadline").id);
  await expect(region.getByRole("table")).toHaveCount(2);
  await expect(
    region.getByText(/not attributable to a single changed input/),
  ).toBeVisible();
  const savedDownload = page.waitForEvent("download");
  await region
    .getByRole("button", {
      name: "Export saved study Baseline delays",
      exact: true,
    })
    .click();
  expect((await savedDownload).suggestedFilename()).toContain("saved-study-");
  await page.screenshot({
    path: "test-results/saved-studies.png",
    fullPage: true,
  });
  expect(await (await request.get(`/api/missions/${m.id}`)).json()).toEqual(m);
  expect(
    await (await request.get(`/api/missions/${m.id}/export/json`)).json(),
  ).toEqual(original);
  const savedEvidence = await (
    await request.get(
      `/api/missions/${m.id}/sensitivity-studies/${saved.find((s: any) => s.name === "Baseline delays").id}`,
    )
  ).json();
  await expect(
    region.getByRole("button", {
      name: "Propose trial 1 from Baseline delays",
      exact: true,
    }),
  ).toBeDisabled();
  await post("reopen", {
    reason: "Propose a study-backed processing improvement",
  });
  await page.reload();
  await page.getByRole("button", { name: name + " →", exact: true }).click();
  await page
    .getByRole("button", { name: "Sensitivity analysis", exact: true })
    .click();
  await region
    .getByLabel("View saved study", { exact: true })
    .selectOption(savedEvidence.id);
  await region
    .getByRole("button", {
      name: "Propose trial 1 from Baseline delays",
      exact: true,
    })
    .click();
  const preview = page.getByRole("region", { name: "Trial change preview" });
  await expect(
    preview.getByText(/Current input: 120 s → proposed: 0 minute/),
  ).toBeVisible();
  await preview
    .getByLabel("Trial change rationale")
    .fill("Reduce processing time using the saved trade evidence");
  await preview
    .getByRole("button", { name: "Submit trial change proposal" })
    .click();
  await expect(
    page.getByText(/From saved study “Baseline delays”/),
  ).toBeVisible();
  const pendingModel = await (
    await request.get(`/api/missions/${m.id}`)
  ).json();
  expect(
    pendingModel.entities["selective-delivery-inputs"].data.inputs.ground_delay
      .value,
  ).toBe(120);
  await page
    .getByRole("button", { name: "Approve design change", exact: true })
    .click();
  await expect
    .poll(
      async () =>
        (await (await request.get(`/api/missions/${m.id}`)).json()).phase,
    )
    .toBe("Trade study");
  const changed = await (await request.get(`/api/missions/${m.id}`)).json();
  expect(
    changed.entities["selective-delivery-inputs"].data.inputs.ground_delay,
  ).toEqual({ value: 0, unit: "minute" });
  expect(
    await (
      await request.get(
        `/api/missions/${m.id}/sensitivity-studies/${savedEvidence.id}`,
      )
    ).json(),
  ).toEqual(savedEvidence);
  expect(
    await (
      await request.get(
        `/api/missions/${m.id}/export/json?baseline_id=${original.baseline}`,
      )
    ).json(),
  ).toEqual(original);
});
