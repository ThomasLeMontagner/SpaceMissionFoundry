import { expect, test } from "@playwright/test";

test("cross-discipline alternatives persist all evaluated budgets on approval", async ({
  page,
  request,
}) => {
  const scenario = await (await request.get("/api/scenario")).json();
  const name = "Cross-discipline " + Date.now();
  let model = await (
    await request.post("/api/missions", {
      data: { name, brief: scenario.brief },
    })
  ).json();
  async function post(path: string, body: object = {}) {
    const response = await request.post(`/api/missions/${model.id}/${path}`, {
      data: { revision: model.revision, ...body },
    });
    expect(response.ok(), await response.text()).toBeTruthy();
    model = await response.json();
  }
  for (let i = 0; i < 3; i++) {
    const proposal: any = Object.values(model.proposals).find(
      (p: any) => p.status === "submitted",
    );
    await post(`proposals/${proposal.id}/decision`, {
      action: "accept",
      reason: "Alternative study setup",
    });
    await post("advance");
  }
  const original = model.entities["selective-data-inputs"];
  await page.goto("/");
  await page.getByRole("button", { name: name + " →", exact: true }).click();
  await page
    .getByRole("button", { name: "Agent collaboration", exact: true })
    .click();
  const view = page.getByRole("region", {
    name: "Agent collaboration",
    exact: true,
  });
  await view.getByLabel("Study type").selectOption("cross-discipline");
  await view.getByLabel("Minimum storage (Gbit)").fill("300");
  await view.getByLabel("Maximum storage (Gbit)").fill("500");
  await view.getByLabel("Storage mass (kg/Gbit)", { exact: true }).fill("0.01");
  await view
    .getByLabel("Storage power (W/Gbit)", { exact: true })
    .fill("0.001");
  await view.getByLabel("Additional observation active power (W)").fill("1");
  await view
    .getByLabel("Processing active power per compression-ratio increment (W)")
    .fill("0.01");
  await view
    .getByLabel("Assumption basis and applicability")
    .fill("Browser test concept assumptions; not qualified hardware");
  await view
    .getByRole("button", { name: "Start collaboration", exact: true })
    .click();
  await view.getByRole("button", { name: "Run until review" }).click();
  await expect(view.getByText(/5 of 5 execution tasks completed/)).toBeVisible({
    timeout: 15000,
  });
  const comparison = view.getByRole("region", {
    name: "Data-system alternatives",
    exact: true,
  });
  await expect(comparison.getByRole("table")).toHaveCount(2);
  await expect(
    comparison.getByText(/Systems recommends Bus option/),
  ).toBeVisible();
  await expect(comparison.getByText(/storage 300–500 Gbit/)).toBeVisible();
  await comparison.screenshot({ path: "test-results/cross-discipline.png" });
  model = await (await request.get(`/api/missions/${model.id}`)).json();
  expect(model.entities["selective-data-inputs"]).toEqual(original);
  const run: any = Object.values(model.entities).find(
    (e: any) => e.data.study === "cross-discipline",
  );
  const selected = run.data.bus.alternatives.find(
    (a: any) => a.id === run.data.selected_alternative,
  );
  expect(selected.storage_gbit).toBeLessThanOrEqual(500);
  await page
    .getByRole("button", { name: "Approve design change", exact: true })
    .click();
  await expect(
    page.getByText(/Recalculation required|Trade study/).first(),
  ).toBeVisible();
  await expect
    .poll(async () => {
      const current = await (
        await request.get(`/api/missions/${model.id}`)
      ).json();
      return current.entities[run.id].data.status;
    })
    .toBe("accepted");
  model = await (await request.get(`/api/missions/${model.id}`)).json();
  const evaluated = run.data.evaluate_bus.alternatives.find(
    (a: any) => a.id === selected.id,
  );
  expect(model.entities["selective-mass-inputs"].data.inputs).toEqual(
    evaluated.mass.inputs,
  );
  const { period, eclipse, ...powerInputs } = evaluated.power.inputs;
  expect(model.entities["selective-power-inputs"].data.inputs).toEqual(
    powerInputs,
  );
  const inputs = model.entities["selective-data-inputs"].data.inputs;
  expect(inputs.duty.value).toBe(selected.duty);
  expect(inputs.compression.value).toBe(selected.compression);
  expect(inputs.storage).toEqual({
    value: selected.storage_gbit,
    unit: "Gbit",
  });
});
