import type { Model } from "./types";

const minutes = (value: number | null | undefined) =>
  value == null ? "—" : (value / 60).toFixed(2);

export default function DeliveryView({
  model,
  busy,
  onInitialize,
  onInspect,
}: {
  model: Model;
  busy: boolean;
  onInitialize: () => void;
  onInspect: (id: string) => void;
}) {
  const configured = !!model.entities["selective-delivery-inputs"];
  return (
    <section className="panel" aria-label="Data delivery simulation">
      <h2>Data delivery</h2>
      <p>
        Follow each modeled observation from acquisition through onboard
        storage, contact-limited downlink, ground processing and dissemination.
      </p>
      <p className="notice">
        One product per target window, one FIFO radio, and assumed usable
        station access. This sampled workload differs from the daily data budget
        and does not certify operational performance.
      </p>
      {!configured &&
        (model.baseline ? (
          <p>Reopen the baseline before adding delivery inputs.</p>
        ) : model.entities["mission-access-inputs"] ? (
          <button disabled={busy} onClick={onInitialize}>
            Propose delivery inputs
          </button>
        ) : (
          <p>Approve coverage and architecture inputs first.</p>
        ))}
      {model.entities["req-latency"] && (
        <button
          className="secondary"
          disabled={busy}
          onClick={() => onInspect("req-latency")}
        >
          Configure latency requirement
        </button>
      )}
      <p>
        To check a deadline, edit the requirement and explicitly choose “Maximum
        acquisition-to-delivery latency” with a ≤ threshold. Requirement prose
        alone does not set a numeric deadline.
      </p>
      {["wide", "selective"].map((candidate) => {
        const run = model.entities[`${candidate}-delivery-analysis`];
        const result = run?.data.outputs;
        const current =
          run?.state === "accepted" && run.data.status === "valid";
        const checks = Object.values(model.entities).filter(
          (e) =>
            e.kind === "VerificationItem" &&
            e.data.candidate === candidate &&
            e.data.criterion?.metric === "delivery.maximum_latency",
        );
        return (
          <section key={candidate} aria-label={`${candidate} delivery`}>
            <h3>{candidate} candidate</h3>
            {model.entities[`${candidate}-delivery-inputs`] && (
              <button
                disabled={busy}
                className="secondary"
                onClick={() => onInspect(`${candidate}-delivery-inputs`)}
              >
                Edit {candidate} delivery delays
              </button>
            )}
            {run && (
              <button
                disabled={busy}
                className="secondary"
                onClick={() => onInspect(run.id)}
              >
                Inspect {candidate} delivery evidence
              </button>
            )}
            {!current ? (
              <p className="notice">
                {run?.state === "stale"
                  ? "Stale — review changes and recalculate before using delivery results."
                  : run?.data.status === "invalid"
                    ? `Calculation invalid: ${(run.data.errors || []).join("; ")}`
                    : "Delivery results are unverified until approved inputs are calculated."}
              </p>
            ) : (
              <>
                <p>
                  {result.delivered_count} delivered · {result.pending_count}{" "}
                  pending · {result.dropped_count} dropped ·{" "}
                  {result.observation_count} products
                </p>
                <p>
                  Maximum latency for complete workload:{" "}
                  {minutes(result.maximum_latency?.value)} min. Delivered
                  products only:{" "}
                  {minutes(result.delivered_only_maximum_latency?.value)} min.
                </p>
                <p>
                  Peak onboard queue:{" "}
                  {(result.peak_queue.value / 1e6).toFixed(2)} Mbit · remaining:{" "}
                  {(result.queued.value / 1e6).toFixed(2)} Mbit · effective
                  rate: {(result.effective_rate.value / 1e6).toFixed(2)} Mbit/s.
                </p>
                <svg
                  viewBox="0 0 600 130"
                  role="img"
                  aria-label={`${candidate} onboard queue over analysis horizon`}
                  style={{ width: "100%", maxHeight: 180 }}
                >
                  <path
                    d={result.queue_trace
                      .map(
                        (p: any, i: number) =>
                          `${i ? "L" : "M"}${10 + (p.time_s / result.horizon.value) * 580} ${110 - (p.queued_bits / Math.max(1, result.peak_queue.value)) * 100}`,
                      )
                      .join(" ")}
                    fill="none"
                    stroke="#087b62"
                    strokeWidth="2"
                  />
                  <text x="10" y="128" fontSize="10">
                    0 min
                  </text>
                  <text x="590" y="128" textAnchor="end" fontSize="10">
                    {minutes(result.horizon.value)} min
                  </text>
                </svg>
                {checks.map((check) => (
                  <p key={check.id}>
                    <button
                      className="secondary"
                      disabled={busy}
                      onClick={() => onInspect(check.id)}
                    >
                      {check.title}
                    </button>{" "}
                    {check.state === "stale" ? "stale" : check.data.status} ·{" "}
                    {check.data.missed_deadlines ?? "—"} missed ·{" "}
                    {check.data.unresolved_deadlines ?? "—"} unresolved
                  </p>
                ))}
                <div className="diff-table-wrap">
                  <table>
                    <caption>
                      Elapsed minutes from the access model’s relative epoch. A
                      dash means no completed event within the horizon.
                    </caption>
                    <thead>
                      <tr>
                        <th>Product</th>
                        <th>Acquired</th>
                        <th>Downlinked</th>
                        <th>Delivered</th>
                        <th>Latency</th>
                        <th>Status</th>
                        <th>Deadline checks</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.observations.map((job: any) => (
                        <tr key={job.id}>
                          <td>
                            {job.id}
                            {job.boundary_truncated ? " (truncated)" : ""}
                          </td>
                          <td>{minutes(job.acquired_at_s)}</td>
                          <td>{minutes(job.downlinked_at_s)}</td>
                          <td>{minutes(job.delivered_at_s)}</td>
                          <td>{minutes(job.latency_s)}</td>
                          <td>{job.status.replaceAll("_", " ")}</td>
                          <td>
                            {checks
                              .filter((c) => c.state !== "stale")
                              .map(
                                (c) =>
                                  `${c.data.requirement}: ${c.data.deadline_outcomes?.find((o: any) => o.id === job.id)?.status ?? "unverified"}`,
                              )
                              .join("; ") || "No numeric deadline"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {!result.observation_count && (
                  <p>
                    No observation products in this horizon; delivery is
                    unverified.
                  </p>
                )}
                <details>
                  <summary>Delivery assumptions and limits</summary>
                  <ul>
                    {result.limitations.map((s: string) => (
                      <li key={s}>{s}</li>
                    ))}
                  </ul>
                </details>
              </>
            )}
          </section>
        );
      })}
    </section>
  );
}
