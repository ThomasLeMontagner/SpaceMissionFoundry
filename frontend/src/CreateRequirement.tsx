import { useState } from "react";
import type { Model } from "./types";

export default function CreateRequirement({
  model,
  busy,
  act,
}: {
  model: Model;
  busy: boolean;
  act: (path: string, body?: any) => Promise<void>;
}) {
  const [statement, setStatement] = useState("");
  const [rationale, setRationale] = useState("");
  const [source, setSource] = useState("");
  const [level, setLevel] = useState("system");
  const [priority, setPriority] = useState("must");
  const [method, setMethod] = useState("review");
  const [parents, setParents] = useState<string[]>([]);
  const choices = Object.values(model.entities).filter(
    (e) =>
      ["Requirement", "Objective"].includes(e.kind) &&
      ["accepted", "stale"].includes(e.state),
  );
  return (
    <section className="panel" aria-label="Create requirement">
      <details>
        <summary>Add a requirement</summary>
        <p>
          Write a requirement and identify its source and originating need.
          Submission creates a proposal; a separate approval adds it to the
          mission. It starts unverified with partial scope. Select a criterion
          later in Requirement readiness.
        </p>
        {choices.length === 0 && (
          <p>
            Approve initial objectives and requirements before adding a
            requirement.
          </p>
        )}
        <form
          onSubmit={(event) => {
            event.preventDefault();
            void act("/requirements", {
              statement,
              rationale,
              source,
              level,
              priority,
              verification_method: method,
              parent_ids: parents,
            });
          }}
        >
          <fieldset
            disabled={
              busy ||
              !!model.baseline ||
              !!model.archived ||
              choices.length === 0
            }
          >
            <legend>New requirement draft</legend>
            <label>
              New requirement statement
              <textarea
                required
                minLength={3}
                maxLength={2000}
                value={statement}
                onChange={(e) => setStatement(e.target.value)}
              />
            </label>
            <label>
              Requirement rationale
              <textarea
                required
                minLength={3}
                maxLength={2000}
                value={rationale}
                onChange={(e) => setRationale(e.target.value)}
              />
            </label>
            <label>
              Requirement source
              <textarea
                required
                minLength={3}
                maxLength={2000}
                value={source}
                onChange={(e) => setSource(e.target.value)}
              />
            </label>
            <p>
              The source is an owner declaration, not independently verified
              evidence.
            </p>
            <label>
              New requirement level
              <select value={level} onChange={(e) => setLevel(e.target.value)}>
                <option value="stakeholder">Stakeholder</option>
                <option value="system">System</option>
                <option value="subsystem">Subsystem</option>
              </select>
            </label>
            <label>
              New requirement priority
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value)}
              >
                <option value="must">Must</option>
                <option value="should">Should</option>
                <option value="could">Could</option>
              </select>
            </label>
            <label>
              Planned verification method
              <select
                value={method}
                onChange={(e) => setMethod(e.target.value)}
              >
                {[
                  "review",
                  "analysis",
                  "test",
                  "inspection",
                  "demonstration",
                ].map((value) => (
                  <option key={value} value={value}>
                    {value}
                  </option>
                ))}
              </select>
            </label>
            <fieldset>
              <legend>Originating objectives or parent requirements</legend>
              {choices.map((e) => (
                <label className="check" key={e.id}>
                  <input
                    type="checkbox"
                    checked={parents.includes(e.id)}
                    onChange={(event) =>
                      setParents(
                        event.target.checked
                          ? [...parents, e.id]
                          : parents.filter((id) => id !== e.id),
                      )
                    }
                  />
                  {e.id} — {e.title}
                </label>
              ))}
            </fieldset>
            <p>
              Approval requires fresh calculation and concept selection where
              analyses exist. It does not establish verification or
              completeness.
            </p>
            <button
              disabled={
                parents.length === 0 ||
                parents.length > 20 ||
                [statement, rationale, source].some(
                  (value) => value.trim().length < 3,
                )
              }
            >
              Propose new requirement for approval
            </button>
          </fieldset>
        </form>
      </details>
    </section>
  );
}
