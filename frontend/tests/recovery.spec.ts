import { execFileSync } from "node:child_process";
import { expect, test } from "@playwright/test";

test("interrupted collaboration resumes its checkpoint after reload", async ({
  page,
  request,
}) => {
  const scenario = await (await request.get("/api/scenario")).json();
  const name = "Checkpoint recovery " + Date.now();
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
      reason: "Recovery test inputs",
    });
    await post("advance");
  }
  const original = m.entities["selective-data-inputs"];
  await post("collaboration", {
    candidate: "selective",
    goal: "Increase observation time",
  });
  const run: any = Object.values(m.entities).find(
    (e: any) => e.data.workflow === "duty-collaboration",
  );
  await post(`collaboration/${run.id}/step`);
  await post(`collaboration/${run.id}/step`);
  const evidence = m.entities[run.id].data.payload;
  // Only the disposable Playwright database is opened. Persist the task-start
  // checkpoint a killed worker would leave, with its lease already expired.
  execFileSync(
    "../.venv/bin/python",
    [
      "-c",
      `
import sys
from datetime import UTC, datetime, timedelta
from uuid import uuid4
from app.persistence.store import Store
from app.services.collaboration import get_run, record
store = Store("sqlite:////tmp/mission-foundry-iteration-e2e.db")
old = store.get(sys.argv[1])
model = old.model_copy(deep=True)
run = get_run(model, sys.argv[2])
run.data.update(status="working", attempt=str(uuid4()), attempts=3,
                task_lease=(datetime.now(UTC)-timedelta(seconds=1)).isoformat())
record(run, "started", "orchestrator", "bus", "Interrupted browser test task")
store.save(model, "test", "Interrupted execution fixture", old)
store.engine.dispose()
`,
      m.id,
      run.id,
    ],
    { cwd: "../backend" },
  );
  await page.goto("/");
  await page.getByRole("button", { name: name + " →", exact: true }).click();
  await page
    .getByRole("button", { name: "Agent collaboration", exact: true })
    .click();
  const view = page.getByRole("region", {
    name: "Agent collaboration",
    exact: true,
  });
  const recovery = view.getByRole("region", { name: "Execution recovery" });
  await expect(
    recovery.getByText(/2 completed tasks will be preserved/),
  ).toBeVisible();
  await expect(
    view.getByRole("button", { name: "Run next task" }),
  ).toBeDisabled();
  await recovery.screenshot({ path: "test-results/checkpoint-recovery.png" });
  await recovery
    .getByRole("button", { name: "Resume from checkpoint" })
    .click();
  await expect(recovery).not.toBeVisible();
  m = await (await request.get(`/api/missions/${m.id}`)).json();
  expect(m.entities[run.id].data.completed).toEqual([
    "payload",
    "evaluate_payload",
  ]);
  expect(m.entities[run.id].data.payload).toEqual(evidence);
  expect(m.entities[run.id].data.attempts).toBe(3);
  await view.getByRole("button", { name: "Run until review" }).click();
  await expect(
    view.getByText(/5 of 5 execution tasks completed/),
  ).toBeVisible();
  m = await (await request.get(`/api/missions/${m.id}`)).json();
  expect(m.entities[run.id].data.attempts).toBe(6);
  expect(m.entities[run.id].data.status).toBe("awaiting_approval");
  expect(m.entities["selective-data-inputs"]).toEqual(original);
  expect(
    m.entities[run.id].data.events.filter((e: any) => e.type === "recovered"),
  ).toHaveLength(1);
});
