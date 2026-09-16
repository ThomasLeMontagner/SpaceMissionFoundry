import { expect, test } from "vitest";
import { compareSnapshots } from "./baselineDiff";
import type { Entity, Model } from "./types";

const entity = (id: string): Entity => ({
  id,
  kind: "Parameter",
  title: id,
  state: "accepted",
  owner: "human",
  revision: 1,
  classification: "Explicit assumption",
  relations: [],
  data: {},
});
function model(): Model {
  return {
    id: "mission",
    name: "Mission",
    brief: "Brief",
    revision: 1,
    phase: "Baselined",
    entities: { input: entity("input") },
    proposals: {},
    selected: "selective",
    baseline: "baseline-1",
    paused: false,
    steps: 1,
  };
}

test("compares quantities, missing values and added/removed objects without mutation", () => {
  const before = model();
  before.entities.input.data = {
    inputs: { duty: { value: 2, unit: "percent" } },
    optional: null,
  };
  before.entities.removed = entity("removed");
  const after = structuredClone(before);
  after.entities.input.data.inputs.duty = { value: 0.1, unit: "dimensionless" };
  delete after.entities.input.data.optional;
  delete after.entities.removed;
  after.entities.added = entity("added");
  const original = structuredClone(before);
  const diff = compareSnapshots(before, after);
  expect(diff.map((c) => [c.id, c.change])).toEqual([
    ["added", "Added"],
    ["input", "Changed"],
    ["removed", "Removed"],
  ]);
  expect(diff[1].fields).toContainEqual({
    path: ["data", "inputs", "duty"],
    before: { value: 2, unit: "percent" },
    after: { value: 0.1, unit: "dimensionless" },
  });
  expect(diff[1].fields).toContainEqual({
    path: ["data", "optional"],
    before: null,
    after: undefined,
  });
  expect(before).toEqual(original);
  const reverse = compareSnapshots(after, before);
  expect(reverse[0].change).toBe("Removed");
  expect(reverse[2].change).toBe("Added");
  expect(compareSnapshots(before, before)).toEqual([]);
});

test("metadata filter preserves changed engineering status and relations are order independent", () => {
  const before = model();
  before.entities.input.relations = [
    { type: "depends_on", target: "a" },
    { type: "depends_on", target: "b" },
  ];
  before.entities.input.data = {
    evaluated_revision: 1,
    result: { value: 10, unit: "kg" },
    status: "pass",
  };
  const after = structuredClone(before);
  after.revision = 2;
  after.entities.input.revision = 2;
  after.entities.input.data = {
    status: "pass",
    result: { unit: "kg", value: 10 },
    evaluated_revision: 2,
  };
  after.entities.input.relations.reverse();
  expect(compareSnapshots(before, after)).toEqual([]);
  expect(compareSnapshots(before, after, true)).toHaveLength(2);
  after.entities.input.data.status = "fail";
  expect(compareSnapshots(before, after)[0].fields).toEqual([
    { path: ["data", "status"], before: "pass", after: "fail" },
  ]);
});

test("includes mission selection and proposal changes and rejects unrelated missions", () => {
  const before = model(),
    after = structuredClone(before);
  after.selected = "wide";
  after.proposals.p = {
    id: "p",
    proposal_type: "design change",
    agent: "human",
    target_revision: 1,
    status: "accepted",
    rationale: "More capacity",
    expected_consequences: "Recalculate",
    confidence: 1,
    operations: [],
  };
  expect(compareSnapshots(before, after).map((c) => c.kind)).toEqual([
    "Mission",
    "Proposal",
  ]);
  after.id = "another-mission";
  expect(() => compareSnapshots(before, after)).toThrow("same mission");
});
