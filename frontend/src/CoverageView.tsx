import type { Model } from "./types";

function duration(value: any) {
  return value && typeof value.value === "number"
    ? `${(value.value / 60).toFixed(1)} min`
    : "Unknown";
}

export default function CoverageView({
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
  const analysis = model.entities["mission-access-analysis"];
  const parameter = model.entities["mission-access-inputs"];
  const result = analysis?.data.outputs;
  const current =
    analysis?.state === "accepted" && analysis.data.status === "valid";
  const paths: string[] = [];
  let previous: number | undefined;
  for (const point of current ? result.ground_track : []) {
    const x = point.longitude + 180,
      y = 90 - point.latitude;
    if (previous === undefined || Math.abs(point.longitude - previous) > 180)
      paths.push(`M${x} ${y}`);
    else paths[paths.length - 1] += ` L${x} ${y}`;
    previous = point.longitude;
  }
  return (
    <section
      className="panel coverage-view"
      aria-label="Coverage and ground access"
    >
      <h2>Coverage & ground access</h2>
      <p>
        Preliminary geometry for configured point targets and hypothetical
        stations. This shared orbit/footprint model applies to both candidates;
        it does not simulate payload scheduling or full regional coverage.
      </p>
      {!parameter && (
        <>
          <p>
            Coverage inputs have not been approved for this mission. Existing
            calculations and historical baselines retain their recorded scope.
          </p>
          {model.baseline ? (
            <p>
              Reopen the baseline under Baselines & replay before adding
              coverage inputs.
            </p>
          ) : model.entities["mission-orbit-inputs"] ? (
            <button disabled={busy} onClick={onInitialize}>
              Propose coverage inputs
            </button>
          ) : (
            <p>Approve architecture and editable orbit inputs first.</p>
          )}
        </>
      )}
      {parameter && (
        <button
          className="secondary"
          disabled={busy}
          onClick={() => onInspect(parameter.id)}
        >
          Inspect or edit coverage inputs
        </button>
      )}
      {analysis && (
        <button
          className="secondary"
          disabled={busy}
          onClick={() => onInspect(analysis.id)}
        >
          Inspect access calculation evidence
        </button>
      )}
      {!current && (
        <p className="notice">
          {analysis?.state === "stale"
            ? "Stale — review changes and recalculate before using coverage results."
            : analysis?.data.status === "invalid"
              ? `Calculation invalid: ${(analysis.data.errors || []).join("; ")}`
              : "Coverage results are unverified until the approved inputs are calculated."}
        </p>
      )}
      {current && (
        <>
          <p className="notice">
            Delivery latency remains unverified. Geometric visibility does not
            establish successful transmission, processing, or delivery.
          </p>
          <div className="comparison">
            <div>
              <h3>Analysis window</h3>
              <p>
                {duration(result.horizon)} · sampling{" "}
                {result.sample_step.value.toFixed(2)} s
              </p>
              <small>
                Time zero uses the declared Earth rotation and orbital position
                angles, not a calendar date.
              </small>
            </div>
            <div>
              <h3>Target points observed</h3>
              <p>
                {result.targets.filter((t: any) => t.observed).length} /{" "}
                {result.targets.length}
              </p>
              <small>
                Unobserved does not prove a target is never accessible.
              </small>
            </div>
            <div>
              <h3>Network visibility</h3>
              <p>{duration(result.contact)} total</p>
              <small>
                {duration(result.daily_contact)} per day averaged over this
                horizon; overlaps between stations count once.
              </small>
            </div>
          </div>
          <h3>Sampled ground track</h3>
          <p className="muted">
            Longitude/latitude grid · green targets · orange stations. Track
            display is downsampled; calculations use the full step resolution.
          </p>
          <svg
            viewBox="-22 -12 408 212"
            role="img"
            aria-label="Sampled ground track on a longitude and latitude grid"
          >
            <rect width="360" height="180" fill="#edf4f5" />
            {[-180, -120, -60, 0, 60, 120, 180].map((lon) => (
              <g key={lon}>
                <line
                  x1={lon + 180}
                  x2={lon + 180}
                  y1={0}
                  y2={180}
                  stroke="#cad6dc"
                  strokeWidth=".5"
                />
                <text x={lon + 180} y={190} textAnchor="middle" fontSize="5">
                  {lon}°
                </text>
              </g>
            ))}
            {[-90, -60, -30, 0, 30, 60, 90].map((lat) => (
              <g key={lat}>
                <line
                  x1={0}
                  x2={360}
                  y1={90 - lat}
                  y2={90 - lat}
                  stroke="#cad6dc"
                  strokeWidth=".5"
                />
                <text x={-4} y={92 - lat} textAnchor="end" fontSize="5">
                  {lat}°
                </text>
              </g>
            ))}
            {paths.map((d, i) => (
              <path
                key={i}
                d={d}
                fill="none"
                stroke="#527a9a"
                strokeWidth=".55"
              />
            ))}
            {[
              ...result.targets.map((t: any) => ({ ...t, color: "#087b62" })),
              ...result.stations.map((s: any) => ({ ...s, color: "#ad5c09" })),
            ].map((site: any, i: number) => {
              const degrees = (q: any) =>
                ["rad", "radian"].includes(q.unit)
                  ? (q.value * 180) / Math.PI
                  : q.value;
              return (
                <circle
                  key={i}
                  cx={degrees(site.longitude) + 180}
                  cy={90 - degrees(site.latitude)}
                  r="2"
                  fill={site.color}
                >
                  <title>{site.name}</title>
                </circle>
              );
            })}
          </svg>
          <h3>Target observation opportunities</h3>
          {result.targets.map((target: any) => (
            <details key={target.name}>
              <summary>
                {target.name} · {target.windows.length} sampled windows ·
                largest in-window gap {duration(target.largest_gap)}
              </summary>
              <p>
                Maximum observed start-to-start revisit:{" "}
                {duration(target.max_observed_revisit)}. Edge gaps are censored
                by the analysis window.
              </p>
              <Windows events={target.windows} />
            </details>
          ))}
          <h3>Station visibility windows</h3>
          {result.stations.map((station: any) => (
            <details key={station.name}>
              <summary>
                {station.name} · {station.windows.length} windows ·{" "}
                {duration(station.contact)} contact
              </summary>
              <Windows events={station.windows} />
            </details>
          ))}
          <p>
            Largest sampled wait from an observation-window start to a following
            network contact: {duration(result.opportunity_wait)}.{" "}
            {result.observations_without_later_contact} observation windows have
            no later contact in this horizon. This is an optimistic contact
            opportunity estimate, not delivery latency.
          </p>
          <p>
            Link-budget contact durations remain separate approved assumptions.
            Visibility does not reserve station time or change those budgets
            automatically.
          </p>
          <details>
            <summary>Model assumptions and limits</summary>
            <ul>
              {result.limitations.map((line: string) => (
                <li key={line}>{line}</li>
              ))}
            </ul>
          </details>
        </>
      )}
    </section>
  );
}

function Windows({ events }: { events: any[] }) {
  if (!events.length)
    return (
      <p>
        No access detected within this sampled horizon. Short events may be
        missed.
      </p>
    );
  return (
    <div className="diff-table-wrap">
      <table>
        <caption>
          Elapsed time from relative epoch; boundaries have sample-scale
          uncertainty
        </caption>
        <thead>
          <tr>
            <th>Start (min)</th>
            <th>End (min)</th>
            <th>Duration (min)</th>
            <th>At horizon edge</th>
          </tr>
        </thead>
        <tbody>
          {events.map((w, i) => (
            <tr key={i}>
              <td>{(w.start_s / 60).toFixed(2)}</td>
              <td>{(w.end_s / 60).toFixed(2)}</td>
              <td>{(w.duration_s / 60).toFixed(2)}</td>
              <td>{w.boundary_truncated ? "Yes" : "No"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
