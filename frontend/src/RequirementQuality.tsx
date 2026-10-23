import { useState } from "react";

type Finding = {
  id: string;
  requirement_id: string;
  code: string;
  title: string;
  message: string;
  action: string;
  related_ids: string[];
  source_quote: string | null;
};
export default function RequirementQuality({
  report,
  onSelect,
  requirementIds,
}: {
  report: {
    revision: number;
    checked_requirements: number;
    findings: Finding[];
  };
  onSelect: (id: string) => void;
  requirementIds: string[];
}) {
  const [filter, setFilter] = useState("all");
  const codes = [...new Set(report.findings.map((f) => f.code))].sort();
  const effectiveFilter = codes.includes(filter) ? filter : "all";
  const findings = report.findings.filter(
    (f) => effectiveFilter === "all" || f.code === effectiveFilter,
  );
  return (
    <section aria-label="Requirement quality checks">
      <h3>Requirement quality and traceability</h3>
      <p>
        {report.findings.length} advisory findings across{" "}
        {report.checked_requirements} requirements at revision {report.revision}
        .
      </p>
      <p>
        These deterministic checks suggest review actions. They do not establish
        completeness, semantic consistency or verification, and never change
        approval status. Wording checks can produce false positives.
      </p>
      <label>
        Quality finding type
        <select
          value={codes.includes(filter) ? filter : "all"}
          onChange={(e) => setFilter(e.target.value)}
        >
          <option value="all">All findings</option>
          {codes.map((code) => (
            <option key={code} value={code}>
              {code.replaceAll("_", " ")}
            </option>
          ))}
        </select>
      </label>
      {findings.length === 0 && (
        <p>
          No matching findings. This is not proof that all requirements are
          complete or correct.
        </p>
      )}
      {findings.map((f) => (
        <article key={f.id}>
          <h4>
            {f.title} — {f.code.replaceAll("_", " ")}
          </h4>
          <p>
            {f.message}{" "}
            {f.source_quote && <>Flagged text: “{f.source_quote}”.</>}
          </p>
          <p>{f.action}</p>
          {requirementIds.includes(f.requirement_id) && (
            <button onClick={() => onSelect(f.requirement_id)}>
              Review {f.requirement_id}
            </button>
          )}
          {f.related_ids.length > 0 && (
            <p>
              Related records:{" "}
              {f.related_ids.map((id) =>
                requirementIds.includes(id) ? (
                  <button key={id} onClick={() => onSelect(id)}>
                    {id}
                  </button>
                ) : (
                  <span key={id}>{id} </span>
                ),
              )}
            </p>
          )}
        </article>
      ))}
    </section>
  );
}
