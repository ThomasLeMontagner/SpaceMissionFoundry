import type { Model } from "./types";

export type FieldChange = { path: string[]; before: unknown; after: unknown };
export type ObjectChange = {
  id: string;
  kind: string;
  title: string;
  collection: string;
  change: "Added" | "Removed" | "Changed";
  fields: FieldChange[];
};

const metadata = new Set(["revision", "created_at", "modified_at"]);
const provenance = new Set([
  "timestamp",
  "elapsed_seconds",
  "source_revision",
  "input_revision",
  "evidence_revision",
  "evaluated_revision",
  "analysis_source_revision",
]);
const object = (value: unknown): value is Record<string, unknown> =>
  value !== null && typeof value === "object" && !Array.isArray(value);

// Key order is irrelevant; array order is meaningful except for typed relation sets.
function canonical(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(canonical);
  if (object(value))
    return Object.fromEntries(
      Object.keys(value)
        .sort()
        .map((k) => [k, canonical(value[k])]),
    );
  return value;
}

function content(value: Record<string, any>, includeMetadata: boolean) {
  const copy = structuredClone(value);
  if (!includeMetadata) {
    for (const key of metadata) delete copy[key];
    if (copy.data) for (const key of provenance) delete copy.data[key];
  }
  if (copy.relations)
    copy.relations.sort((a: any, b: any) =>
      `${a.type}:${a.target}`.localeCompare(`${b.type}:${b.target}`),
    );
  return copy;
}

function fields(
  before: unknown,
  after: unknown,
  path: string[] = [],
): FieldChange[] {
  if (JSON.stringify(canonical(before)) === JSON.stringify(canonical(after)))
    return [];
  // Keep quantities and arrays intact so units and list membership remain legible.
  if (
    object(before) &&
    object(after) &&
    !("value" in before && "unit" in before) &&
    !("value" in after && "unit" in after)
  ) {
    return [...new Set([...Object.keys(before), ...Object.keys(after)])]
      .sort()
      .flatMap((key) => fields(before[key], after[key], [...path, key]));
  }
  return [{ path, before, after }];
}

export function compareSnapshots(
  before: Model,
  after: Model,
  includeMetadata = false,
): ObjectChange[] {
  if (before.id !== after.id)
    throw Error("Only snapshots from the same mission can be compared.");
  const changes: ObjectChange[] = [];
  const {
    entities: oldEntities,
    proposals: oldProposals,
    ...oldMission
  } = before;
  const {
    entities: newEntities,
    proposals: newProposals,
    ...newMission
  } = after;
  const missionFields = fields(
    content(oldMission, includeMetadata),
    content(newMission, includeMetadata),
  );
  if (missionFields.length)
    changes.push({
      id: before.id,
      kind: "Mission",
      title: "Mission summary",
      collection: "mission",
      change: "Changed",
      fields: missionFields,
    });
  for (const [collection, left, right] of [
    ["entities", oldEntities, newEntities],
    ["proposals", oldProposals, newProposals],
  ] as const) {
    for (const id of [
      ...new Set([...Object.keys(left), ...Object.keys(right)]),
    ].sort()) {
      const oldValue: any = left[id],
        newValue: any = right[id];
      const differences = fields(
        oldValue && content(oldValue, includeMetadata),
        newValue && content(newValue, includeMetadata),
      );
      if (!differences.length) continue;
      const value = newValue || oldValue;
      changes.push({
        id,
        kind: value.kind || "Proposal",
        title: value.title || value.proposal_type,
        collection,
        change: !oldValue ? "Added" : !newValue ? "Removed" : "Changed",
        fields: differences,
      });
    }
  }
  return changes;
}
