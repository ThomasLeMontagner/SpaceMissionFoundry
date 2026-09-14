import { useState } from "react";
import { request } from "./api";
import type { Entity, Model } from "./types";

type Changes = Record<string, unknown>;
const names: Record<string, string> = {
  duty: "Observation duty cycle",
  compression: "Compression ratio",
  contact: "Daily ground contact",
  limit: "Mass allocation",
  margin: "Mass contingency",
  storage: "Onboard storage",
  solar: "Solar generation",
  battery: "Battery capacity",
  depth_of_discharge: "Battery depth of discharge",
  altitude: "Orbit altitude",
};

function QuantityFields({
  value,
  path = [],
  update,
}: {
  value: any;
  path?: string[];
  update: (path: string[], value: string | number) => void;
}) {
  if (
    value &&
    typeof value === "object" &&
    "value" in value &&
    "unit" in value
  ) {
    const label = names[path.at(-1)!] || path.join(" / ").replaceAll("_", " ");
    return (
      <div className="quantity-fields">
        <label>
          {label}
          <input
            required
            type="number"
            min="0"
            step="any"
            value={value.value}
            onChange={(e) =>
              update(
                [...path, "value"],
                e.target.value === "" ? "" : Number(e.target.value),
              )
            }
          />
        </label>
        <label>
          {label} unit
          <input
            value={value.unit}
            onChange={(e) => update([...path, "unit"], e.target.value)}
            placeholder="dimensionless"
          />
        </label>
      </div>
    );
  }
  if (value && typeof value === "object")
    return (
      <>
        {Object.entries(value).map(([k, v]) => (
          <QuantityFields
            key={k}
            value={v}
            path={[...path, k]}
            update={update}
          />
        ))}
      </>
    );
  return null;
}

export default function DesignEditor({
  entity,
  missionId,
  revision,
  onProposed,
}: {
  entity: Entity;
  missionId: string;
  revision: number;
  onProposed: (model: Model) => void;
}) {
  const [editing, setEditing] = useState(false),
    [reason, setReason] = useState(""),
    [error, setError] = useState(""),
    [saving, setSaving] = useState(false);
  const [targetRevision] = useState(revision);
  const parameter = entity.kind === "Parameter";
  const [changes, setChanges] = useState<Changes>(() =>
    parameter
      ? { inputs: structuredClone(entity.data.inputs) }
      : {
          title: entity.title,
          rationale: entity.data.rationale,
          ...(entity.kind === "Assumption"
            ? {
                impact: entity.data.impact,
                confidence: entity.data.confidence,
                validation_plan: entity.data.validation_plan,
              }
            : {
                level: entity.data.level,
                priority: entity.data.priority,
                verification_method: entity.data.verification_method,
              }),
        },
  );
  function update(path: string[], value: string | number) {
    setChanges((previous) => {
      const next = structuredClone(previous);
      let node: any = next.inputs;
      for (const k of path.slice(0, -1)) node = node[k];
      node[path.at(-1)!] = value;
      return next;
    });
  }
  if (!editing)
    return (
      <button className="secondary" onClick={() => setEditing(true)}>
        Edit {parameter ? "calculation inputs" : entity.kind.toLowerCase()}
      </button>
    );
  return (
    <form
      className="design-editor"
      onSubmit={async (e) => {
        e.preventDefault();
        setSaving(true);
        setError("");
        try {
          const result = await request(
            `/missions/${missionId}/objects/${entity.id}/edit`,
            { revision: targetRevision, changes, reason },
          );
          onProposed(result);
        } catch (e) {
          setError((e as Error).message);
        } finally {
          setSaving(false);
        }
      }}
    >
      <h3>Propose a design change</h3>
      <p className="muted">
        Values remain assumptions. Approval invalidates affected results and
        automatically recalculates once inputs are reviewed and the workflow is
        running. Fractions use 0–1 or compatible percent units.
      </p>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {parameter ? (
        <QuantityFields value={changes.inputs} update={update} />
      ) : (
        Object.entries(changes).map(([key, value]) => (
          <label key={key} htmlFor={`design-edit-${key}`}>
            {key.replaceAll("_", " ")}
            {["priority", "level", "verification_method"].includes(key) ? (
              <select
                id={`design-edit-${key}`}
                value={String(value)}
                onChange={(e) =>
                  setChanges({ ...changes, [key]: e.target.value })
                }
              >
                {(key === "priority"
                  ? ["must", "should", "could"]
                  : key === "level"
                    ? ["stakeholder", "system", "subsystem"]
                    : [
                        "analysis",
                        "test",
                        "inspection",
                        "demonstration",
                        "review",
                      ]
                ).map((v) => (
                  <option key={v}>{v}</option>
                ))}
              </select>
            ) : key === "confidence" ? (
              <input
                required
                id={`design-edit-${key}`}
                type="number"
                min="0"
                max="1"
                step="0.05"
                value={String(value)}
                onChange={(e) =>
                  setChanges({ ...changes, [key]: Number(e.target.value) })
                }
              />
            ) : (
              <textarea
                id={`design-edit-${key}`}
                required
                rows={2}
                value={String(value)}
                onChange={(e) =>
                  setChanges({ ...changes, [key]: e.target.value })
                }
              />
            )}
          </label>
        ))
      )}
      <label>
        Change rationale
        <textarea
          required
          minLength={3}
          value={reason}
          onChange={(e) => setReason(e.target.value)}
        />
      </label>
      <div className="actions">
        <button disabled={saving}>
          {saving ? "Submitting…" : "Propose change"}
        </button>
        <button
          className="secondary"
          type="button"
          disabled={saving}
          onClick={() => setEditing(false)}
        >
          Cancel edit
        </button>
      </div>
    </form>
  );
}
