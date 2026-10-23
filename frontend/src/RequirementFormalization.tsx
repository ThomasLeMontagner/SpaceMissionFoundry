import { useEffect, useState } from "react";
import { request } from "./api";
import RequirementLinks from "./RequirementLinks";
import RequirementQuality from "./RequirementQuality";
import type { Model } from "./types";

type Props = {
  model: Model;
  busy: boolean;
  act: (path: string, body?: any) => Promise<void>;
};
export default function RequirementFormalization(props: Props) {
  const { model } = props;
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState("");
  const [selected, setSelected] = useState("");
  useEffect(() => {
    let active = true;
    setError("");
    setData(null);
    request(`/missions/${model.id}/requirement-formalization`)
      .then((value) => {
        if (active) setData({ ...value, missionId: model.id });
      })
      .catch((e) => {
        if (active) setError(String(e));
      });
    return () => {
      active = false;
    };
  }, [model.id, model.revision]);
  if (error) return <p role="alert">{error}</p>;
  if (!data || data.missionId !== model.id || data.revision !== model.revision)
    return <p>Loading requirement readiness…</p>;
  const row =
    data.requirements.find((r: any) => r.id === selected) ||
    data.requirements[0];
  return (
    <section className="panel">
      <h2>Requirement readiness</h2>
      <p>
        Clarify the statement, propose a measurable criterion, then review it in
        Conflicts & review. This owner-guided workflow makes no AI model calls.
      </p>
      <p>
        Partial coverage cannot verify the whole requirement. Full coverage is
        your assessment of scope, not flight certification. Existing criteria
        without a scope assessment retain their previous checking behavior.
      </p>
      {data.quality && (
        <RequirementQuality
          report={data.quality}
          onSelect={setSelected}
          requirementIds={data.requirements.map((r: any) => r.id)}
        />
      )}
      {row ? (
        <>
          {(model.entities[row.id].relations || [])
            .filter(
              (r) =>
                r.type === "derives_from" &&
                model.entities[r.target]?.kind === "Requirement",
            )
            .map((r) => (
              <p key={r.target}>
                Parent requirement:{" "}
                <button onClick={() => setSelected(r.target)}>
                  {model.entities[r.target].title}
                </button>
              </p>
            ))}
          {Object.values(model.entities).some(
            (e) =>
              e.kind === "Requirement" &&
              (e.relations || []).some(
                (r) => r.type === "derives_from" && r.target === row.id,
              ),
          ) && (
            <div>
              <h3>Derived requirements</h3>
              <p>Child checks do not automatically verify this parent.</p>
              <ul>
                {Object.values(model.entities)
                  .filter(
                    (e) =>
                      e.kind === "Requirement" &&
                      (e.relations || []).some(
                        (r) => r.type === "derives_from" && r.target === row.id,
                      ),
                  )
                  .map((e) => (
                    <li key={e.id}>
                      <button onClick={() => setSelected(e.id)}>
                        {e.title}
                      </button>
                    </li>
                  ))}
              </ul>
            </div>
          )}

          <label>
            Requirement to clarify
            <select
              value={row.id}
              onChange={(e) => setSelected(e.target.value)}
            >
              {data.requirements.map((r: any) => (
                <option key={r.id} value={r.id}>
                  {r.title} — {r.status.replaceAll("_", " ")}
                </option>
              ))}
            </select>
          </label>
          <RequirementLinks
            key={`links:${model.id}:${row.id}:${model.revision}`}
            model={model}
            requirementId={row.id}
            busy={props.busy}
            act={props.act}
          />
          <Editor
            key={`${model.id}:${row.id}:${model.entities[row.id].revision}`}
            {...props}
            row={row}
            data={data}
          />
        </>
      ) : (
        <p>Approve the initial requirements to begin.</p>
      )}
    </section>
  );
}
function Editor({
  model,
  busy,
  act,
  row,
  data,
}: Props & { row: any; data: any }) {
  const [metric, setMetric] = useState(row.criterion?.metric || "");
  const [operator, setOperator] = useState(row.criterion?.operator || "<=");
  const [threshold, setThreshold] = useState(
    String(row.criterion?.threshold.value ?? ""),
  );
  const [unit, setUnit] = useState(row.criterion?.threshold.unit || "");
  const [basis, setBasis] = useState(row.formalization?.basis || "");
  const [coverage, setCoverage] = useState("partial");
  const [confirmed, setConfirmed] = useState(false);
  const [questions, setQuestions] = useState(
    (row.formalization?.open_questions || []).join("\n"),
  );
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [reply, setReply] = useState<string | null>(null);
  const disabled = busy || !!model.baseline || !!model.archived;
  const notes = data.notes.filter((n: any) => n.requirement_id === row.id);
  const superseded = new Set(notes.map((n: any) => n.reply_to));
  return (
    <>
      <p>
        <strong>Readiness:</strong> {row.status.replaceAll("_", " ")}
      </p>
      {row.suggestion && (
        <div className="notice">
          <p>
            Suggested deadline from the statement: “
            {row.suggestion.source_quote}”. {row.suggestion.explanation}
          </p>
          <button
            disabled={disabled}
            onClick={() => {
              const c = row.suggestion.criterion;
              setMetric(c.metric);
              setOperator(c.operator);
              setThreshold(String(c.threshold.value));
              setUnit(c.threshold.unit);
              setCoverage("partial");
              setConfirmed(false);
            }}
          >
            Use suggested deadline
          </button>
        </div>
      )}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          void act(`/requirements/${row.id}/formalize`, {
            criterion: metric
              ? {
                  metric,
                  operator,
                  threshold: { value: Number(threshold), unit },
                }
              : null,
            basis,
            coverage,
            confirm_full_coverage: confirmed,
            open_questions: questions
              .split("\n")
              .map((q: string) => q.trim())
              .filter(Boolean),
          });
        }}
      >
        <fieldset disabled={disabled}>
          <legend>Propose criterion and scope</legend>
          <label>
            Measured quantity
            <select
              value={metric}
              onChange={(e) => {
                setMetric(e.target.value);
                setUnit(data.metrics[e.target.value]?.unit || "");
                setThreshold("");
                setOperator("<=");
              }}
            >
              <option value="">No supported criterion yet</option>
              {Object.entries(data.metrics).map(([id, m]: [string, any]) => (
                <option key={id} value={id}>
                  {m.label}
                </option>
              ))}
            </select>
          </label>
          {metric && (
            <>
              <label>
                Comparison
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
                Threshold
                <input
                  type="number"
                  min="0"
                  step="any"
                  required
                  value={threshold}
                  onChange={(e) => setThreshold(e.target.value)}
                />
              </label>
              <label>
                Threshold unit
                <input
                  required
                  value={unit}
                  onChange={(e) => setUnit(e.target.value)}
                />
              </label>
            </>
          )}
          <label>
            Basis and applicability
            <textarea
              required
              minLength={3}
              maxLength={2000}
              value={basis}
              onChange={(e) => setBasis(e.target.value)}
            />
          </label>
          <label>
            Unresolved questions (one per line, maximum ten)
            <textarea
              value={questions}
              onChange={(e) => setQuestions(e.target.value)}
            />
          </label>
          <label>
            Criterion coverage
            <select
              value={coverage}
              onChange={(e) => {
                setCoverage(e.target.value);
                setConfirmed(false);
              }}
            >
              <option value="partial">Partial or unresolved</option>
              <option value="full">Entire requirement</option>
            </select>
          </label>
          {coverage === "full" && (
            <label>
              <input
                type="checkbox"
                required
                checked={confirmed}
                onChange={(e) => setConfirmed(e.target.checked)}
              />
              I confirm that this criterion covers the entire statement,
              including its conditions and workload.
            </label>
          )}
          <p>
            Current clarification notes are linked automatically. Unanswered
            questions prevent full coverage.
          </p>
          <button type="submit">Propose formalization</button>
        </fieldset>
      </form>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          void act(`/requirements/${row.id}/clarify`, {
            question,
            answer,
            reply_to: reply,
          });
        }}
      >
        <fieldset disabled={disabled}>
          <legend>Record clarification</legend>
          <label>
            Clarification question
            <textarea
              required
              minLength={3}
              maxLength={1000}
              readOnly={!!reply}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
            />
          </label>
          <label>
            Clarification answer
            <textarea
              required={!!reply}
              maxLength={2000}
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
            />
          </label>
          <button type="submit">Save clarification</button>
          {reply && (
            <button
              type="button"
              onClick={() => {
                setReply(null);
                setQuestion("");
                setAnswer("");
              }}
            >
              New question
            </button>
          )}
        </fieldset>
      </form>
      {notes.map((n: any) => {
        const current =
          n.source_requirement.revision === model.entities[row.id].revision;
        return (
          <article key={n.id}>
            <strong>{n.question}</strong>
            <p>
              {n.answer || "Awaiting answer"} — recorded at revision{" "}
              {n.source_revision}
              {!current
                ? " (earlier requirement)"
                : superseded.has(n.id)
                  ? " (superseded by reply)"
                  : ""}
            </p>
            {current && !superseded.has(n.id) && (
              <button
                disabled={disabled}
                onClick={() => {
                  setReply(n.id);
                  setQuestion(n.question);
                  setAnswer("");
                }}
              >
                Answer question
              </button>
            )}
          </article>
        );
      })}
    </>
  );
}
