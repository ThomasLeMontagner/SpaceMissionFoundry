import { expect, test } from "@playwright/test";

test("collaboration records negotiation and waits for owner approval", async ({
  page,
  request,
}) => {
  const scenario = await (await request.get("/api/scenario")).json();
  const name = "Collaboration " + Date.now();
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
      reason: "Approve reference inputs for collaboration test",
    });
    await post("advance");
  }
  const original = m.entities["selective-data-inputs"].data.inputs.duty;
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
    .getByRole("button", { name: "Start collaboration", exact: true })
    .click();
  await expect(view.getByText(/SIMULATION · no model calls/)).toBeVisible();
  await page.getByRole("button", { name: "Pause", exact: true }).click();
  await expect(
    view.getByRole("button", { name: "Run next task" }),
  ).toBeDisabled();
  await page.getByRole("button", { name: "Resume", exact: true }).click();
  for (let i = 1; i <= 5; i++) {
    await view.getByRole("button", { name: "Run next task" }).click();
    await expect(
      view.getByText(new RegExp(`${i} of 5 execution tasks completed`)),
    ).toBeVisible();
  }
  m = await (await request.get(`/api/missions/${m.id}`)).json();
  expect(m.entities["selective-data-inputs"].data.inputs.duty).toEqual(
    original,
  );
  const graph = view.getByRole("region", { name: "Agent interaction graph" });
  await graph
    .getByRole("button", { name: "Engineering tools → Bus & Ground: 1 events" })
    .click();
  await expect(view.locator("li.collaboration-event")).toHaveCount(1);
  await expect(view.locator("li.collaboration-event")).toContainText(
    "Data or downlink constraint fails",
  );
  await view.getByRole("button", { name: "Clear graph selection" }).click();
  await expect(view.locator("li.collaboration-event")).toHaveCount(11);
  await view
    .getByRole("combobox", { name: "Event filter", exact: true })
    .selectOption("tool_result");
  await expect(view.locator("li.collaboration-event")).toHaveCount(2);
  await view.screenshot({ path: "test-results/collaboration.png" });
  await page.reload();
  await page.getByRole("button", { name: name + " →", exact: true }).click();
  await page
    .getByRole("button", { name: "Agent collaboration", exact: true })
    .click();
  await expect(view.locator("li.collaboration-event")).toHaveCount(11);
  await page.getByRole("button", { name: "Challenge", exact: true }).click();
  const clarification = view.getByRole("form", { name: "Clarify and revise" });
  await clarification
    .getByLabel("Revision feedback")
    .fill("Science needs at least 3.5 percent observation duty.");
  await clarification
    .getByLabel("Minimum observation duty fraction")
    .fill("0.035");
  await clarification
    .getByRole("button", { name: "Request revised proposal" })
    .click();
  await expect(view.getByText(/Revision round 1/)).toBeVisible();
  for (let i = 1; i <= 5; i++) {
    await view.getByRole("button", { name: "Run next task" }).click();
    await expect(
      view.getByText(new RegExp(`${i} of 5 execution tasks completed`)),
    ).toBeVisible();
  }
  await expect(view.locator("li.collaboration-event")).toHaveCount(23);
  await view.screenshot({ path: "test-results/collaboration-revision.png" });
  await page
    .getByRole("button", { name: "Approve design change", exact: true })
    .click();
  await expect(view.getByText(/Design proposal: accepted/)).toBeVisible();
  m = await (await request.get(`/api/missions/${m.id}`)).json();
  expect(m.entities["selective-data-inputs"].data.inputs.duty.value).toBe(
    0.035,
  );
});
