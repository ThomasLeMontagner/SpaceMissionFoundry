import { test, expect } from "@playwright/test";

test("reviewed allocations expose target responsibility without verifying requirements", async ({
  page,
  request,
}) => {
  const scenario = await (await request.get("/api/scenario")).json();
  const name = "Allocation " + Date.now();
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
      reason: "Prepare architecture for allocation review",
    });
    await post("advance");
  }
  await page.goto("/");
  await page.getByRole("button", { name: name + " →", exact: true }).click();
  await page.getByRole("button", { name: "Requirements", exact: true }).click();
  await page.getByLabel("Requirement to clarify").selectOption("req-observe");
  const panel = page.getByRole("region", {
    name: "Requirement responsibility allocation",
    exact: true,
  });
  await panel.getByText("Allocate responsibility", { exact: true }).click();
  await panel.getByRole("checkbox", { name: /^detect —/ }).check();
  await panel.getByRole("checkbox", { name: /^imager —/ }).check();
  await panel
    .getByLabel("Allocation change rationale")
    .fill("Detection and payload own the observation responsibility");
  await panel
    .getByRole("button", { name: "Propose allocations for approval" })
    .click();
  let saved = await (await request.get(`/api/missions/${m.id}`)).json();
  expect(
    saved.entities["req-observe"].relations.filter(
      (r: any) => r.type === "allocated_to",
    ),
  ).toHaveLength(0);
  await page.getByRole("button", { name: /Conflicts.*review/i }).click();
  await page
    .getByRole("button", { name: "Approve design change", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Review affected design content" }),
  ).toBeVisible();
  await page
    .getByRole("checkbox", {
      name: "I reviewed the affected assumptions, requirements and design inputs and reaffirm this content.",
      exact: true,
    })
    .check();
  await page
    .getByRole("button", { name: "Confirm impact review", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Review affected design content" }),
  ).not.toBeVisible();
  await expect(
    page.getByText("Working · validating and recording model changes…", {
      exact: true,
    }),
  ).not.toBeVisible();
  await page.getByRole("button", { name: "Requirements", exact: true }).click();
  await page.getByLabel("Requirement to clarify").selectOption("req-observe");
  await panel.getByText("Allocate responsibility", { exact: true }).click();
  await panel.getByLabel("Inspect allocation target").selectOption("imager");
  await expect(
    panel.getByRole("button", {
      name: "The mission shall acquire wildfire monitoring imagery over southern Europe.",
      exact: true,
    }),
  ).toBeVisible();
  saved = await (await request.get(`/api/missions/${m.id}`)).json();
  expect(saved.entities["check-req-observe-selective"].data.status).toBe(
    "unverified",
  );
  await panel.screenshot({ path: "test-results/requirement-allocation.png" });
});
