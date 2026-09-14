import { test, expect } from "@playwright/test";

test("quantitative criterion converts units and exposes calculation evidence", async ({
  page,
  request,
}) => {
  const scenario = await (await request.get("/api/scenario")).json();
  const name = "Requirement checks " + Date.now();
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
      reason: "Prepare verified browser fixture",
    });
    await post("advance");
  }
  await page.goto("/");
  await page.getByRole("button", { name: name + " →", exact: true }).click();
  await page.getByRole("button", { name: "Requirements", exact: true }).click();
  await page.getByRole("button", { name: /Requirement \/ req-launch/ }).click();
  await expect(
    page.getByRole("heading", { name: "selective · unverified", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Edit requirement", exact: true })
    .click();
  await page
    .getByRole("textbox", { name: "title", exact: true })
    .fill("Allocated spacecraft mass shall not exceed 30 kg.");
  await page
    .getByLabel("Measured output", { exact: true })
    .selectOption("mass.total");
  await page.getByLabel("Required value", { exact: true }).fill("30000");
  await page.getByLabel("Requirement unit", { exact: true }).fill("g");
  await page
    .getByLabel("Change rationale", { exact: true })
    .fill(
      "Replace envelope criterion with an explicit mass allocation for this study.",
    );
  await page
    .getByRole("button", { name: "Propose change", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Approve design change", exact: true })
    .click();
  await page.getByRole("button", { name: /Requirement \/ req-launch/ }).click();
  await expect(
    page.getByRole("heading", { name: "selective · pass", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", {
      name: "Inspect selective check and evidence",
      exact: true,
    })
    .click();
  await expect(
    page.getByRole("button", { name: /evidenced_by.*selective-mass-analysis/ }),
  ).toBeVisible();
  await page.screenshot({
    path: "test-results/requirement-evidence.png",
    fullPage: true,
  });
  await page
    .getByRole("button", { name: "Close details", exact: true })
    .click();
  await page.getByRole("button", { name: /Requirement \/ req-launch/ }).click();
  await page
    .getByRole("button", { name: "Edit requirement", exact: true })
    .click();
  await page.getByLabel("Required value", { exact: true }).fill("1");
  await page
    .getByLabel("Change rationale", { exact: true })
    .fill("Test a deliberately insufficient allocation.");
  await page
    .getByRole("button", { name: "Propose change", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Approve design change", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: /Requirement \/ req-launch/ }),
  ).toContainText("selective: fail");
  await page.getByRole("button", { name: "Trades", exact: true }).click();
  await expect(
    page.getByRole("button", {
      name: "Select B · Event-selective imaging + X-band",
      exact: true,
    }),
  ).toBeDisabled();
});
