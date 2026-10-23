import { useEffect, useState } from "react";
import type { Model } from "./types";
import RunBudget from "./RunBudget";
import { request } from "./api";

type Props = {
  model: Model;
  busy: boolean;
  act: (path: string, body?: object) => unknown;
};
const activeStates = [
  "ready",
  "working",
  "awaiting_answers",
  "review_ready",
  "failed",
];
const labels: Record<string, string> = {
  mission: "Mission clarification",
  formalize: "Systems criterion proposal",
  review: "Independent review",
};
export default function RequirementCollaboration({ model, busy, act }: Props) {
  const [selected, setSelected] = useState("");
  const [requirement, setRequirement] = useState("");
  const [study, setStudy] = useState("formalization");
  const [mode, setMode] = useState("simulation");
  const [cost, setCost] = useState("1");
  const [tokens, setTokens] = useState("100000");
  const [seconds, setSeconds] = useState("3600");
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, []);
  const requirements = Object.values(model.entities).filter(
    (e) => e.kind === "Requirement" && ["accepted", "stale"].includes(e.state),
  );
  const runs = Object.values(model.entities)
    .filter(
      (e) =>
        e.kind === "AgentRun" &&
        e.data.workflow === "requirement-collaboration",
    )
    .reverse();
  const run = runs.find((r) => r.id === selected) || runs[0];
  const pending = Object.values(model.proposals).some((p) =>
    ["submitted", "challenged"].includes(p.status),
  );
  const disabled =
    busy || !!model.baseline || !!model.archived || model.paused || pending;
  const active = runs.some((r) => activeStates.includes(r.data.status));
  const d = run?.data;
  const claimed = d?.execution?.status === "running";
  const expiredClaim =
    claimed && Date.parse(d.execution.lease_expires_at) <= now;
  const recoveringCall = d?.status === "working" || d?.status === "failed";
  const proposedCriterion = d?.criteria?.[d?.proposal?.criterion_id]?.criterion;
  const proposalStatus = d?.proposal_id
    ? model.proposals[d.proposal_id]?.status
    : null;
  const prefix = run ? `/requirement-collaboration/${run.id}` : "";
  return (
    <section className="panel" aria-label="Requirement agent collaboration">
      <h2>Requirement clarification with agents</h2>
      <p>
        Mission asks questions → Systems selects a source-backed criterion → an
        independent reviewer checks the proposal → you approve. Agents cannot
        invent thresholds or claim full coverage. Choose a single task or run
        until owner action is needed. Unanswered questions and completed review
        stop progression; submission and approval remain separate actions.
      </p>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          setSelected("");
          act("/requirement-collaboration", {
            requirement_id: requirement || requirements[0]?.id,
            mode,
            study,
            limits: {
              cost_eur: Number(cost),
              tokens: Number(tokens),
              elapsed_seconds: Number(seconds),
            },
          });
        }}
      >
        <fieldset disabled={disabled || active || !requirements.length}>
          <legend>Start requirement assistance</legend>
          <label>
            Requirement assistance type
            <select value={study} onChange={(e) => setStudy(e.target.value)}>
              <option value="formalization">Clarify one criterion</option>
              <option value="decomposition">
                Decompose into child requirements
              </option>
            </select>
          </label>
          {study === "decomposition" && (
            <p>
              Propose two to five children quoted from the parent or owner
              answers. The parent stays unchanged. Missing targets stay
              unresolved; no child or parent is automatically verified.
              Simulation separates an explicit delivery deadline from its
              preceding obligation; other statements need live mode.
            </p>
          )}
          <label>
            Requirement for agents
            <select
              value={requirement || requirements[0]?.id || ""}
              onChange={(e) => setRequirement(e.target.value)}
            >
              {requirements.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.title}
                </option>
              ))}
            </select>
          </label>
          <label>
            Requirement execution mode
            <select value={mode} onChange={(e) => setMode(e.target.value)}>
              <option value="simulation">Simulation — no model calls</option>
              <option value="live">Live — configured AI provider</option>
            </select>
          </label>
          <p>
            {mode === "simulation"
              ? "Simulation demonstrates the exchange and selects the first sourced criterion. It records free-text answers without interpreting them."
              : "Live mode makes separate model calls using the server’s configured provider and credentials. This is a separate review call, not a different model guarantee."}
          </p>
          <label>
            Requirement run cost limit (EUR)
            <input
              type="number"
              min="0"
              max="10000"
              step="any"
              required
              value={cost}
              onChange={(e) => setCost(e.target.value)}
            />
          </label>
          <label>
            Requirement run token limit
            <input
              type="number"
              min="0"
              max="10000000"
              required
              value={tokens}
              onChange={(e) => setTokens(e.target.value)}
            />
          </label>
          <label>
            Requirement execution window (seconds)
            <input
              type="number"
              min="1"
              max="86400"
              required
              value={seconds}
              onChange={(e) => setSeconds(e.target.value)}
            />
          </label>
          <button type="submit">Start requirement collaboration</button>
        </fieldset>
      </form>
      {run && d && (
        <>
          <label>
            Requirement collaboration history
            <select
              value={run.id}
              onChange={(e) => setSelected(e.target.value)}
            >
              {runs.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.data.source_requirement.title} — {r.data.mode} —{" "}
                  {r.data.status}
                </option>
              ))}
            </select>
          </label>
          <h3>
            {labels[d.stage]} · {d.status.replaceAll("_", " ")}
          </h3>
          <p>
            Source revision {d.source_revision} · {d.mode} · Clarification
            rounds {d.round}/3 · Task attempts {d.attempts}/10
          </p>
          {d.error && d.status === "failed" && <p role="alert">{d.error}</p>}
          <ol>
            {Object.entries(labels).map(([stage, label]) => (
              <li key={stage}>
                {label}
                {stage === d.stage ? ` — ${d.status.replaceAll("_", " ")}` : ""}
              </li>
            ))}
          </ol>
          {d.status === "ready" && (
            <div>
              <button
                disabled={disabled || claimed}
                onClick={() => act(prefix + "/run")}
              >
                Run until owner action
              </button>
              <button
                disabled={disabled || claimed}
                onClick={() => act(prefix + "/step")}
              >
                Run {labels[d.stage]}
              </button>
            </div>
          )}
          {claimed && (
            <p className="notice">
              {expiredClaim
                ? "Execution checkpoint expired. Prepare recovery before continuing."
                : "Automatic progression is running. Pause stops further work; resuming requires an explicit run action."}
            </p>
          )}
          {!claimed && d.execution?.reason && (
            <p className="notice">{d.execution.reason}</p>
          )}
          {d.status === "working" && (
            <p>
              Task claimed. Its result and usage will appear here. After an
              interruption, wait for the two-minute checkpoint lease before
              preparing a retry.
            </p>
          )}
          {((!claimed &&
            (d.status === "failed" ||
              (d.status === "working" && Date.parse(d.task_lease) <= now))) ||
            expiredClaim) && (
            <Retry
              key={`${run.id}:${d.execution?.id}:${d.attempt}`}
              live={d.mode === "live" && recoveringCall}
              disabled={disabled || (recoveringCall && d.attempts >= 10)}
              action={(body) => act(prefix + "/retry", body)}
            />
          )}
          {d.status === "awaiting_answers" && (
            <Answers
              key={`${run.id}:${d.round}`}
              questions={d.pending_questions}
              disabled={disabled || claimed || d.round >= 3}
              action={(body) => act(prefix + "/answers", body)}
            />
          )}
          {d.round >= 3 && d.status === "awaiting_answers" && (
            <p>
              Clarification limit reached. Cancel this run; use the recorded
              findings to clarify the requirement before starting again.
            </p>
          )}
          {d.proposal && (
            <div className="notice">
              <h3>
                {d.study === "decomposition"
                  ? "Proposed child requirements"
                  : "Proposed partial criterion"}
              </h3>
              <p>{d.proposal.basis}</p>
              {d.study === "decomposition" ? (
                <ol>
                  {d.proposal.children.map((child: any, i: number) => {
                    const criterion = d.criteria[child.criterion_id]?.criterion;
                    return (
                      <li key={i}>
                        <strong>{child.source_quote}</strong>
                        <p>
                          Quoted from{" "}
                          {child.source_ref === "parent"
                            ? "parent requirement"
                            : "owner " + child.source_ref}
                          . {child.rationale}
                        </p>
                        <p>
                          {criterion
                            ? `${criterion.metric} ${criterion.operator} ${criterion.threshold.value} ${criterion.threshold.unit}`
                            : "No supported criterion — unresolved"}{" "}
                          · Partial coverage
                        </p>
                        <ul>
                          {child.unresolved.map((q: string, j: number) => (
                            <li key={j}>{q}</li>
                          ))}
                        </ul>
                      </li>
                    );
                  })}
                </ol>
              ) : (
                <>
                  <p>
                    {proposedCriterion
                      ? `${proposedCriterion.metric.replaceAll(".", " / ").replaceAll("_", " ")} ${proposedCriterion.operator === "<=" ? "≤" : "≥"} ${proposedCriterion.threshold.value} ${proposedCriterion.threshold.unit}`
                      : "No supported criterion selected"}
                  </p>
                  <p>
                    Source:{" "}
                    {d.criteria[d.proposal.criterion_id]?.source || "None"}
                  </p>
                </>
              )}
              <ul>
                {d.proposal.limitations.map((l: string, i: number) => (
                  <li key={i}>{l}</li>
                ))}
              </ul>
            </div>
          )}
          {d.review && (
            <div className="notice">
              <h3>Independent reviewer: {d.review.recommendation}</h3>
              <p>{d.review.rationale}</p>
              <ul>
                {d.review.findings.map((f: string, i: number) => (
                  <li key={i}>{f}</li>
                ))}
              </ul>
            </div>
          )}
          {d.status === "review_ready" && (
            <button
              disabled={disabled || claimed}
              onClick={() => act(prefix + "/submit")}
            >
              {d.study === "decomposition"
                ? "Submit child requirements for human approval"
                : "Submit partial criterion for human approval"}
            </button>
          )}
          {d.status === "submitted" && (
            <p>
              {proposalStatus === "accepted"
                ? d.study === "decomposition"
                  ? "Child requirements accepted. The parent is unchanged; child results do not roll up into parent verification."
                  : "Proposal accepted by the owner. The recorded criterion has partial coverage; complete requirement verification remains unresolved."
                : proposalStatus === "rejected"
                  ? "Proposal rejected by the owner. The accepted requirement was not changed by this proposal."
                  : "Proposal submitted. Open Conflicts & review to inspect and approve, reject or resolve a challenge. The accepted requirement changes only after approval."}
            </p>
          )}
          {activeStates.includes(d.status) && (
            <button
              disabled={busy || !!model.archived || !!model.baseline}
              onClick={() => act(prefix + "/cancel")}
            >
              Cancel requirement collaboration
            </button>
          )}
          <RunBudget budget={d.budget} />
          <h3>Recorded agent exchanges</h3>
          {d.events.map((e: any) => (
            <details key={e.id}>
              <summary>
                {e.sequence}. {labels[e.sender] || e.sender} →{" "}
                {labels[e.recipient] || e.recipient} · {e.type}
              </summary>
              <p>{e.summary}</p>
              <p>
                {e.timestamp} · {e.mode}
              </p>
              {e.evidence && <pre>{JSON.stringify(e.evidence, null, 2)}</pre>}
            </details>
          ))}
        </>
      )}
    </section>
  );
}
function Retry({
  live,
  disabled,
  action,
}: {
  live: boolean;
  disabled: boolean;
  action: (body: object) => unknown;
}) {
  const [ack, setAck] = useState(false);
  return (
    <div>
      {live && (
        <label>
          <input
            type="checkbox"
            checked={ack}
            onChange={(e) => setAck(e.target.checked)}
          />
          I understand the previous call may already have incurred a charge and
          retrying may incur another.
        </label>
      )}
      <button
        disabled={disabled || (live && !ack)}
        onClick={() => action({ acknowledge_unknown: ack })}
      >
        Prepare explicit retry
      </button>
    </div>
  );
}
function Answers({
  questions,
  disabled,
  action,
}: {
  questions: string[];
  disabled: boolean;
  action: (body: object) => unknown;
}) {
  const [answers, setAnswers] = useState<string[]>(questions.map(() => ""));
  const [metrics, setMetrics] = useState<Record<string, any>>({});
  const [metric, setMetric] = useState("");
  const [operator, setOperator] = useState("<=");
  const [value, setValue] = useState("");
  const [unit, setUnit] = useState("");
  useEffect(() => {
    let active = true;
    request("/requirement-metrics")
      .then((m) => {
        if (active) setMetrics(m);
      })
      .catch(() => {});
    return () => {
      active = false;
    };
  }, []);
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        action({
          answers,
          criterion: metric
            ? { metric, operator, threshold: { value: Number(value), unit } }
            : null,
        });
      }}
    >
      <fieldset disabled={disabled}>
        <legend>Owner clarification answers</legend>
        {questions.map((q, i) => (
          <label key={i}>
            {q}
            <textarea
              required
              minLength={3}
              maxLength={2000}
              value={answers[i]}
              onChange={(e) =>
                setAnswers(
                  answers.map((a, j) => (i === j ? e.target.value : a)),
                )
              }
            />
          </label>
        ))}
        <p>
          Optionally supply an explicit criterion. This is your proposed
          threshold; agents may select it and must review its applicability.
          Free-text numbers are never automatically converted into thresholds.
        </p>
        <label>
          Owner-supplied metric
          <select
            value={metric}
            onChange={(e) => {
              setMetric(e.target.value);
              setUnit(metrics[e.target.value]?.unit || "");
              setValue("");
              setOperator("<=");
            }}
          >
            <option value="">No additional criterion</option>
            {Object.entries(metrics).map(([key, m]) => (
              <option key={key} value={key}>
                {m.label}
              </option>
            ))}
          </select>
        </label>
        {metric && (
          <>
            <label>
              Owner comparison
              <select
                value={operator}
                onChange={(e) => setOperator(e.target.value)}
              >
                <option value="<=">At most</option>
                {metric !== "delivery.maximum_latency" && (
                  <option value=">=">At least</option>
                )}
              </select>
            </label>
            <label>
              Owner threshold
              <input
                type="number"
                min="0"
                step="any"
                required
                value={value}
                onChange={(e) => setValue(e.target.value)}
              />
            </label>
            <label>
              Owner threshold unit
              <input
                required
                value={unit}
                onChange={(e) => setUnit(e.target.value)}
              />
            </label>
          </>
        )}
        <button type="submit">Record answers and continue</button>
      </fieldset>
    </form>
  );
}
