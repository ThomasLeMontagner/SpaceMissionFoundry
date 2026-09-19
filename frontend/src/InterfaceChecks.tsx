import type { Model } from "./types";

export default function InterfaceChecks({
  model,
  busy,
  onInspect,
}: {
  model: Model;
  busy: boolean;
  onInspect: (id: string) => void;
}) {
  const interfaces = Object.values(model.entities).filter(
    (e) => e.kind === "Interface",
  );
  return (
    <section className="panel" aria-label="Interface consistency checks">
      <h2>Data interface consistency</h2>
      <p>
        Checks compare declared sender/receiver protocols and peak rates. They
        do not establish electrical, timing, packet-format, power or mechanical
        compatibility. Both reference candidates share these interfaces.
      </p>
      {model.baseline && (
        <p>
          Reopen the baseline before editing a data contract. Existing baseline
          evidence remains unchanged.
        </p>
      )}
      {!interfaces.length && (
        <p>Approve architecture interfaces before defining data contracts.</p>
      )}
      {interfaces.map((e) => {
        const check = model.entities[`interface-check-${e.id}`];
        const stale = check?.state === "stale" || e.state === "stale";
        return (
          <article key={e.id}>
            <h3>
              {e.title} · {stale ? "stale" : check?.data.status || "unverified"}
            </h3>
            <button
              className="secondary"
              disabled={busy}
              onClick={() => onInspect(e.id)}
            >
              Inspect or edit {e.id} contract
            </button>
            {check && (
              <button
                className="secondary"
                disabled={busy}
                onClick={() => onInspect(check.id)}
              >
                Inspect {e.id} check evidence
              </button>
            )}
            {stale ? (
              <p className="notice">
                Stale — review changes and recalculate before using these
                checks.
              </p>
            ) : !check ? (
              <p>
                Checks have not been recorded for this revision. Define a data
                contract and recalculate; descriptive text alone cannot verify
                compatibility.
              </p>
            ) : (
              <>
                <p>
                  Tool {check.data.tool_version} · evaluated source revision{" "}
                  {check.data.source_revision}. Failed checks block concept
                  selection and baseline approval. Unverified checks remain
                  outstanding.
                </p>
                <ul>
                  {check.data.checks.map((c: any) => (
                    <li key={c.check}>
                      <strong>
                        {c.check}: {c.status}
                      </strong>{" "}
                      — {c.reason}
                      {c.margin_bits_per_second != null
                        ? ` Margin: ${(c.margin_bits_per_second / 1e6).toFixed(2)} Mbit/s.`
                        : ""}
                    </li>
                  ))}
                </ul>
              </>
            )}
          </article>
        );
      })}
    </section>
  );
}
