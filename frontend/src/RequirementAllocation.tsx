import { useState } from "react";
import type { Model } from "./types";

export default function RequirementAllocation({
  model,
  requirementId,
  busy,
  act,
  onSelect,
}: {
  model: Model;
  requirementId: string;
  busy: boolean;
  act: (path: string, body?: any) => Promise<void>;
  onSelect: (id: string) => void;
}) {
  const requirement = model.entities[requirementId];
  const current = (requirement.relations || [])
    .filter((r) => r.type === "allocated_to")
    .map((r) => r.target);
  const [selected, setSelected] = useState(current);
  const [reason, setReason] = useState("");
  const [targetId, setTargetId] = useState(current[0] || "");
  const targets = Object.values(model.entities).filter(
    (e) =>
      ["Function", "Component"].includes(e.kind) &&
      ["accepted", "stale"].includes(e.state),
  );
  const ids = [...new Set([...current, ...targets.map((e) => e.id)])];
  const target = model.entities[targetId];
  const incoming = Object.values(model.entities).filter(
    (e) =>
      e.kind === "Requirement" &&
      ["accepted", "stale"].includes(e.state) &&
      (e.relations || []).some(
        (r) => r.type === "allocated_to" && r.target === targetId,
      ),
  );
  const changed =
    [...selected].sort().join("\n") !== [...current].sort().join("\n");
  const name = (id: string) =>
    `${id} — ${model.entities[id]?.title || "Missing record"}`;
  return (
    <section aria-label="Requirement responsibility allocation">
      <details>
        <summary>Allocate responsibility</summary>
        <p>
          Assign responsibility to functions or components. These links do not
          prove satisfaction or verification. Reference architecture records are
          shared across candidates; no candidate-specific allocation is
          inferred.
        </p>
        <p>Current allocations: {current.map(name).join("; ") || "None"}</p>
        {targets.length === 0 && (
          <p>
            Approve architecture functions and components before adding
            allocations.
          </p>
        )}
        <form
          onSubmit={(event) => {
            event.preventDefault();
            void act(`/objects/${requirementId}/edit`, {
              changes: { allocation_ids: selected },
              reason,
            });
          }}
        >
          <fieldset disabled={busy || !!model.baseline || !!model.archived}>
            <legend>Propose responsibility assignments</legend>
            {ids.map((id) => (
              <label key={id} className="check">
                <input
                  type="checkbox"
                  checked={selected.includes(id)}
                  onChange={(event) =>
                    setSelected(
                      event.target.checked
                        ? [...selected, id]
                        : selected.filter((key) => key !== id),
                    )
                  }
                />
                {name(id)}
                {!targets.some((e) => e.id === id)
                  ? " (invalid target; remove to repair)"
                  : model.entities[id].state === "stale"
                    ? " (needs impact review)"
                    : ""}
              </label>
            ))}
            <p>
              Proposed allocations:{" "}
              {selected.map(name).join("; ") ||
                "None — removes current assignments"}
            </p>
            <label>
              Allocation change rationale
              <textarea
                required
                minLength={3}
                maxLength={2000}
                value={reason}
                onChange={(event) => setReason(event.target.value)}
              />
            </label>
            <p>
              Approval resets criterion coverage to partial and may require
              impact review and recalculation. Existing parent links and
              provenance remain intact.
            </p>
            <button
              disabled={
                !changed || selected.length > 20 || reason.trim().length < 3
              }
            >
              Propose allocations for approval
            </button>
          </fieldset>
        </form>
        <label>
          Inspect allocation target
          <select
            value={targetId}
            onChange={(event) => setTargetId(event.target.value)}
          >
            <option value="">Choose a function or component</option>
            {ids.map((id) => (
              <option key={id} value={id}>
                {name(id)}
              </option>
            ))}
          </select>
        </label>
        {target && (
          <article>
            <h4>{target.title}</h4>
            <p>
              {target.kind} · {target.state} · owner {target.owner} · revision{" "}
              {target.revision}
            </p>
            <h4>Requirements allocated to this target</h4>
            {incoming.length === 0 ? (
              <p>No active requirement is explicitly allocated here.</p>
            ) : (
              <ul>
                {incoming.map((e) => (
                  <li key={e.id}>
                    <button onClick={() => onSelect(e.id)}>{e.title}</button>
                  </li>
                ))}
              </ul>
            )}
          </article>
        )}
      </details>
    </section>
  );
}
