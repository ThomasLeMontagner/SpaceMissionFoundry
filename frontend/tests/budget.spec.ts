import { expect, test } from "@playwright/test";

test("owner-configured execution window stops tasks and permits cancellation", async ({
  page,
  request,
}) => {
  const scenario = await (await request.get("/api/scenario")).json();
  const name = "Budget window " + Date.now();
  let model = await (
    await request.post("/api/missions", {
      data: { name, brief: scenario.brief },
    })
  ).json();
  async function post(path: string, body: object = {}) {
    const result = await request.post(`/api/missions/${model.id}/${path}`, {
      data: { revision: model.revision, ...body },
    });
    expect(result.ok(), await result.text()).toBeTruthy();
    model = await result.json();
  }
  for (let i = 0; i < 3; i++) {
    const proposal: any = Object.values(model.proposals).find(
      (p: any) => p.status === "submitted",
    );
    await post(`proposals/${proposal.id}/decision`, {
      action: "accept",
      reason: "Budget test setup",
    });
    await post("advance");
  }
  await page.goto("/");
  await page.getByRole("button", { name: name + " →", exact: true }).click();
  await page
    .getByRole("button", { name: "Agent collaboration", exact: true })
    .click();
  const view = page.getByRole("region", {
    name: "Agent collaboration",
    exact: true,
  });
  await view
    .getByLabel("Execution window (seconds, including pauses)")
    .fill("5");
  await view
    .getByRole("button", { name: "Start collaboration", exact: true })
    .click();
  await expect(view.getByText(/Execution window expired/)).toBeVisible({
    timeout: 12000,
  });
  await view.getByRole("button", { name: "Run until review" }).click();
  await expect(
    view.getByRole("heading", { name: /budget_blocked/ }),
  ).toBeVisible();
  model = await (await request.get(`/api/missions/${model.id}`)).json();
  const run: any = Object.values(model.entities).find(
    (e: any) => e.data.workflow === "duty-collaboration",
  );
  expect(run.data.budget.limits.elapsed_seconds).toBe(5);
  expect(run.data.attempts).toBe(0);
  expect(run.data.budget.attempts).toEqual([]);
  await view.getByRole("button", { name: "Cancel collaboration" }).click();
  await expect(view.getByRole("heading", { name: /cancelled/ })).toBeVisible();
});
