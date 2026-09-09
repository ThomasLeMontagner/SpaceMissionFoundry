import { useEffect, useState, useRef } from "react";
import { request, download, setToken, subscribe } from "./api";
import type { Entity, Model, Proposal } from "./types";

const tabs: Record<string, string[]> = {
  Overview: [],
  "Brief & assumptions": ["Mission", "Assumption"],
  Requirements: ["Objective", "Requirement"],
  Architectures: ["ArchitectureAlternative", "Function", "Component"],
  Interfaces: ["Interface"],
  Budgets: ["Budget", "BudgetEntry", "AnalysisRun"],
  Trades: ["TradeStudy"],
  "Claims & evidence": ["Claim", "Evidence", "Parameter"],
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
    [list, setList] = useState<{ id: string; name: string }[]>([]),
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
    [history, setHistory] = useState<any[]>([]),
    [past, setPast] = useState<Model | null>(null),
    [token, setTokenInput] = useState("");
  const detailRef = useRef<HTMLElement>(null);
  useEffect(() => {
    if (!detail) return;
    const previous = document.activeElement as HTMLElement | null;
    return () => previous?.focus();
  }, [!!detail]);
  const loadList = () => request("/missions").then(setList);
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
    return subscribe(model.id, () => {
      request("/missions/" + model.id)
        .then(setModel)
        .catch((e) => setError(e.message));
    });
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
      if (result?.entities) setModel(result);
      setSuccess(message);
      await loadList();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  const base = model ? "/missions/" + model.id : "";
  const act = (path: string, body: object = {}) =>
    run(() => request(base + path, { revision: model!.revision, ...body }));
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
                {list.length ? (
                  list.map((m) => (
                    <button
                      className="mission-link"
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
                  ))
                ) : (
                  <p className="muted">
                    No missions yet. Your first design starts here.
                  </p>
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
                  onClick={() => {
                    setModel(null);
                    setDetail(null);
                  }}
                >
                  Switch mission
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
                      EU<span>550 km assumed LEO</span>
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
                        <Value value={e.data.margin} />
                        <small className={e.data.compliant ? "pass" : "fail"}>
                          {e.data.compliant
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
                      "Ready for baseline",
                      "Baselined",
                    ].includes(model.phase) && (
                      <button
                        disabled={busy || model.paused}
                        onClick={() => act("/advance")}
                      >
                        {model.phase === "Review"
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
            {pending.length > 0 &&
              [
                "Overview",
                "Brief & assumptions",
                "Requirements",
                "Architectures",
              ].includes(tab) && (
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
                  Criterion scores are engineering estimates. Weighted totals
                  are calculated deterministically. Candidate A fails downlink
                  capacity; candidate B preserves an explicit science dissent.
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
                <button
                  disabled={busy}
                  onClick={() =>
                    act("/select", { candidate: "selective", weights, reason })
                  }
                >
                  Select B · Event-selective imaging + X-band
                </button>
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
                            name: "Mission Concept Baseline 1",
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
            {tab !== "Overview" && (
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
                {!objects.some((e) => tabs[tab].includes(e.kind)) && (
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
