import { useEffect, useState } from "react";
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
  inclination: "Orbit inclination",
  raan: "Ascending node angle",
  argument_of_latitude: "Initial orbital position angle",
  earth_rotation_angle: "Initial Earth rotation angle",
  duration: "Analysis duration",
  step: "Sampling step",
  footprint_width: "Ground footprint diameter",
  minimum_elevation: "Minimum station elevation",
};

function QuantityFields({
  value,
  path = [],
  update,
}: {
  value: any;
  path?: string[];
  update: (path: string[], value: unknown) => void;
}) {
  if (Array.isArray(value) && ["targets", "stations"].includes(path[0])) {
    const label = path[0] === "targets" ? "Target" : "Station";
    return (
      <fieldset>
        <legend>
          {path[0] === "targets" ? "Point targets" : "Ground stations"}
        </legend>
        {value.map((site, index) => (
          <fieldset key={index}>
            <legend>
              {label} {index + 1}
            </legend>
            <label>
              {label} {index + 1} name
              <input
                required
                maxLength={80}
                value={site.name}
                onChange={(e) =>
                  update([...path, String(index), "name"], e.target.value)
                }
              />
            </label>
            <QuantityFields
              value={site}
              path={[...path, String(index)]}
              update={update}
            />
            <button
              type="button"
              className="secondary"
              disabled={value.length === 1}
              onClick={() =>
                update(
                  path,
                  value.filter((_, i) => i !== index),
                )
              }
            >
              Remove {label.toLowerCase()} {index + 1}
            </button>
          </fieldset>
        ))}
        <button
          type="button"
          className="secondary"
          disabled={value.length >= (path[0] === "targets" ? 12 : 8)}
          onClick={() =>
            update(path, [
              ...value,
              {
                name: `${label} ${value.length + 1}`,
                latitude: { value: 0, unit: "deg" },
                longitude: { value: 0, unit: "deg" },
              },
            ])
          }
        >
          Add {label.toLowerCase()}
        </button>
      </fieldset>
    );
  }
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
            min={
              path.at(-1) === "latitude" || path.at(-1) === "longitude"
                ? undefined
                : 0
            }
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
  const [metrics, setMetrics] = useState<
    Record<string, { label: string; unit: string }>
  >({});
  useEffect(() => {
    if (editing && entity.kind === "Requirement")
      request("/requirement-metrics")
        .then(setMetrics)
        .catch((e) => setError(e.message));
  }, [editing, entity.kind]);
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
  const criterion: any =
    "criterion" in changes ? changes.criterion : entity.data.criterion;
  function update(path: string[], value: unknown) {
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
        Object.entries(changes)
          .filter(([key]) => key !== "criterion")
          .map(([key, value]) => (
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
      {entity.kind === "Requirement" && (
        <fieldset>
          <legend>Quantitative verification</legend>
          <p className="muted">
            Choose an output that verifies this statement. Units are converted
            automatically. Passing a concept calculation is conditional on its
            assumptions.
          </p>
          <label>
            Measured output
            <select
              aria-label="Measured output"
              value={criterion?.metric || ""}
              onChange={(e) => {
                const metric = e.target.value;
                setChanges({
                  ...changes,
                  criterion: metric
                    ? {
                        metric,
                        operator: "<=",
                        threshold: { value: 0, unit: metrics[metric].unit },
                      }
                    : null,
                });
              }}
            >
              <option value="">Unverified — no quantitative check</option>
              {Object.entries(metrics).map(([key, metric]) => (
                <option key={key} value={key}>
                  {metric.label}
                </option>
              ))}
            </select>
          </label>
          {criterion && (
            <>
              <label>
                Comparison
                <select
                  aria-label="Comparison"
                  value={criterion.operator}
                  onChange={(e) =>
                    setChanges({
                      ...changes,
                      criterion: { ...criterion, operator: e.target.value },
                    })
                  }
                >
                  <option value="<=">At most (≤)</option>
                  {criterion.metric !== "delivery.maximum_latency" && (
                    <option value=">=">At least (≥)</option>
                  )}
                </select>
              </label>
              <label>
                Required value
                <input
                  required
                  aria-label="Required value"
                  type="number"
                  min="0"
                  step="any"
                  value={criterion.threshold.value}
                  onChange={(e) =>
                    setChanges({
                      ...changes,
                      criterion: {
                        ...criterion,
                        threshold: {
                          ...criterion.threshold,
                          value:
                            e.target.value === "" ? "" : Number(e.target.value),
                        },
                      },
                    })
                  }
                />
              </label>
              <label>
                Requirement unit
                <input
                  required
                  aria-label="Requirement unit"
                  value={criterion.threshold.unit}
                  onChange={(e) =>
                    setChanges({
                      ...changes,
                      criterion: {
                        ...criterion,
                        threshold: {
                          ...criterion.threshold,
                          unit: e.target.value,
                        },
                      },
                    })
                  }
                />
              </label>
            </>
          )}
        </fieldset>
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
