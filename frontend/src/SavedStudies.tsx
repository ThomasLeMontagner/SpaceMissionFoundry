import { useEffect, useState } from "react";
import { request } from "./api";
import type { Model } from "./types";

type Summary = {
  id: string;
  name: string;
  created_at: string;
  source_revision: number;
  candidate: string;
  parameter: string;
};
const minutes = (q: any) =>
  q == null ? "Unknown" : `${(q.value / 60).toFixed(2)} min`;

export default function SavedStudies({
  missionId,
  revision,
  refresh,
  model,
  busy = false,
  onPropose,
}: {
  missionId: string;
  revision: number;
  refresh: number;
  model?: Model;
  busy?: boolean;
  onPropose?: (studyId: string, trialIndex: number, reason: string) => void;
}) {
  const [items, setItems] = useState<Summary[]>([]);
  const [left, setLeft] = useState("");
  const [right, setRight] = useState("");
  const [records, setRecords] = useState<any[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [retry, setRetry] = useState(0);
  const [choice, setChoice] = useState<any>(null);
  const [reason, setReason] = useState("");
  useEffect(() => {
    let active = true;
    setError("");
    void request(`/missions/${missionId}/sensitivity-studies`)
      .then((data) => {
        if (active) setItems(data);
      })
      .catch((e) => {
        if (active) setError(e.message);
      });
    return () => {
      active = false;
    };
  }, [missionId, refresh, retry]);
  useEffect(() => {
    let active = true;
    setRecords([]);
    setError("");
    const ids = [left, right].filter(Boolean);
    setChoice(null);
    if (!ids.length) {
      setLoading(false);
      return;
    }
    setLoading(true);
    void Promise.all(
      ids.map((id) =>
        request(`/missions/${missionId}/sensitivity-studies/${id}`),
      ),
    )
      .then((data) => {
        if (active) setRecords(data);
      })
      .catch((e) => {
        if (active) setError(e.message);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [missionId, left, right, retry]);
  function download(record: any) {
    const url = URL.createObjectURL(
      new Blob([JSON.stringify(record, null, 2)], { type: "application/json" }),
    );
    const a = document.createElement("a");
    a.href = url;
    a.download = `saved-study-${record.id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }
  const options = items.map((item) => (
    <option key={item.id} value={item.id}>
      {item.name} · {item.candidate} · {item.parameter} · r
      {item.source_revision} · {item.created_at}
    </option>
  ));
  return (
    <section aria-label="Saved sensitivity studies">
      <h3>Saved studies</h3>
      {model?.baseline && (
        <p className="notice">
          To propose a trial as a design change, reopen the baseline in
          Baselines & replay first. Saved evidence will remain unchanged.
        </p>
      )}
      <p>
        Saved evidence stays unchanged when your design evolves. Compare source
        revisions, candidates, horizons and deadlines before interpreting
        differences. Studies do not approve or update mission inputs.
      </p>
      {error && (
        <p role="alert">
          {error}{" "}
          <button onClick={() => setRetry((v) => v + 1)}>
            Retry saved studies
          </button>
        </p>
      )}
      {!items.length && !error && (
        <p>No saved studies yet. Run a study and give it a name to save it.</p>
      )}
      {!!items.length && (
        <div className="comparison">
          <label>
            View saved study
            <select
              aria-label="View saved study"
              value={left}
              onChange={(e) => {
                setRecords([]);
                setLeft(e.target.value);
              }}
            >
              <option value="">Choose a study</option>
              {options}
            </select>
          </label>
          <label>
            Compare with study (optional)
            <select
              aria-label="Compare with study (optional)"
              value={right}
              onChange={(e) => {
                setRecords([]);
                setRight(e.target.value);
              }}
            >
              <option value="">No comparison</option>
              {options}
            </select>
          </label>
        </div>
      )}
      {loading && <p role="status">Loading saved evidence…</p>}
      {records.length === 2 &&
        (records[0].result.parameter !== records[1].result.parameter ||
          records[0].result.source_revision !==
            records[1].result.source_revision ||
          records[0].result.candidate !== records[1].result.candidate ||
          JSON.stringify(records[0].result.deadline) !==
            JSON.stringify(records[1].result.deadline)) && (
          <p className="notice">
            These studies use different settings or source designs. Differences
            are not attributable to a single changed input.
          </p>
        )}
      {choice && model && (
        <section className="panel" aria-label="Trial change preview">
          <h4>
            Propose trial {choice.index + 1} from {choice.record.name}
          </h4>
          <p>
            {choice.record.result.candidate} · {choice.record.result.parameter}{" "}
            · source revision {choice.record.result.source_revision}
          </p>
          <p>
            Current input: {choice.current?.value} {choice.current?.unit} →
            proposed: {choice.value.value} {choice.value.unit}
          </p>
          <p>
            Only this input will be proposed. Study results and deadline
            outcomes are not approved evidence; accepted changes require fresh
            calculations and review.
          </p>
          <label>
            Trial change rationale
            <input
              value={reason}
              minLength={3}
              maxLength={2000}
              disabled={busy}
              onChange={(e) => setReason(e.target.value)}
            />
          </label>
          <button
            disabled={
              busy ||
              !!model.baseline ||
              !!model.archived ||
              reason.trim().length < 3
            }
            onClick={() =>
              onPropose?.(choice.record.id, choice.index, reason.trim())
            }
          >
            Submit trial change proposal
          </button>
          <button
            className="secondary"
            disabled={busy}
            onClick={() => setChoice(null)}
          >
            Cancel trial proposal
          </button>
        </section>
      )}
      <div className="comparison">
        {records.map((record, i) => {
          const result = record.result;
          return (
            <article
              key={`${record.id}:${i}`}
              aria-label={`Saved study ${record.name}`}
            >
              <h4>{record.name}</h4>
              <p>
                Saved {record.created_at} · source revision{" "}
                {result.source_revision}{" "}
                {result.source_revision === revision
                  ? "(current revision)"
                  : "(historical revision)"}
                {result.baseline_id ? " · baseline source" : ""}
              </p>
              <p>
                {result.candidate} · varying {result.parameter} · horizon{" "}
                {minutes(
                  result.reference.delivery_analysis.inputs.access.horizon,
                )}{" "}
                · study deadline{" "}
                {result.deadline
                  ? `${result.deadline.value} ${result.deadline.unit}`
                  : "not set"}
              </p>
              <button className="secondary" onClick={() => download(record)}>
                Export saved study {record.name}
              </button>
              <div className="diff-table-wrap">
                <table>
                  <caption>{record.name} — recorded outcomes</caption>
                  <thead>
                    <tr>
                      <th>Case / input</th>
                      <th>Delivery and deadline outcome</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[result.reference, ...result.trials].map(
                      (row: any, j: number) => {
                        const o = row.delivery_analysis.outputs;
                        return (
                          <tr key={j}>
                            <th>
                              {j ? `Trial ${j}` : "Reference"} ·{" "}
                              {row.value.value} {row.value.unit}
                              {j > 0 && onPropose && model && (
                                <button
                                  className="secondary"
                                  disabled={
                                    busy ||
                                    !!model.baseline ||
                                    !!model.archived ||
                                    row.status !== "valid"
                                  }
                                  onClick={() => {
                                    const mapping: Record<
                                      string,
                                      [string, string]
                                    > = {
                                      storage: ["data", "storage"],
                                      downlink_rate: ["link", "rate"],
                                      onboard_delay: [
                                        "delivery",
                                        "onboard_delay",
                                      ],
                                      ground_delay: [
                                        "delivery",
                                        "ground_delay",
                                      ],
                                      dissemination_delay: [
                                        "delivery",
                                        "dissemination_delay",
                                      ],
                                    };
                                    const [tool, field] =
                                      mapping[result.parameter];
                                    setChoice({
                                      record,
                                      index: j - 1,
                                      value: row.value,
                                      current:
                                        model.entities[
                                          `${result.candidate}-${tool}-inputs`
                                        ]?.data.inputs[field],
                                    });
                                    setReason("");
                                  }}
                                >
                                  Propose trial {j} from {record.name}
                                </button>
                              )}
                            </th>
                            {row.status !== "valid" ? (
                              <td>
                                Invalid:{" "}
                                {row.delivery_analysis.errors.join("; ")}
                              </td>
                            ) : (
                              <td>
                                {o.delivered_count} / {o.observation_count}{" "}
                                delivered
                                <br />
                                {o.pending_count} pending · {o.dropped_count}{" "}
                                dropped
                                <br />
                                Full-workload max:{" "}
                                <span>{minutes(o.maximum_latency)}</span>
                                <br />
                                Deadline:{" "}
                                {row.deadline_check
                                  ? `${row.deadline_check.status} · ${row.deadline_check.missed_deadlines} missed · ${row.deadline_check.unresolved_deadlines} unresolved`
                                  : "Not set"}
                              </td>
                            )}
                          </tr>
                        );
                      },
                    )}
                  </tbody>
                </table>
              </div>
              <details>
                <summary>Recorded assumptions and evidence</summary>
                <ul>
                  {result.limitations.map((line: string) => (
                    <li key={line}>{line}</li>
                  ))}
                </ul>
                <pre>{JSON.stringify(result.study_request, null, 2)}</pre>
                <p>
                  Full per-product and RF evidence is included in the saved JSON
                  export.
                </p>
              </details>
            </article>
          );
        })}
      </div>
    </section>
  );
}
