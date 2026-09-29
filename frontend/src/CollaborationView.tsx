import { useState } from "react";
import type { Model } from "./types";
import CollaborationGraph, { selectedEventIds } from "./CollaborationGraph";

const stages = [
  "payload",
  "evaluate_payload",
  "bus",
  "evaluate_bus",
  "systems",
];
const labels: Record<string, string> = {
  payload: "Payload proposal",
  evaluate_payload: "Evaluate payload proposal",
  bus: "Bus & Ground review",
  evaluate_bus: "Evaluate revised proposal",
  systems: "Systems approval request",
};
export default function CollaborationView({
  model,
  busy,
  act,
  onInspect,
}: {
  model: Model;
  busy: boolean;
  act: (path: string, body?: object) => unknown;
  onInspect: (id: string) => void;
}) {
  const [candidate, setCandidate] = useState("selective");
  const [goal, setGoal] = useState(
    "Increase observation time while respecting storage and downlink capacity.",
  );
  const [mode, setMode] = useState("simulation");
  const [selected, setSelected] = useState("");
  const [agent, setAgent] = useState("");
  const [kind, setKind] = useState("");
  const [task, setTask] = useState("");
  const [query, setQuery] = useState("");
  const [graph, setGraph] = useState<{
    run: string;
    label: string;
    ids: string[];
  } | null>(null);
  const runs = Object.values(model.entities)
    .filter(
      (e) => e.kind === "AgentRun" && e.data.workflow === "duty-collaboration",
    )
    .reverse();
  const run = runs.find((e) => e.id === selected) || runs[0];
  const data = run?.data;
  const pending = Object.values(model.proposals).some((p) =>
    ["submitted", "challenged"].includes(p.status),
  );
  const active = runs.some((r) =>
    ["ready", "working", "failed"].includes(r.data.status),
  );
  const editable = !model.baseline && !model.archived;
  const events: any[] = data?.events || [];
  const graphSelection = graph?.run === run?.id ? graph : null;
  const graphIds = graphSelection
    ? selectedEventIds(events, graphSelection.label)
    : null;
  const visible = events.filter(
    (e) =>
      (!graphIds || graphIds.includes(e.id)) &&
      (!agent || e.sender === agent || e.recipient === agent) &&
      (!kind || e.type === kind) &&
      (!task || e.task === task) &&
      (!query ||
        `${e.summary} ${e.objects.join(" ")}`
          .toLowerCase()
          .includes(query.toLowerCase())),
  );
  const proposal = data?.proposal_id ? model.proposals[data.proposal_id] : null;
  return (
    <section className="panel" aria-label="Agent collaboration">
      <h2>Agent collaboration</h2>
      <p>
        A bounded observation-duty negotiation: Payload → tools → Bus &amp;
        Ground → tools → Systems → you. Other mission design tasks and
        independent LLM review are not implemented in this slice.
      </p>
      <p>
        Each click executes one task. Events persist and update during
        execution. Pause prevents subsequent tasks; an in-flight call may
        finish. Cancel discards its response. Interrupted work can be cancelled
        and restarted.
      </p>
      {model.baseline && (
        <p className="notice">
          Reopen the baseline before starting collaboration. Recorded runs below
          remain readable.
        </p>
      )}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          setSelected("");
          act("/collaboration", { candidate, goal, mode });
        }}
      >
        <div className="row">
          <label>
            Candidate
            <select
              value={candidate}
              onChange={(e) => setCandidate(e.target.value)}
            >
              <option value="selective">B · Event-selective</option>
              <option value="wide">A · Wide-area</option>
            </select>
          </label>
          <label>
            Execution mode
            <select value={mode} onChange={(e) => setMode(e.target.value)}>
              <option value="simulation">Simulation · no LLM calls</option>
              <option value="live">
                Live provider · may incur API charges
              </option>
            </select>
          </label>
        </div>
        <label>
          Design goal
          <textarea
            maxLength={1000}
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
          />
        </label>
        <button
          disabled={
            busy ||
            active ||
            pending ||
            !editable ||
            model.paused ||
            !["Trade study", "Ready for baseline"].includes(model.phase) ||
            goal.trim().length < 3
          }
        >
          Start collaboration
        </button>
        <p className="muted">
          Requires an analyzed mission with no pending proposals. Simulation
          demonstrates the workflow; it does not interpret your goal with an
          LLM. Live execution requires backend provider configuration.
        </p>
      </form>
      {!!runs.length && (
        <>
          <label>
            Recorded collaboration
            <select
              value={run?.id || ""}
              onChange={(e) => {
                setSelected(e.target.value);
                setAgent("");
                setKind("");
                setTask("");
                setQuery("");
              }}
            >
              {runs.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.title} · source r{r.data.source_revision} · {r.data.mode} ·{" "}
                  {r.id.slice(0, 8)}
                </option>
              ))}
            </select>
          </label>
          <h3>
            {data.mode === "simulation"
              ? "SIMULATION · no model calls"
              : `LIVE PROVIDER · ${data.provider_model}`}{" "}
            · {proposal?.status || data.status}
          </h3>
          <p>
            Source revision {data.source_revision} · {data.completed.length} of
            5 execution tasks completed. This measures workflow progress, not
            mission feasibility. Recorded results describe their source inputs;
            subsequent design changes require a new run.
          </p>
          {model.paused && (
            <p className="notice">
              Paused — resume the mission to execute another task.
            </p>
          )}
          {data.status === "working" && (
            <p role="status">
              Working on {labels[data.stage]}. A completed response will be
              recorded; after an interruption, cancel and start a new run.
            </p>
          )}
          {["failed", "stale", "blocked"].includes(data.status) && (
            <p className="notice">{events.at(-1)?.summary}</p>
          )}
          <div className="collaboration-tasks">
            {stages.map((s, index) => (
              <article className="panel" key={s}>
                <h4>{labels[s]}</h4>
                <p>
                  {data.completed.includes(s)
                    ? "Completed"
                    : s === data.stage
                      ? data.status
                      : "Waiting"}
                </p>
                {!data.completed.includes(s) && s !== data.stage && (
                  <p className="muted">
                    Depends on {labels[stages[index - 1]] || "owner request"}.
                  </p>
                )}
              </article>
            ))}
          </div>
          <div className="actions">
            <button
              disabled={
                busy ||
                !editable ||
                model.paused ||
                pending ||
                !["ready", "failed"].includes(data.status) ||
                data.attempts >= 10
              }
              onClick={() => act(`/collaboration/${run!.id}/step`)}
            >
              {data.status === "failed" ? "Retry task" : "Run next task"}
            </button>
            <button
              className="secondary"
              disabled={
                busy ||
                !editable ||
                !["ready", "working", "failed"].includes(data.status)
              }
              onClick={() => act(`/collaboration/${run!.id}/cancel`)}
            >
              Cancel collaboration
            </button>
            <button className="secondary" onClick={() => onInspect(run!.id)}>
              Inspect recorded run
            </button>
          </div>
          {proposal && (
            <p className="notice">
              Design proposal: {proposal.status}. Use the proposal approval
              controls to inspect, approve, challenge or reject it. Only
              approval changes accepted inputs; calculations run again
              afterward.
            </p>
          )}
          <h3>Collaboration timeline</h3>
          <CollaborationGraph
            events={events}
            stage={data.stage}
            status={data.status}
            paused={model.paused}
            mode={data.mode}
            selection={graphSelection?.label || ""}
            onSelect={(label, ids) => {
              setGraph({ run: run!.id, label, ids });
              setAgent("");
              setKind("");
              setTask("");
              setQuery("");
            }}
          />
          {graphSelection && (
            <p role="status">
              Showing exchanges: {graphSelection.label}.{" "}
              <button className="secondary" onClick={() => setGraph(null)}>
                Clear graph selection
              </button>
            </p>
          )}
          <div className="row">
            <label>
              Agent filter
              <select value={agent} onChange={(e) => setAgent(e.target.value)}>
                <option value="">All agents</option>
                {[
                  ...new Set(events.flatMap((e) => [e.sender, e.recipient])),
                ].map((a) => (
                  <option key={a}>{a}</option>
                ))}
              </select>
            </label>
            <label>
              Event filter
              <select value={kind} onChange={(e) => setKind(e.target.value)}>
                <option value="">All events</option>
                {[...new Set(events.map((e) => e.type))].map((t) => (
                  <option key={t}>{t}</option>
                ))}
              </select>
            </label>
            <label>
              Task filter
              <select value={task} onChange={(e) => setTask(e.target.value)}>
                <option value="">All tasks</option>
                {stages.map((s) => (
                  <option key={s} value={s}>
                    {labels[s]}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <label>
            Search timeline or object ID
            <input value={query} onChange={(e) => setQuery(e.target.value)} />
          </label>
          {!visible.length && <p>No matching events.</p>}
          <ol>
            {visible.map((e) => (
              <li key={e.id} className="collaboration-event">
                <strong>
                  {e.sender} → {e.recipient} · {e.type}
                </strong>
                <p>{e.summary}</p>
                <small>
                  {e.timestamp} · {labels[e.task]} · source r{e.source_revision}
                  {e.elapsed_seconds != null
                    ? ` · ${e.elapsed_seconds.toFixed(2)}s`
                    : ""}
                </small>
                <p>
                  <button
                    className="secondary"
                    disabled={busy}
                    onClick={() => onInspect(data.input_id)}
                  >
                    Inspect affected input
                  </button>
                </p>
                {e.evidence && (
                  <details>
                    <summary>Recorded proposal or calculation evidence</summary>
                    <pre>{JSON.stringify(e.evidence, null, 2)}</pre>
                  </details>
                )}
              </li>
            ))}
          </ol>
        </>
      )}
      {!runs.length && (
        <p>
          No recorded collaboration yet. Start a simulation to explore the
          workflow without an API key.
        </p>
      )}
    </section>
  );
}
