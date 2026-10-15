import { expect, test } from "@playwright/test";

test("bounded alternatives are compared and approved as one reviewed configuration", async ({
  page,
  request,
}) => {
  const scenario = await (await request.get("/api/scenario")).json();
  const name = "Data alternatives " + Date.now();
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
  await view.getByLabel("Study type").selectOption("data-system");
  await view.getByLabel("Maximum storage (Gbit)").fill("32");
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
  await expect(comparison.getByText(/storage 1–32 Gbit/)).toBeVisible();
  await comparison.screenshot({ path: "test-results/data-alternatives.png" });
  model = await (await request.get(`/api/missions/${model.id}`)).json();
  expect(model.entities["selective-data-inputs"]).toEqual(original);
  const run: any = Object.values(model.entities).find(
    (e: any) => e.data.study === "data-system",
  );
  const selected = run.data.bus.alternatives.find(
    (a: any) => a.id === run.data.selected_alternative,
  );
  expect(selected.storage_gbit).toBeLessThanOrEqual(32);
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
  const inputs = model.entities["selective-data-inputs"].data.inputs;
  expect(inputs.duty.value).toBe(selected.duty);
  expect(inputs.compression.value).toBe(selected.compression);
  expect(inputs.storage).toEqual({
    value: selected.storage_gbit,
    unit: "Gbit",
  });
});
