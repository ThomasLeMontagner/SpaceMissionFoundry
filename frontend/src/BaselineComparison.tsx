import { useEffect, useMemo, useRef, useState } from "react";
import { request } from "./api";
import { compareSnapshots } from "./baselineDiff";
import type { Model } from "./types";

type Baseline = { id: string; name: string; revision: number };
function StoredValue({ value }: { value: unknown }) {
  if (value === undefined) return <em>Not present</em>;
  if (value === null) return <em>Not specified</em>;
  if (typeof value === "object") {
    if ("value" in value && "unit" in value)
      return (
        <span>
          {String(value.value)} {String(value.unit) || "dimensionless"}
        </span>
      );
    return <pre>{JSON.stringify(value, null, 2)}</pre>;
  }
  return <span>{String(value)}</span>;
}

export default function BaselineComparison({
  missionId,
  revision,
}: {
  missionId: string;
  revision: number;
}) {
  const [baselines, setBaselines] = useState<Baseline[]>([]);
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [snapshots, setSnapshots] = useState<[Model, Model] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [metadata, setMetadata] = useState(false);
  const [kind, setKind] = useState("");
  const [search, setSearch] = useState("");
  const [reload, setReload] = useState(0);
  const generation = useRef(0);
  useEffect(() => {
    const current = ++generation.current;
    setSnapshots(null);
    setError("");
    setLoading(true);
    setBaselines([]);
    setKind("");
    setSearch("");
    setMetadata(false);
    setFrom("");
    setTo("");
    request(`/missions/${missionId}/baselines`)
      .then((rows: Baseline[]) => {
        if (current !== generation.current) return;
        setBaselines(rows);
        setFrom(rows.at(-2)?.id || rows[0]?.id || "");
        setTo(rows.at(-1)?.id || "");
      })
      .catch((e) => {
        if (current === generation.current) setError(e.message);
      })
      .finally(() => {
        if (current === generation.current) setLoading(false);
      });
    return () => {
      generation.current++;
    };
  }, [missionId, revision, reload]);
  const changes = useMemo(
    () => (snapshots ? compareSnapshots(...snapshots, metadata) : []),
    [snapshots, metadata],
  );
  const kinds = [...new Set(changes.map((c) => c.kind))].sort();
  const visible = changes.filter(
    (c) =>
      (!kind || c.kind === kind) &&
      JSON.stringify(c).toLowerCase().includes(search.toLowerCase()),
  );
  const label = (model: Model) =>
    `${model.entities[model.baseline!]?.title || model.baseline} · revision ${model.revision}`;
  return (
    <section
      className="panel baseline-comparison"
      aria-label="Baseline comparison"
    >
      <h2>Compare saved baselines</h2>
      <p>
        Inspect two immutable snapshots. Values are shown as recorded, including
        their units; comparison does not recalculate the design.
      </p>
      {error && (
        <>
          <p role="alert" className="error">
            {error}
          </p>
          <button disabled={loading} onClick={() => setReload((v) => v + 1)}>
            Reload baseline list
          </button>
        </>
      )}
      {!loading && !error && baselines.length < 2 && (
        <p>Save at least two baselines to compare different design versions.</p>
      )}
      <div className="comparison">
        {(
          [
            ["From baseline", from, setFrom],
            ["To baseline", to, setTo],
          ] as const
        ).map(([name, value, setter]) => (
          <label key={name}>
            {name}
            <select
              aria-label={name}
              value={value}
              disabled={loading || !baselines.length}
              onChange={(e) => {
                setter(e.target.value);
                setSnapshots(null);
                setError("");
              }}
            >
              {!baselines.length && (
                <option value="">No saved baselines</option>
              )}
              {baselines.map((b) => (
                <option value={b.id} key={b.id}>
                  {b.name} · revision {b.revision}
                </option>
              ))}
            </select>
          </label>
        ))}
      </div>
      <button
        disabled={loading || !from || !to}
        onClick={async () => {
          const current = ++generation.current;
          setLoading(true);
          setError("");
          setSnapshots(null);
          setKind("");
          setSearch("");
          try {
            const pair = (await Promise.all(
              [from, to].map((id) =>
                request(
                  `/missions/${missionId}/export/json?baseline_id=${encodeURIComponent(id)}`,
                ),
              ),
            )) as [Model, Model];
            if (current !== generation.current) return;
            if (
              pair.some(
                (m, i) => m.id !== missionId || m.baseline !== [from, to][i],
              )
            )
              throw Error(
                "The returned snapshots do not match the selected baselines.",
              );
            setSnapshots(pair);
          } catch (e) {
            if (current === generation.current) setError((e as Error).message);
          } finally {
            if (current === generation.current) setLoading(false);
          }
        }}
      >
        {loading ? "Loading baselines…" : "Compare baselines"}
      </button>
      {snapshots && (
        <>
          <p className="notice">
            From {label(snapshots[0])} → To {label(snapshots[1])}
          </p>
          <label className="check">
            <input
              type="checkbox"
              checked={metadata}
              onChange={(e) => {
                setMetadata(e.target.checked);
                setKind("");
              }}
            />{" "}
            Include audit timestamps and revision metadata
          </label>
          <p className="muted">
            {metadata
              ? "All stored fields are included."
              : "Audit timestamps, elapsed calculation time, and revision provenance are hidden. Engineering values, states, evidence links and added/removed objects remain visible."}
          </p>
          <p role="status">
            {changes.filter((c) => c.change === "Added").length} added ·{" "}
            {changes.filter((c) => c.change === "Removed").length} removed ·{" "}
            {changes.filter((c) => c.change === "Changed").length} changed
          </p>
          <div className="comparison">
            <label>
              Object type
              <select
                aria-label="Comparison object type"
                value={kind}
                onChange={(e) => setKind(e.target.value)}
              >
                <option value="">All types</option>
                {kinds.map((k) => (
                  <option key={k}>{k}</option>
                ))}
              </select>
            </label>
            <label>
              Find a change
              <input
                aria-label="Find a change"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Requirement, input, result or object ID"
              />
            </label>
          </div>
          {!changes.length && (
            <p>
              No differences between these snapshots
              {metadata ? "." : " with audit metadata hidden."}
            </p>
          )}
          {!!changes.length && !visible.length && (
            <p>No changes match these filters.</p>
          )}
          {visible.map((change) => (
            <details
              key={`${change.collection}:${change.id}`}
              className="baseline-change"
            >
              <summary>
                {change.change} · {change.kind} · {change.title}{" "}
                <small>({change.id})</small>
              </summary>
              <div className="diff-table-wrap">
                <table>
                  <caption>{change.title}: stored field differences</caption>
                  <thead>
                    <tr>
                      <th scope="col">Field</th>
                      <th scope="col">From</th>
                      <th scope="col">To</th>
                    </tr>
                  </thead>
                  <tbody>
                    {change.fields.map((field, index) => (
                      <tr key={index}>
                        <th scope="row">
                          {field.path.length
                            ? field.path
                                .map((p) => p.replaceAll("_", " "))
                                .join(" › ")
                            : "Entire object"}
                        </th>
                        <td>
                          <StoredValue value={field.before} />
                        </td>
                        <td>
                          <StoredValue value={field.after} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </details>
          ))}
        </>
      )}
    </section>
  );
}
