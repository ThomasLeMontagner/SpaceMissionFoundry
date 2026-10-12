import { useEffect, useState } from "react";

export default function RunBudget({ budget }: { budget: any }) {
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, []);
  if (!budget)
    return (
      <p className="notice">
        Legacy run: complete usage accounting is unavailable. Start a new
        collaboration to use budgets.
      </p>
    );
  const entries: any[] = budget.attempts;
  const tokens = entries.reduce(
    (sum, entry) => sum + entry.accounted_tokens,
    0,
  );
  const unknown = entries.filter(
    (entry) => entry.live && entry.reported_tokens === null,
  ).length;
  const remaining = Math.max(
    0,
    Math.ceil((Date.parse(budget.deadline) - now) / 1000),
  );
  const cost = (value: number) =>
    ((value * budget.price_per_million) / 1e6).toFixed(6);
  const agents = [...new Set(entries.map((entry) => entry.agent))];
  const nearLimit =
    (budget.limits.tokens > 0 && tokens >= 0.8 * budget.limits.tokens) ||
    (budget.limits.cost_eur > 0 &&
      (tokens * budget.price_per_million) / 1e6 >=
        0.8 * budget.limits.cost_eur);
  return (
    <section className="panel" aria-label="Run budget and usage">
      <h3>Run budget and usage</h3>
      <p>
        Accounted tokens: {tokens.toLocaleString()} /{" "}
        {budget.limits.tokens.toLocaleString()} · Estimated/reserved cost: €
        {cost(tokens)} / €{budget.limits.cost_eur}
      </p>
      <p>
        Execution window: {budget.limits.elapsed_seconds} seconds, including
        pauses · {remaining} seconds remaining.
      </p>
      {remaining === 0 && (
        <p className="notice">
          Execution window expired. Further tasks require a new collaboration.
        </p>
      )}
      <p className="muted">
        Limits cover every revision round and retry. Each live call reserves
        29,120 tokens at the recorded maximum token price. Valid reported usage
        replaces its reservation. Missing results retain the reservation; billed
        charges remain unknown. Simulation uses no model tokens or cost.
      </p>
      {nearLimit && (
        <p className="notice">
          At least 80% of the token or estimated cost allowance is accounted
          for. The next live call may not fit its reservation.
        </p>
      )}
      {!!unknown && (
        <p className="notice">
          {unknown} live attempt(s) have unknown usage. Their full reservations
          remain counted.
        </p>
      )}
      {!!agents.length && (
        <table>
          <thead>
            <tr>
              <th>Agent / task</th>
              <th>Attempts</th>
              <th>Reported tokens</th>
              <th>Accounted tokens</th>
              <th>Estimated/reserved EUR</th>
              <th>Recorded task seconds</th>
            </tr>
          </thead>
          <tbody>
            {agents.map((agent) => {
              const rows = entries.filter((entry) => entry.agent === agent);
              const accounted = rows.reduce(
                (sum, entry) => sum + entry.accounted_tokens,
                0,
              );
              const reported = rows.reduce(
                (sum, entry) => sum + (entry.reported_tokens ?? 0),
                0,
              );
              const seconds = rows.reduce(
                (sum, entry) => sum + (entry.elapsed_seconds ?? 0),
                0,
              );
              return (
                <tr key={agent}>
                  <th>{agent}</th>
                  <td>{rows.length}</td>
                  <td>
                    {reported}
                    {rows.some((e) => e.reported_tokens === null)
                      ? " + unknown"
                      : ""}
                  </td>
                  <td>{accounted}</td>
                  <td>{cost(accounted)}</td>
                  <td>
                    {seconds.toFixed(2)}
                    {rows.some((e) => e.elapsed_seconds === null)
                      ? " + unknown"
                      : ""}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </section>
  );
}
