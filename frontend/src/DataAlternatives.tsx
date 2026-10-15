export const defaultBounds = {
  duty_min: 0.01,
  duty_max: 0.2,
  compression_min: 1,
  compression_max: 8,
  storage_min_gbit: 1,
  storage_max_gbit: 64,
};
export type Bounds = typeof defaultBounds;

export function AlternativeBounds({
  bounds,
  onChange,
}: {
  bounds: Bounds;
  onChange: (bounds: Bounds) => void;
}) {
  return (
    <fieldset>
      <legend>Data-system design bounds</legend>
      {(
        [
          ["duty_min", "Minimum duty fraction", 0, 1],
          ["duty_max", "Maximum duty fraction", 0, 1],
          ["compression_min", "Minimum compression ratio", 1, 100],
          ["compression_max", "Maximum compression ratio", 1, 100],
          ["storage_min_gbit", "Minimum storage (Gbit)", 0.000001, 1000000],
          ["storage_max_gbit", "Maximum storage (Gbit)", 0.000001, 1000000],
        ] as const
      ).map(([key, label, min, max]) => (
        <label key={key}>
          {label}
          <input
            type="number"
            required
            step="any"
            min={min}
            max={max}
            value={bounds[key]}
            onChange={(e) =>
              onChange({ ...bounds, [key]: Number(e.target.value) })
            }
          />
        </label>
      ))}
      <p className="muted">
        Duty 0.1 means 10%. Storage uses decimal Gbit, not GB. Bounds stay fixed
        for this study. These are permitted design assumptions, not qualified
        hardware specifications.
      </p>
    </fieldset>
  );
}

export default function DataAlternatives({ data }: { data: any }) {
  const margin = (value: any) =>
    Number.isFinite(value?.value) ? value.value.toFixed(3) : "Unverified";
  const quantity = (value: any) =>
    value ? `${value.value} ${value.unit}` : "Unknown";
  const gigabits = (value: any) =>
    value && Number.isFinite(value.value)
      ? (value.value / 1e9).toFixed(3)
      : "Unknown";
  return (
    <section className="panel" aria-label="Data-system alternatives">
      <h3>
        {data.study === "cross-discipline"
          ? "Cross-discipline alternatives"
          : "Data-system alternatives"}
      </h3>
      <p>
        Source inputs: duty {quantity(data.inputs.data.duty)}, compression{" "}
        {quantity(data.inputs.data.compression)}, storage{" "}
        {quantity(data.inputs.data.storage)}. These describe the source
        revision; proposals below remain separate from accepted inputs.
      </p>
      <p>
        Owner bounds: duty {data.bounds.duty_min}–{data.bounds.duty_max};
        compression {data.bounds.compression_min}–{data.bounds.compression_max};
        storage {data.bounds.storage_min_gbit}–{data.bounds.storage_max_gbit}{" "}
        Gbit.
      </p>
      <p className="notice">
        Passing data/link checks does not verify compression image quality,
        science adequacy, or storage mass, power, cost and qualification. Review
        these trade-offs before approving.
      </p>
      {data.study === "cross-discipline" && (
        <div>
          <h4>Mass and power impact model</h4>
          {data.impact_assumptions ? (
            <>
              <p>
                Incremental estimates relative to source inputs; no savings
                credit for reductions. Eclipse assumes full coincidence of added
                active loads. These estimates do not qualify hardware.
              </p>
              <dl>
                {Object.entries(data.impact_assumptions).map(([key, value]) => (
                  <div key={key}>
                    <dt>
                      {
                        (
                          {
                            storage_kg_per_gbit: "Storage kg/Gbit",
                            storage_w_per_gbit: "Storage W/Gbit",
                            observation_w: "Observation active W",
                            processing_w_per_ratio:
                              "Processing W per ratio increment",
                            basis: "Basis",
                          } as Record<string, string>
                        )[key]
                      }
                    </dt>
                    <dd>{String(value)}</dd>
                  </div>
                ))}
              </dl>
            </>
          ) : (
            <p role="alert">
              Missing impact assumptions. Mass and power remain unverified;
              start a new study with explicit coefficients and their basis.
            </p>
          )}
        </div>
      )}
      {data.selected_alternative && (
        <p>
          <strong>
            Systems recommends Bus option {data.selected_alternative}.
          </strong>{" "}
          Use the proposal controls to approve, challenge or reject.
        </p>
      )}
      {["payload", "bus"].map(
        (author) =>
          data[author] && (
            <div key={author}>
              <h4>
                {author === "payload"
                  ? "Payload options"
                  : "Bus & Ground options"}
              </h4>
              <div style={{ overflowX: "auto" }}>
                <table>
                  <thead>
                    <tr>
                      <th>Option</th>
                      <th>Duty (%)</th>
                      <th>Compression</th>
                      <th>Storage (Gbit)</th>
                      <th>Daily data (Gbit)</th>
                      <th>Storage margin (Gbit)</th>
                      <th>Downlink capacity (Gbit/day)</th>
                      {data.study === "cross-discipline" && (
                        <>
                          <th>Mass margin (kg)</th>
                          <th>Energy margin (Wh/orbit)</th>
                          <th>Battery margin (Wh)</th>
                        </>
                      )}
                      <th>Checks</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data[author].alternatives.map((option: any) => {
                      const row = data[`evaluate_${author}`]?.alternatives.find(
                        (r: any) => r.id === option.id,
                      );
                      return (
                        <tr key={option.id}>
                          <th>
                            {option.id}
                            {author === "bus" &&
                            option.id === data.selected_alternative
                              ? " · recommended"
                              : ""}
                          </th>
                          <td>{(100 * option.duty).toFixed(3)}</td>
                          <td>{option.compression}</td>
                          <td>{option.storage_gbit}</td>
                          <td>{gigabits(row?.data.outputs.daily)}</td>
                          <td>{gigabits(row?.data.outputs.margin)}</td>
                          <td>{gigabits(row?.link.outputs.capacity)}</td>
                          {data.study === "cross-discipline" && (
                            <>
                              <td>{margin(row?.mass?.outputs.margin)}</td>
                              <td>{margin(row?.power?.outputs.margin)}</td>
                              <td>
                                {margin(row?.power?.outputs.battery_margin)}
                              </td>
                            </>
                          )}
                          <td>
                            {!row
                              ? "Not evaluated"
                              : row.eligible
                                ? "Pass declared checks"
                                : "Not eligible"}
                            {row?.blockers?.map((reason: string) => (
                              <div key={reason}>{reason}</div>
                            ))}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              {data[author].alternatives.map((option: any) => (
                <details key={option.id}>
                  <summary>
                    {author === "payload" ? "Payload" : "Bus"} {option.id}:
                    rationale and evidence
                  </summary>
                  <p>{option.rationale}</p>
                  <pre>
                    {JSON.stringify(
                      data[`evaluate_${author}`]?.alternatives.find(
                        (r: any) => r.id === option.id,
                      ) ?? "Not evaluated",
                      null,
                      2,
                    )}
                  </pre>
                </details>
              ))}
            </div>
          ),
      )}
      {!data.payload && (
        <p>Run the tasks to generate and evaluate alternatives.</p>
      )}
    </section>
  );
}
