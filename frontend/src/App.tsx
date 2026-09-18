import { useEffect, useState, useRef } from "react";
import { request, download, setToken, subscribe } from "./api";
import DesignEditor from "./DesignEditor";
import BaselineComparison from "./BaselineComparison";
import CoverageView from "./CoverageView";
import DeliveryView from "./DeliveryView";
import type { Entity, Model, Proposal } from "./types";

type MissionSummary = {
  id: string;
  name: string;
  revision: number;
  archived?: boolean;
};

const tabs: Record<string, string[]> = {
  Overview: [],
  "Brief & assumptions": ["Mission", "Assumption"],
  "Design inputs": ["Parameter"],
  Requirements: ["Objective", "Requirement"],
  Architectures: ["ArchitectureAlternative", "Function", "Component"],
  Interfaces: ["Interface"],
  Budgets: ["Budget", "BudgetEntry", "AnalysisRun"],
  "Coverage & access": [],
  "Data delivery": [],
  Trades: ["TradeStudy"],
  "Claims & evidence": ["Claim", "Evidence"],
  "Conflicts & review": ["ReviewFinding", "Risk", "VerificationItem"],
  "Agent activity": ["AgentRun", "AgentDefinition"],
  Decisions: ["Decision"],
  "Baselines & replay": ["Baseline"],
};
export function Badge({ value }: { value: string }) {
  return (
    <span
      className={
        "badge " +
        (value === "Deterministic calculation"
          ? "calc"
          : value === "Human decision"
            ? "human"
            : value === "Unknown"
              ? "unknown"
              : "")
      }
    >
      {value}
    </span>
  );
}
function Value({ value }: { value: any }) {
  if (value === null) return <>Unknown</>;
  if (typeof value === "object" && "value" in value && "unit" in value)
    return (
      <strong>
        {Number(
          value.unit === "bit" && Math.abs(value.value) >= 1e9
            ? value.value / 1e9
            : value.value,
        ).toLocaleString(undefined, { maximumFractionDigits: 3 })}{" "}
        <small>
          {value.unit === "bit" && Math.abs(value.value) >= 1e9
            ? "Gbit"
            : value.unit || "dimensionless"}
        </small>
      </strong>
    );
  if (typeof value === "boolean")
    return (
      <span className={value ? "pass" : "fail"}>
        {value ? "Compliant" : "Not compliant"}
      </span>
    );
  if (typeof value === "object")
    return <pre>{JSON.stringify(value, null, 2)}</pre>;
  return <>{String(value)}</>;
}
export default function App() {
  const [model, setModel] = useState<Model | null>(null),
    [list, setList] = useState<MissionSummary[]>([]),
    [archivedList, setArchivedList] = useState<MissionSummary[]>([]),
    [showArchived, setShowArchived] = useState(false),
    [tab, setTab] = useState("Overview"),
    [name, setName] = useState(""),
    [brief, setBrief] = useState(""),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [success, setSuccess] = useState(""),
    [query, setQuery] = useState(""),
    [detail, setDetail] = useState<Entity | null>(null),
    [reason, setReason] = useState(
      "Reviewed against mission intent and declared concept assumptions.",
    ),
    [weights, setWeights] = useState({
      science: 0.35,
      capacity: 0.45,
      simplicity: 0.2,
    }),
    [confirm, setConfirm] = useState(false),
    [impactConfirmed, setImpactConfirmed] = useState(false),
    [baselineName, setBaselineName] = useState("Mission Concept Baseline"),
    [baselineList, setBaselineList] = useState<
      { id: string; name: string; revision: number }[]
    >([]),
    [history, setHistory] = useState<any[]>([]),
    [past, setPast] = useState<Model | null>(null),
    [token, setTokenInput] = useState("");
  useEffect(() => {
    setConfirm(false);
    setImpactConfirmed(false);
  }, [model?.revision]);
  useEffect(() => {
    setBaselineList([]);
    setHistory([]);
    setPast(null);
    setDetail(null);
    setQuery("");
  }, [model?.id]);
  function receiveModel(next: Model) {
    setModel((current) =>
      current?.id === next.id && current.revision > next.revision
        ? current
        : next.archived
          ? null
          : next,
    );
  }
  const detailRef = useRef<HTMLElement>(null);
  useEffect(() => {
    if (!detail) return;
    const previous = document.activeElement as HTMLElement | null;
    return () => previous?.focus();
  }, [!!detail]);
  const loadList = async () => {
    const [active, archived] = await Promise.all([
      request("/missions"),
      request("/missions?archived=true"),
    ]);
    setList(active);
    setArchivedList(archived);
  };
  useEffect(() => {
    Promise.all([request("/scenario"), loadList()])
      .then(([s]) => {
        setName(s.name);
        setBrief(s.brief);
      })
      .catch((e) => setError(e.message));
  }, []);
  useEffect(() => {
    if (!model?.id) return;
    let active = true;
    const stop = subscribe(model.id, () => {
      request("/missions/" + model.id)
        .then((next: Model) => {
          if (active)
            setModel((current) =>
              current?.id === next.id && current.revision <= next.revision
                ? next.archived
                  ? null
                  : next
                : current,
            );
        })
        .catch((e) => {
          if (active) setError(e.message);
        });
    });
    return () => {
      active = false;
      stop();
    };
  }, [model?.id]);
  async function run(
    fn: () => Promise<any>,
    message = "Saved to model history",
  ) {
    setBusy(true);
    setError("");
    setSuccess("");
    try {
      const result = await fn();
      if (result?.entities) receiveModel(result);
      setSuccess(message);
      await loadList();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  const base = model ? "/missions/" + model.id : "";
  function archiveMission(mission: MissionSummary, archived: boolean) {
    if (
      archived &&
      !window.confirm(
        `Archive “${mission.name}”? Its history and baselines will be kept, and you can restore it later.`,
      )
    )
      return;
    void run(
      async () => {
        await request(`/missions/${mission.id}/archive`, {
          revision: mission.revision,
          archived,
        });
        if (model?.id === mission.id) {
          setModel(null);
          setDetail(null);
        }
      },
      archived
        ? "Mission archived. Find it under Show archived missions to restore it."
        : "Mission restored to the active list.",
    );
  }
  const act = (path: string, body: object = {}) =>
    run(async () => {
      const updated: Model = await request(base + path, {
        revision: model!.revision,
        ...body,
      });
      receiveModel(updated);
      const approvals =
        path.endsWith("/decision") ||
        path === "/review-impact" ||
        path === "/pause";
      if (
        approvals &&
        updated.phase === "Recalculation required" &&
        !updated.paused &&
        !Object.values(updated.proposals).some((p) =>
          ["submitted", "challenged"].includes(p.status),
        )
      ) {
        try {
          return await request(base + "/advance", {
            revision: updated.revision,
          });
        } catch (error) {
          throw Error(
            "The change is saved, but recalculation needs attention: " +
              (error as Error).message,
          );
        }
      }
      return updated;
    });
  const objects = model ? Object.values(model.entities) : [];
  const pending = model
    ? Object.values(model.proposals).filter((p) =>
        ["submitted", "challenged"].includes(p.status),
      )
    : [];
  const open = objects.filter(
    (e) => e.kind === "ReviewFinding" && e.state === "open",
  );
  const budgets = objects.filter(
    (e) =>
      e.kind === "Budget" &&
      e.data.candidate === (model?.selected || "selective"),
  );
  function show(e: Entity) {
    setDetail(e);
  }
  const affectedDesign = objects.filter(
    (e) =>
      e.state === "stale" &&
      [
        "Objective",
        "Requirement",
        "Assumption",
        "Parameter",
        "ArchitectureAlternative",
        "Function",
        "Component",
        "Interface",
        "Risk",
      ].includes(e.kind),
  );
  function proposal(p: Proposal) {
    return (
      <article className="proposal" key={p.id}>
        <div className="row">
          <span className="eyebrow">PENDING HUMAN DECISION</span>
          <Badge value={p.status} />
        </div>
        <h3>
          {p.proposal_type} <small> / {p.agent}</small>
        </h3>
        <p>{p.rationale}</p>
        {p.operations.map((o) => (
          <div className="proposed-object" key={o.entity.id}>
            <button className="text-button" onClick={() => show(o.entity)}>
              {o.entity.title}
            </button>
            <Badge value={o.entity.classification} />
            {o.action === "replace" && (
              <details className="change-comparison">
                <summary>Compare proposed change</summary>
                <div className="comparison">
                  <div>
                    <b>Current accepted content</b>
                    <pre>
                      {JSON.stringify(
                        {
                          title: model?.entities[o.entity.id]?.title,
                          data: model?.entities[o.entity.id]?.data,
                        },
                        null,
                        2,
                      )}
                    </pre>
                  </div>
                  <div>
                    <b>Proposed content</b>
                    <pre>
                      {JSON.stringify(
                        { title: o.entity.title, data: o.entity.data },
                        null,
                        2,
                      )}
                    </pre>
                  </div>
                </div>
              </details>
            )}
          </div>
        ))}
        <p className="muted">
          {p.expected_consequences} · Confidence {p.confidence}
        </p>
        <div className="actions">
          <button
            disabled={busy}
            onClick={() =>
              act(`/proposals/${p.id}/decision`, { action: "accept", reason })
            }
          >
            Approve {p.proposal_type}
          </button>
          <button
            className="secondary"
            disabled={busy}
            onClick={() =>
              act(`/proposals/${p.id}/decision`, { action: "reject", reason })
            }
          >
            Reject
          </button>
          <button
            className="secondary"
            disabled={busy || p.status === "challenged"}
            onClick={() =>
              act(`/proposals/${p.id}/decision`, {
                action: "challenge",
                reason,
              })
            }
          >
            Challenge
          </button>
        </div>
      </article>
    );
  }
  return (
    <div className="shell">
      <aside>
        <div className="brand">
          <span className="brandmark">✧</span>
          <div>
            MISSION
            <br />
            <b>FOUNDRY</b>
          </div>
        </div>
        <div className="workspace-label">ENGINEERING WORKSPACE</div>
        {Object.keys(tabs).map((t, i) => (
          <button
            key={t}
            aria-label={t}
            className={"nav " + (tab === t ? "active" : "")}
            onClick={() => {
              setTab(t);
              setPast(null);
            }}
          >
            <span>{String(i + 1).padStart(2, "0")}</span>
            {t}
            {t === "Conflicts & review" && open.length > 0 && (
              <b className="count">{open.length}</b>
            )}
          </button>
        ))}
        <div className="aside-foot">
          <span className="dot" /> Concept design environment
          <br />
          <small>Model first. Evidence always.</small>
        </div>
      </aside>
      <main>
        <header>
          <div>
            <span className="eyebrow">
              MISSION CONTROL / CONCEPT ENGINEERING
            </span>
            <h1>
              {model?.name || "From mission intent to engineering evidence."}
            </h1>
          </div>
          <div className="header-status">
            <span className="dot" />{" "}
            {model
              ? "REV " + String(model.revision).padStart(3, "0")
              : "LOCAL WORKSPACE"}
            <small>{model?.phase || "Ready to begin"}</small>
          </div>
        </header>
        {error && (
          <div role="alert" className="error">
            {error}{" "}
            <button className="text-button" onClick={() => setError("")}>
              Dismiss
            </button>
          </div>
        )}
        {success && (
          <div role="status" className="success">
            {success}
          </div>
        )}
        {busy && (
          <div role="status" className="loading">
            Working · validating and recording model changes…
          </div>
        )}
        {!model ? (
          <section className="welcome">
            <div className="panel">
              <span className="eyebrow">01 / DEFINE THE MISSION</span>
              <h2>Start with a brief.</h2>
              <p className="muted">
                The reference workflow proposes explicit assumptions, derives
                requirements, compares concepts and stops at every human
                decision gate.
              </p>
              <label>
                Mission name
                <input value={name} onChange={(e) => setName(e.target.value)} />
              </label>
              <label>
                Natural-language mission brief
                <textarea
                  rows={7}
                  value={brief}
                  onChange={(e) => setBrief(e.target.value)}
                />
              </label>
              <div className="notice">
                Reference scenario mode: wildfire CubeSat only. The first
                approval explicitly confirms the scenario constraints; arbitrary
                briefs are retained but not generally interpreted.
              </div>
              <button
                disabled={busy || brief.length < 20 || !name.trim()}
                onClick={() =>
                  run(
                    () => request("/missions", { name, brief }),
                    "Mission created. Review the proposed assumptions.",
                  )
                }
              >
                Create mission →
              </button>
            </div>
            <div>
              <div className="panel">
                <h3>Saved missions</h3>
                <label className="check">
                  <input
                    type="checkbox"
                    checked={showArchived}
                    onChange={(e) => setShowArchived(e.target.checked)}
                  />{" "}
                  Show archived missions
                </label>
                {showArchived ? (
                  <section aria-label="Archived missions">
                    <p className="muted">
                      Archived missions retain their history and baselines.
                      Restore a mission before continuing work.
                    </p>
                    {archivedList.length ? (
                      archivedList.map((m) => (
                        <div key={m.id} className="timeline">
                          <span>{m.name}</span>
                          <button
                            disabled={busy}
                            onClick={() => archiveMission(m, false)}
                          >
                            Restore {m.name}
                          </button>
                        </div>
                      ))
                    ) : (
                      <p>No archived missions.</p>
                    )}
                  </section>
                ) : (
                  <>
                    {list.length ? (
                      list.map((m) => (
                        <div key={m.id}>
                          <button
                            className="mission-link"
                            disabled={busy}
                            key={m.id}
                            onClick={() =>
                              run(
                                () => request("/missions/" + m.id),
                                "Mission loaded",
                              )
                            }
                          >
                            {m.name} →
                          </button>
                          <button
                            className="secondary"
                            disabled={busy}
                            onClick={() => archiveMission(m, true)}
                          >
                            Archive {m.name}
                          </button>
                        </div>
                      ))
                    ) : (
                      <p className="muted">
                        No missions yet. Your first design starts here.
                      </p>
                    )}
                  </>
                )}
              </div>
              <div className="panel">
                <h3>Private workspace access</h3>
                <p className="muted">
                  Local demo needs no token. For a protected server, enter your
                  configured mission owner token.
                </p>
                <label>
                  Owner token
                  <input
                    type="password"
                    value={token}
                    onChange={(e) => setTokenInput(e.target.value)}
                  />
                </label>
                <button
                  className="secondary"
                  onClick={() => {
                    setToken(token);
                    setTokenInput("");
                    void run(() => loadList(), "Access configuration updated");
                  }}
                >
                  Connect
                </button>
              </div>
            </div>
          </section>
        ) : (
          <>
            <div className="toolbar">
              <div>
                <Badge value={model.phase} />
                <span className="muted">
                  {" "}
                  {model.paused
                    ? "Workflow paused"
                    : "Human-controlled progression"}{" "}
                  · {objects.length} model objects
                </span>
              </div>
              <div className="actions">
                <button
                  className="secondary"
                  disabled={busy}
                  onClick={() => {
                    setModel(null);
                    setDetail(null);
                  }}
                >
                  Switch mission
                </button>
                <button
                  className="secondary"
                  disabled={busy}
                  onClick={() => archiveMission(model, true)}
                >
                  Archive mission
                </button>
                {!model.baseline && (
                  <button
                    className="secondary"
                    disabled={busy}
                    onClick={() => act("/pause")}
                  >
                    {model.paused ? "Resume" : "Pause"}
                  </button>
                )}
              </div>
            </div>
            {tab === "Overview" && (
              <>
                <section className="hero">
                  <div>
                    <span className="eyebrow">PYRA / EARTH OBSERVATION</span>
                    <h2>
                      Wildfire intelligence.
                      <br />
                      An accountable design.
                    </h2>
                    <p>{model.brief}</p>
                  </div>
                  <div className="orbital">
                    <div className="earth">
                      EU<span>Conceptual LEO</span>
                    </div>
                    <div className="satellite">▣</div>
                  </div>
                </section>
                <div className="metrics">
                  <div>
                    <span>DESIGN MATURITY</span>
                    <strong>
                      {model.baseline ? "Concept baselined" : model.phase}
                    </strong>
                    <small>Feasibility remains unverified</small>
                  </div>
                  <div>
                    <span>OPEN CONFLICTS</span>
                    <strong>{open.length.toString().padStart(2, "0")}</strong>
                    <small>Independent review + cross-discipline</small>
                  </div>
                  <div>
                    <span>HUMAN DECISIONS</span>
                    <strong>
                      {pending.length +
                        (model.phase === "Ready for baseline" ? 1 : 0)}
                    </strong>
                    <small>Pending explicit approval</small>
                  </div>
                  <div>
                    <span>MISSION RISK</span>
                    <strong>
                      {objects.some((e) => e.kind === "Risk")
                        ? "High / open"
                        : "Not yet assessed"}
                    </strong>
                    <small>Latency · coverage · lifetime · cost</small>
                  </div>
                </div>
                <div className="section-title">
                  <h2>Engineering margins</h2>
                  <span className="muted">
                    {model.selected
                      ? "Selected concept"
                      : "Candidate B preview"}
                  </span>
                </div>
                <div className="budget-grid">
                  {budgets.length ? (
                    budgets.map((e) => (
                      <button
                        className="budget-card"
                        key={e.id}
                        onClick={() => show(e)}
                      >
                        <span>{e.title.split(" · ")[1].toUpperCase()}</span>
                        {e.state === "stale" ? (
                          <strong>Stale — recalculate</strong>
                        ) : (
                          <Value value={e.data.margin} />
                        )}
                        <small
                          className={
                            e.state === "stale"
                              ? "muted"
                              : e.data.compliant
                                ? "pass"
                                : "fail"
                          }
                        >
                          {e.state === "stale"
                            ? "Previous results are no longer current"
                            : e.data.compliant
                              ? "Positive preliminary margin"
                              : "Constraint violation"}
                        </small>
                      </button>
                    ))
                  ) : (
                    <div className="empty">
                      Budgets appear after requirements and architecture
                      proposals are approved.
                    </div>
                  )}
                </div>
                <section className="panel">
                  <h3>Next engineering gate</h3>
                  {pending.length ? (
                    <p>
                      Review {pending[0].proposal_type} below. Proposed content
                      is separate from accepted model objects.
                    </p>
                  ) : (
                    <p>
                      {model.phase === "Trade study"
                        ? "Open Trades to inspect weights and select a compliant concept."
                        : model.phase === "Ready for baseline"
                          ? "Open Baselines & replay to approve the conceptual baseline."
                          : model.baseline
                            ? "Baseline approved. Export the report or replay the engineering history."
                            : "Advance the workflow to execute the next dependent task."}
                    </p>
                  )}
                  {!pending.length &&
                    ![
                      "Trade study",
                      "Impact review",
                      "Ready for baseline",
                      "Baselined",
                    ].includes(model.phase) && (
                      <button
                        disabled={busy || model.paused}
                        onClick={() => act("/advance")}
                      >
                        {model.phase === "Recalculation required"
                          ? "Recalculate engineering budgets"
                          : model.phase === "Review"
                            ? "Propose finding resolution"
                            : model.phase === "Resolution proposed"
                              ? "Verify resolution independently"
                              : model.phase === "Selected concept"
                                ? "Run independent review"
                                : "Advance workflow →"}
                      </button>
                    )}
                  {model.phase === "Trade study" && (
                    <button onClick={() => setTab("Trades")}>
                      Inspect trade study →
                    </button>
                  )}
                  {["Ready for baseline", "Baselined"].includes(
                    model.phase,
                  ) && (
                    <button onClick={() => setTab("Baselines & replay")}>
                      Open baseline workspace →
                    </button>
                  )}
                </section>
              </>
            )}
            {pending.length > 0 && (
              <section>
                <label>
                  Decision rationale
                  <input
                    value={reason}
                    onChange={(e) => setReason(e.target.value)}
                  />
                </label>
                {pending.map(proposal)}
              </section>
            )}
            {model.phase === "Recalculation required" && tab !== "Overview" && (
              <section className="panel">
                <h3>Engineering results need recalculation</h3>
                <p>
                  Accepted input changes invalidate the previous analyses,
                  trade, selection and review.
                </p>
                <button
                  disabled={busy || model.paused || pending.length > 0}
                  onClick={() => act("/advance")}
                >
                  Recalculate engineering budgets
                </button>
              </section>
            )}
            {model.phase === "Impact review" && (
              <section className="panel">
                <h2>Review affected design content</h2>
                <p>
                  Inspect or edit these objects before reaffirming them.
                  Reaffirmation does not validate numerical results.
                </p>
                {affectedDesign.map((e) => (
                  <button
                    className="mission-link"
                    key={e.id}
                    onClick={() => show(e)}
                  >
                    {e.kind}: {e.title}
                  </button>
                ))}
                <label>
                  Impact review rationale
                  <input
                    value={reason}
                    onChange={(e) => setReason(e.target.value)}
                  />
                </label>
                <label className="check">
                  <input
                    type="checkbox"
                    checked={impactConfirmed}
                    onChange={(e) => setImpactConfirmed(e.target.checked)}
                  />
                  I reviewed the affected assumptions, requirements and design
                  inputs and reaffirm this content.
                </label>
                <button
                  disabled={busy || !impactConfirmed || pending.length > 0}
                  onClick={() =>
                    act("/review-impact", { reason, confirm: impactConfirmed })
                  }
                >
                  Confirm impact review
                </button>
              </section>
            )}
            {tab === "Coverage & access" && (
              <CoverageView
                model={model}
                busy={busy || pending.length > 0}
                onInitialize={() => void act("/initialize-access")}
                onInspect={(id) => show(model.entities[id])}
              />
            )}
            {tab === "Data delivery" && (
              <DeliveryView
                model={model}
                busy={busy || pending.length > 0}
                onInitialize={() => void act("/initialize-delivery")}
                onInspect={(id) => show(model.entities[id])}
              />
            )}
            {tab === "Design inputs" && (
              <section className="panel">
                <h2>Accepted calculation inputs</h2>
                <p>
                  Select an input group to edit quantities and units.
                  Calculators read these accepted values; changing a requirement
                  statement requires human impact review and does not
                  automatically infer new numbers.
                </p>
                {model.baseline ? (
                  <p className="notice">
                    Open Baselines & replay and reopen the baseline before
                    editing.
                  </p>
                ) : !model.entities["mission-orbit-inputs"] &&
                  model.entities.selective ? (
                  <button
                    disabled={busy || pending.length > 0}
                    onClick={() => act("/initialize-inputs")}
                  >
                    Initialize editable inputs
                  </button>
                ) : (
                  <p className="muted">
                    Period and eclipse come from the orbit tool. Downlink demand
                    comes from the data tool. These derived inputs cannot be
                    overridden.
                  </p>
                )}
              </section>
            )}
            {tab === "Brief & assumptions" && (
              <section className="panel">
                <h2>Mission brief</h2>
                <p>{model.brief}</p>
                <p className="notice">
                  Approved assumptions establish the sizing basis. Numerical
                  assumptions are not sourced facts or verified performance.
                </p>
              </section>
            )}
            {tab === "Trades" && model.phase === "Trade study" && (
              <section className="panel">
                <h2>Select an integrated concept</h2>
                <p>
                  Science and simplicity scores are estimates. Capacity scores
                  and weighted totals follow current calculations. Select a
                  candidate only when all four budgets comply.
                </p>
                <div className="weights">
                  {Object.entries(weights).map(([k, v]) => (
                    <label key={k}>
                      {k} weight
                      <input
                        type="number"
                        min="0"
                        max="1"
                        step="0.05"
                        value={v}
                        onChange={(e) =>
                          setWeights({
                            ...weights,
                            [k]: Number(e.target.value),
                          })
                        }
                      />
                    </label>
                  ))}
                </div>
                <label>
                  Selection rationale
                  <input
                    value={reason}
                    onChange={(e) => setReason(e.target.value)}
                  />
                </label>
                <div className="actions">
                  {["wide", "selective"].map((candidate) => {
                    const compliant = ["mass", "power", "data", "link"].every(
                      (tool) =>
                        model.entities[`${candidate}-${tool}`]?.state ===
                          "accepted" &&
                        model.entities[`${candidate}-${tool}`]?.data
                          .compliant === true,
                    );
                    const failedRequirements = objects.some(
                      (e) =>
                        e.kind === "VerificationItem" &&
                        e.data.candidate === candidate &&
                        model.entities[e.data.requirement]?.data.priority ===
                          "must" &&
                        (e.state === "stale" ||
                          ["fail", "stale"].includes(e.data.status)),
                    );
                    return (
                      <div key={candidate}>
                        <button
                          disabled={busy || !compliant || failedRequirements}
                          onClick={() =>
                            act("/select", { candidate, weights, reason })
                          }
                        >
                          Select{" "}
                          {candidate === "wide"
                            ? "A · Wide-area continuous imaging"
                            : "B · Event-selective imaging + X-band"}
                        </button>
                        {!compliant && (
                          <p className="fail">
                            Resolve failing or stale budgets before selecting
                            this concept.
                          </p>
                        )}
                      </div>
                    );
                  })}
                </div>
              </section>
            )}
            {tab === "Baselines & replay" && (
              <>
                <section className="panel">
                  <h2>
                    {model.baseline
                      ? "Immutable conceptual baseline"
                      : "Baseline approval"}
                  </h2>
                  {model.baseline ? (
                    <>
                      <p>
                        Baseline {model.baseline} · revision {model.revision}
                      </p>
                      <label>
                        Revision rationale
                        <input
                          value={reason}
                          onChange={(e) => setReason(e.target.value)}
                        />
                      </label>
                      <button
                        className="secondary"
                        disabled={busy}
                        onClick={() => act("/reopen", { reason })}
                      >
                        Reopen baseline for design changes
                      </button>
                      <div className="actions">
                        {["md", "json", "csv"].map((f) => (
                          <button
                            key={f}
                            onClick={() =>
                              run(
                                () => download(base + "/export/" + f, f),
                                "Export downloaded",
                              )
                            }
                          >
                            Export {f.toUpperCase()}
                          </button>
                        ))}
                      </div>
                    </>
                  ) : model.phase === "Ready for baseline" ? (
                    <>
                      <p>
                        Independent review verified the evidence correction.
                        Delivery latency, coverage, detection sensitivity,
                        lifetime and cost remain unverified.
                      </p>
                      <label>
                        Baseline name
                        <input
                          value={baselineName}
                          onChange={(e) => setBaselineName(e.target.value)}
                        />
                      </label>
                      <label className="check">
                        <input
                          type="checkbox"
                          checked={confirm}
                          onChange={(e) => setConfirm(e.target.checked)}
                        />{" "}
                        I approve this conceptual baseline and acknowledge the
                        recorded residual risks and verification obligations.
                      </label>
                      <button
                        disabled={!confirm || busy}
                        onClick={() =>
                          act("/baseline", {
                            name: baselineName,
                            confirm,
                          })
                        }
                      >
                        Approve immutable baseline
                      </button>
                    </>
                  ) : (
                    <p className="muted">
                      Complete selection, independent review and verified
                      finding resolution before approving a baseline.
                    </p>
                  )}
                </section>
                <BaselineComparison
                  key={model.id}
                  missionId={model.id}
                  revision={model.revision}
                />
                <section className="panel">
                  <div className="row">
                    <h2>Saved immutable baselines</h2>
                    <button
                      className="secondary"
                      onClick={() =>
                        run(async () => {
                          setBaselineList(await request(base + "/baselines"));
                        }, "Baselines loaded")
                      }
                    >
                      Load baseline history
                    </button>
                  </div>
                  {baselineList.map((b) => (
                    <div className="timeline" key={b.id}>
                      <div>
                        <b>{b.name}</b> · revision {b.revision}
                        <div className="actions">
                          {["json", "md", "csv"].map((f) => (
                            <button
                              className="secondary"
                              key={f}
                              onClick={() =>
                                run(
                                  () =>
                                    download(
                                      `${base}/export/${f}?baseline_id=${b.id}`,
                                      f,
                                    ),
                                  "Historical baseline downloaded",
                                )
                              }
                            >
                              Export {b.name} {f.toUpperCase()}
                            </button>
                          ))}
                        </div>
                      </div>
                    </div>
                  ))}
                </section>
                <section className="panel">
                  <div className="row">
                    <h2>Revision replay & comparison</h2>
                    <button
                      className="secondary"
                      onClick={() =>
                        run(async () => {
                          setHistory(await request(base + "/history"));
                        }, "Timeline loaded")
                      }
                    >
                      Load replay timeline
                    </button>
                  </div>
                  {history.length > 0 && (
                    <label>
                      Historical revision
                      <select
                        aria-label="Historical revision"
                        defaultValue=""
                        onChange={(e) =>
                          void run(async () => {
                            setPast(
                              await request(
                                base + "/revisions/" + e.target.value,
                              ),
                            );
                          }, "Historical revision loaded")
                        }
                      >
                        <option value="" disabled>
                          Select a revision
                        </option>
                        {history.map((h) => (
                          <option key={h.revision} value={h.revision}>
                            r{h.revision} · {h.reason}
                          </option>
                        ))}
                      </select>
                    </label>
                  )}
                  {past && (
                    <>
                      <div className="comparison">
                        <div>
                          <h3>
                            Revision {past.revision} · {past.phase}
                          </h3>
                          <p>{Object.keys(past.entities).length} objects</p>
                        </div>
                        <div>
                          <h3>
                            Current revision {model.revision} · {model.phase}
                          </h3>
                          <p>{objects.length} objects</p>
                        </div>
                      </div>
                      <h3>Changed objects</h3>
                      {objects
                        .filter(
                          (e) =>
                            JSON.stringify(e) !==
                            JSON.stringify(past.entities[e.id]),
                        )
                        .map((e) => (
                          <button
                            className="mission-link"
                            key={e.id}
                            onClick={() => show(e)}
                          >
                            {past.entities[e.id] ? "Changed" : "Added"} ·{" "}
                            {e.title}
                          </button>
                        ))}
                      <details>
                        <summary>Inspect full historical model</summary>
                        <pre>{JSON.stringify(past, null, 2)}</pre>
                      </details>
                      <button
                        className="secondary"
                        disabled={busy}
                        onClick={() => {
                          if (
                            window.confirm(
                              "Create a new current revision from this historical state? Existing baselines and history remain immutable.",
                            )
                          )
                            void act("/restore", {
                              source_revision: past.revision,
                            });
                        }}
                      >
                        Restore as new revision
                      </button>
                    </>
                  )}
                  {history.map((h) => (
                    <div className="timeline" key={h.revision}>
                      <b>r{h.revision}</b>
                      <div>
                        {h.reason}
                        <small>
                          {h.actor} · {h.created_at}
                        </small>
                      </div>
                    </div>
                  ))}
                </section>
              </>
            )}
            {tab !== "Overview" &&
              tab !== "Coverage & access" &&
              tab !== "Data delivery" && (
                <section>
                  <div className="section-title">
                    <h2>{tab}</h2>
                    <label className="search">
                      Search model objects
                      <input
                        placeholder="ID, text, owner, state…"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                      />
                    </label>
                  </div>
                  <div
                    className={
                      tab === "Architectures"
                        ? "architecture-grid"
                        : "object-list"
                    }
                  >
                    {objects
                      .filter(
                        (e) =>
                          tabs[tab].includes(e.kind) &&
                          JSON.stringify(e)
                            .toLowerCase()
                            .includes(query.toLowerCase()),
                      )
                      .map((e) => (
                        <button
                          className="object-card"
                          disabled={busy}
                          key={e.id}
                          onClick={() => show(e)}
                        >
                          <div className="row">
                            <span className="eyebrow">
                              {e.kind} / {e.id.slice(0, 24)}
                            </span>
                            <Badge value={e.state} />
                          </div>
                          <h3>{e.title}</h3>
                          {e.kind === "Requirement" && (
                            <p>
                              {e.data.criterion
                                ? `${e.data.criterion.metric} ${e.data.criterion.operator} ${e.data.criterion.threshold.value} ${e.data.criterion.threshold.unit}`
                                : "No quantitative criterion · unverified"}
                              {["wide", "selective"].map((candidate) => {
                                const check =
                                  model.entities[`check-${e.id}-${candidate}`];
                                return (
                                  <span key={candidate}>
                                    {" "}
                                    · {candidate}:{" "}
                                    {e.state === "stale" ||
                                    check?.state === "stale"
                                      ? "stale"
                                      : check?.data.status || "unverified"}
                                  </span>
                                );
                              })}
                            </p>
                          )}
                          <div className="row">
                            <Badge value={e.classification} />
                            <small>
                              {e.owner} · r{e.revision}
                            </small>
                          </div>
                          {e.kind === "Budget" && (
                            <p>
                              <Value value={e.data.margin} /> margin
                            </p>
                          )}
                          {e.kind === "ArchitectureAlternative" && (
                            <p>{e.data.conops}</p>
                          )}
                        </button>
                      ))}
                  </div>
                  {tab !== "Coverage & access" &&
                    !objects.some((e) => tabs[tab].includes(e.kind)) && (
                      <p className="empty">
                        No {tab.toLowerCase()} objects at this revision.
                      </p>
                    )}
                </section>
              )}
          </>
        )}
        <footer>
          MISSION FOUNDRY{" "}
          <span>Conceptual engineering · auditable by design · v0.1</span>
        </footer>
      </main>
      {detail && (
        <div className="dialog-backdrop" onClick={() => setDetail(null)}>
          <section
            ref={detailRef}
            role="dialog"
            aria-modal="true"
            aria-label="Engineering object details"
            className="detail"
            onClick={(e) => e.stopPropagation()}
            onKeyDown={(e) => {
              if (e.key === "Escape") setDetail(null);
              if (e.key === "Tab") {
                const nodes = detailRef.current?.querySelectorAll<HTMLElement>(
                  'button:not(:disabled), input, select, textarea, [tabindex="0"]',
                );
                if (nodes?.length) {
                  const first = nodes[0],
                    last = nodes[nodes.length - 1];
                  if (e.shiftKey && document.activeElement === first) {
                    e.preventDefault();
                    last.focus();
                  } else if (!e.shiftKey && document.activeElement === last) {
                    e.preventDefault();
                    first.focus();
                  }
                }
              }
            }}
          >
            <button
              autoFocus
              className="secondary close"
              onClick={() => setDetail(null)}
            >
              Close details
            </button>
            <span className="eyebrow">
              {detail.kind} / {detail.id}
            </span>
            <h2>{detail.title}</h2>
            <Badge value={detail.classification} />
            <p>
              {detail.state} · Owner {detail.owner} · Revision {detail.revision}
            </p>
            {detail.kind === "Requirement" && model && (
              <section aria-label="Requirement verification results">
                <h3>Verification results</h3>
                <p>
                  These checks assess the declared criterion under concept
                  assumptions. Unverified requirements remain open obligations.
                </p>
                {["wide", "selective"].map((candidate) => {
                  const check =
                    model.entities[`check-${detail.id}-${candidate}`];
                  const status =
                    detail.state === "stale" || check?.state === "stale"
                      ? "stale"
                      : check?.data.status || "unverified";
                  return (
                    <div key={candidate}>
                      <h4>
                        {candidate} · {status}
                      </h4>
                      <p>
                        {status === "stale"
                          ? "Previous evidence is stale; review and recalculate."
                          : check?.data.reason ||
                            "No current calculation check is available."}
                      </p>
                      {status !== "stale" && check?.data.actual && (
                        <p>
                          Measured: <Value value={check.data.actual} />
                        </p>
                      )}
                      {check && (
                        <button onClick={() => show(check)}>
                          Inspect {candidate} check and evidence
                        </button>
                      )}
                    </div>
                  );
                })}
              </section>
            )}
            {detail.state === "stale" && (
              <p className="notice">
                This object is stale. The values below describe the previous
                design and must not be treated as current results.
              </p>
            )}
            {model &&
              !model.baseline &&
              !pending.length &&
              ["accepted", "stale"].includes(detail.state) &&
              ["Assumption", "Requirement", "Parameter"].includes(
                detail.kind,
              ) &&
              model.entities[detail.id] && (
                <DesignEditor
                  key={`${model.id}:${detail.id}:${detail.revision}`}
                  entity={detail}
                  missionId={model.id}
                  revision={model.revision}
                  onProposed={(m) => {
                    receiveModel(m);
                    setDetail(null);
                    setSuccess(
                      "Change proposed. Review and approve it before recalculating.",
                    );
                  }}
                />
              )}
            <dl>
              {Object.entries(detail.data).map(([k, v]) => (
                <div key={k}>
                  <dt>{k.replaceAll("_", " ")}</dt>
                  <dd>
                    <Value value={v} />
                  </dd>
                </div>
              ))}
            </dl>
            <h3>Upstream relationships</h3>
            {detail.relations.map((r) => (
              <button
                key={r.type + r.target}
                className="mission-link"
                disabled={!model?.entities[r.target]}
                onClick={() => show(model!.entities[r.target])}
              >
                {r.type} → {r.target}
              </button>
            ))}
            <h3>Downstream relationships</h3>
            {objects
              .filter((e) => e.relations.some((r) => r.target === detail.id))
              .map((e) => (
                <button
                  key={e.id}
                  className="mission-link"
                  onClick={() => show(e)}
                >
                  {e.kind} → {e.title}
                </button>
              ))}
          </section>
        </div>
      )}
    </div>
  );
}
