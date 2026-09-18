import { useState } from "react";
import { request } from "./api";
import SavedStudies from "./SavedStudies";
import type { Model } from "./types";

const parameters: Record<
  string,
  { label: string; unit: string; values: string }
> = {
  storage: {
    label: "Onboard storage",
    unit: "Mbit",
    values: "1, 10, 100, 1000",
  },
  downlink_rate: {
    label: "Downlink rate",
    unit: "Mbit/s",
    values: "0.5, 1, 5, 10",
  },
  onboard_delay: {
    label: "Onboard delay",
    unit: "minute",
    values: "0, 1, 5, 15",
  },
  ground_delay: {
    label: "Ground processing delay",
    unit: "minute",
    values: "0, 2, 10, 30",
  },
  dissemination_delay: {
    label: "Dissemination delay",
    unit: "minute",
    values: "0, 1, 5, 15",
  },
};
const number = (v: number | null | undefined, scale = 1) =>
  v == null ? "—" : (v / scale).toFixed(2);

// The parent keys this view by mission and revision, so late requests cannot show
// evidence from another mission or a superseded revision.
export default function SensitivityView({
  model,
  busy,
  onPropose,
}: {
  model: Model;
  busy: boolean;
  onPropose?: (studyId: string, trialIndex: number, reason: string) => void;
}) {
  const [candidate, setCandidate] = useState(model.selected || "selective");
  const [parameter, setParameter] = useState("ground_delay");
  const [values, setValues] = useState(parameters.ground_delay.values);
  const [unit, setUnit] = useState(parameters.ground_delay.unit);
  const [deadline, setDeadline] = useState("30");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [studyName, setStudyName] = useState("");
  const [savedId, setSavedId] = useState("");
  const [libraryVersion, setLibraryVersion] = useState(0);
  const source = model.entities[`${candidate}-delivery-analysis`];
  const ready = source?.state === "accepted" && source.data.status === "valid";
  function invalidate() {
    setResult(null);
    setError("");
    setSavedId("");
  }
  async function run(event: React.FormEvent) {
    event.preventDefault();
    invalidate();
    const parts = values.split(",").map((v) => v.trim());
    if (
      parts.length < 2 ||
      parts.length > 15 ||
      parts.some((v) => !v || !Number.isFinite(Number(v)) || Number(v) < 0)
    ) {
      setError("Enter 2–15 distinct, nonnegative numbers separated by commas.");
      return;
    }
    setLoading(true);
    try {
      setResult(
        await request(`/missions/${model.id}/sensitivity`, {
          revision: model.revision,
          candidate,
          parameter,
          values: parts.map((value) => ({ value: Number(value), unit })),
          deadline: deadline.trim()
            ? { value: Number(deadline), unit: "minute" }
            : null,
        }),
      );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }
  async function save() {
    setLoading(true);
    setError("");
    try {
      const saved = await request(`/missions/${model.id}/sensitivity-studies`, {
        name: studyName.trim(),
        study: result.study_request,
      });
      setSavedId(saved.id);
      setLibraryVersion((v) => v + 1);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }
  function download() {
    const url = URL.createObjectURL(
      new Blob([JSON.stringify(result, null, 2)], { type: "application/json" }),
    );
    const a = document.createElement("a");
    a.href = url;
    a.download = `delivery-sensitivity-${result.candidate}-r${result.source_revision}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }
  return (
    <section
      className="panel sensitivity-view"
      aria-label="Delivery sensitivity analysis"
    >
      <h2>Sensitivity analysis</h2>
      <p>
        Explore one input at a time and compare delivery outcomes against the
        current design. Studies also work on a saved baseline and never change
        its inputs or approvals.
      </p>
      <form onSubmit={run}>
        <fieldset disabled={busy || loading}>
          <legend>Study settings</legend>
          <label>
            Candidate
            <select
              value={candidate}
              onChange={(e) => {
                setCandidate(e.target.value);
                invalidate();
              }}
            >
              <option value="selective">Selective</option>
              <option value="wide">Wide</option>
            </select>
          </label>
          <label>
            Vary input
            <select
              value={parameter}
              onChange={(e) => {
                const key = e.target.value;
                setParameter(key);
                setUnit(parameters[key].unit);
                setValues(parameters[key].values);
                invalidate();
              }}
            >
              {Object.entries(parameters).map(([key, p]) => (
                <option key={key} value={key}>
                  {p.label}
                </option>
              ))}
            </select>
          </label>
          <label>
            Trial values
            <input
              value={values}
              onChange={(e) => {
                setValues(e.target.value);
                invalidate();
              }}
              required
            />
          </label>
          <label>
            Trial unit
            <input
              value={unit}
              onChange={(e) => {
                setUnit(e.target.value);
                invalidate();
              }}
              required
            />
          </label>
          <label>
            Exploratory deadline (minutes, optional)
            <input
              type="number"
              min="0"
              step="any"
              value={deadline}
              onChange={(e) => {
                setDeadline(e.target.value);
                invalidate();
              }}
            />
          </label>
          <p>
            Use 2–15 distinct values separated by commas. The exploratory
            deadline does not change a mission requirement. Downlink-rate trials
            also recalculate RF margin.
          </p>
          <button type="submit" disabled={!ready}>
            {loading ? "Running study…" : "Run sensitivity study"}
          </button>
        </fieldset>
      </form>
      {!ready && (
        <p className="notice">
          Current valid delivery evidence is required. Approve delivery inputs
          and recalculate in Data delivery first.
        </p>
      )}
      {error && <p role="alert">{error}</p>}
      {result && (
        <>
          <h3>
            {parameters[result.parameter].label} · {result.candidate}
          </h3>
          <p>
            Source revision {result.source_revision}
            {result.baseline_id ? " · saved baseline" : ""} · reference and
            trials use the same recorded geometry and workload.
          </p>
          <button className="secondary" onClick={download}>
            Export sensitivity JSON
          </button>
          <p>
            Save this study to revisit it later, or export JSON. Unsaved results
            disappear when settings, revision or tab changes. To adopt a value,
            edit the corresponding Design inputs and follow the normal review
            workflow.
          </p>
          <label>
            Study name
            <input
              maxLength={120}
              value={studyName}
              disabled={loading || !!savedId}
              onChange={(e) => setStudyName(e.target.value)}
            />
          </label>
          <button
            disabled={
              busy ||
              loading ||
              !!savedId ||
              !studyName.trim() ||
              model.archived
            }
            onClick={() => void save()}
          >
            {savedId ? "Study saved" : "Save study"}
          </button>
          <div className="diff-table-wrap">
            <table>
              <caption>
                Conditional delivery outcomes. A dash means unavailable or
                incomplete evidence; delivered-only latency does not verify the
                whole workload.
              </caption>
              <thead>
                <tr>
                  <th>Case / input</th>
                  <th>Delivered / total</th>
                  <th>Pending</th>
                  <th>Dropped</th>
                  <th>Full-workload max (min)</th>
                  <th>Delivered-only max (min)</th>
                  <th>Peak queue (Mbit)</th>
                  <th>RF margin (dB)</th>
                  <th>Study deadline</th>
                  <th>Approved criteria (exploratory comparison)</th>
                </tr>
              </thead>
              <tbody>
                {[result.reference, ...result.trials].map(
                  (row: any, i: number) => {
                    const o = row.delivery_analysis.outputs;
                    return (
                      <tr key={i}>
                        <th>
                          {row.reference ? "Reference" : `Trial ${i}`} ·{" "}
                          {row.value.value} {row.value.unit}
                        </th>
                        {row.status !== "valid" ? (
                          <td colSpan={9}>
                            Invalid: {row.delivery_analysis.errors.join("; ")}
                          </td>
                        ) : (
                          <>
                            <td>
                              {o.delivered_count} / {o.observation_count}
                            </td>
                            <td>{o.pending_count}</td>
                            <td>{o.dropped_count}</td>
                            <td>{number(o.maximum_latency?.value, 60)}</td>
                            <td>
                              {number(
                                o.delivered_only_maximum_latency?.value,
                                60,
                              )}
                            </td>
                            <td>{number(o.peak_queue?.value, 1e6)}</td>
                            <td>
                              {number(
                                row.link_analysis.outputs.link_margin_db?.value,
                              )}
                            </td>
                            <td>
                              {row.deadline_check
                                ? `${row.deadline_check.status} · ${row.deadline_check.missed_deadlines} missed · ${row.deadline_check.unresolved_deadlines} unresolved`
                                : "Not set"}
                            </td>
                            <td>
                              {row.requirement_checks
                                .map(
                                  (c: any) => `${c.requirement}: ${c.status}`,
                                )
                                .join("; ") ||
                                "No accepted numeric delivery criterion"}
                            </td>
                          </>
                        )}
                      </tr>
                    );
                  },
                )}
              </tbody>
            </table>
          </div>
          <details>
            <summary>Study assumptions and limits</summary>
            <ul>
              {result.limitations.map((s: string) => (
                <li key={s}>{s}</li>
              ))}
            </ul>
            <ul>
              {result.reference.delivery_analysis.outputs.limitations?.map(
                (s: string) => (
                  <li key={s}>{s}</li>
                ),
              )}
            </ul>
          </details>
        </>
      )}
      <SavedStudies
        key={model.id}
        missionId={model.id}
        revision={model.revision}
        refresh={libraryVersion}
        model={model}
        busy={busy || loading}
        onPropose={onPropose}
      />
    </section>
  );
}
