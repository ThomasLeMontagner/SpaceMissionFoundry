import { useState } from "react";
import type { Model } from "./types";

export default function RequirementLinks({
  model,
  requirementId,
  busy,
  act,
}: {
  model: Model;
  requirementId: string;
  busy: boolean;
  act: (path: string, body?: any) => Promise<void>;
}) {
  const requirement = model.entities[requirementId];
  const current = (requirement.relations || [])
    .filter((r) => r.type === "derives_from")
    .map((r) => r.target);
  const [selected, setSelected] = useState(current);
  const [reason, setReason] = useState("");
  const choices = Object.values(model.entities).filter(
    (e) =>
      e.id !== requirementId &&
      ["Requirement", "Objective"].includes(e.kind) &&
      ["accepted", "stale"].includes(e.state),
  );
  const ids = [...new Set([...current, ...choices.map((e) => e.id)])];
  const changed =
    [...selected].sort().join("\n") !== [...current].sort().join("\n");
  const label = (id: string) =>
    `${id} — ${model.entities[id]?.title || "Missing record"}`;
  return (
    <form
      aria-label="Edit requirement parent links"
      onSubmit={(event) => {
        event.preventDefault();
        void act(`/objects/${requirementId}/edit`, {
          changes: { parent_ids: selected },
          reason,
        });
      }}
    >
      <fieldset disabled={busy || !!model.baseline || !!model.archived}>
        <legend>Review parent links</legend>
        <p>
          Select the originating objectives or parent requirements. Approval
          preserves other relations, resets criterion coverage to partial and
          invalidates dependent evidence for review and recalculation. Circular
          links are rejected.
        </p>
        {ids.map((id) => (
          <label key={id} className="check">
            <input
              type="checkbox"
              checked={selected.includes(id)}
              onChange={(event) =>
                setSelected(
                  event.target.checked
                    ? [...selected, id]
                    : selected.filter((value) => value !== id),
                )
              }
            />
            {label(id)}
            {!choices.some((e) => e.id === id) &&
              " (invalid parent; remove to repair)"}
          </label>
        ))}
        <p>Current parents: {current.map(label).join("; ") || "None"}</p>
        <p>
          Proposed parents:{" "}
          {selected.map(label).join("; ") || "None — choose at least one"}
        </p>
        <label>
          Parent-link change rationale
          <textarea
            required
            minLength={3}
            maxLength={2000}
            value={reason}
            onChange={(event) => setReason(event.target.value)}
          />
        </label>
        <button
          disabled={
            !changed ||
            selected.length === 0 ||
            selected.length > 20 ||
            reason.trim().length < 3
          }
        >
          Propose parent links for approval
        </button>
      </fieldset>
    </form>
  );
}
