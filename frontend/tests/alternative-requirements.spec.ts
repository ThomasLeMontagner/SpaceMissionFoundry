import { expect, test } from "@playwright/test";

test("mission requirements block submission with explicit unverified evidence", async ({
  page,
  request,
}) => {
  const scenario = await (await request.get("/api/scenario")).json();
  const name = "Requirement study " + Date.now();
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
    .getByRole("checkbox", { name: /Check mission requirements/ })
    .check();
  await view
    .getByRole("button", { name: "Start collaboration", exact: true })
    .click();
  await view.getByRole("button", { name: "Run until review" }).click();
  await expect
    .poll(
      async () => {
        model = await (await request.get(`/api/missions/${model.id}`)).json();
        return (
          Object.values(model.entities).find(
            (e: any) => e.data.check_requirements,
          ) as any
        )?.data.status;
      },
      { timeout: 30000 },
    )
    .toBe("blocked");
  const comparison = view.getByRole("region", {
    name: "Data-system alternatives",
    exact: true,
  });
  await expect(
    comparison.getByText(/Mission requirement checks enabled/),
  ).toBeVisible();
  await comparison
    .getByText("Bus B: rationale and evidence", { exact: true })
    .click();
  await expect(
    comparison
      .getByLabel("bus B requirement checks")
      .getByText(/\(must\): Unverified/)
      .first(),
  ).toBeVisible();
  await expect(
    comparison
      .getByLabel("bus B requirement checks")
      .getByText(/No supported quantitative criterion/)
      .first(),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Approve design change", exact: true }),
  ).toHaveCount(0);
  expect(model.entities["selective-data-inputs"]).toEqual(original);
  await comparison.screenshot({
    path: "test-results/requirement-alternatives.png",
  });
});
