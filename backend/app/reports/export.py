import csv
import io
import json

from app.domain.models import now


def report(model):
    lines = [
        f"# {model['name']} — Mission concept report",
        "",
        f"Baseline: {model['baseline']} · Model revision: {model['revision']}",
        f"Generated: {now()}",
        "",
        "## Scope",
        model["brief"],
        "",
        "**Conceptual study only. Latency, coverage, detection performance, lifetime and programme cost remain unverified.**",
        "",
        "## Selected concept",
        str(model["selected"]),
        "",
    ]
    groups = [
        "Objective",
        "Requirement",
        "ArchitectureAlternative",
        "Function",
        "Component",
        "Interface",
        "Budget",
        "Claim",
        "Evidence",
        "Parameter",
        "AnalysisRun",
        "Assumption",
        "TradeStudy",
        "Risk",
        "ReviewFinding",
        "VerificationItem",
        "Decision",
    ]
    for kind in groups:
        lines.extend([f"## {kind}", ""])
        for e in model["entities"].values():
            if e["kind"] == kind:
                lines.extend(
                    [
                        f"### {e['id']}: {e['title']}",
                        f"{e['classification']} · {e['state']} · Owner: {e['owner']}",
                        "```json",
                        json.dumps(e["data"], indent=2, ensure_ascii=False),
                        "```",
                        "Traceability: "
                        + ", ".join(f"{r['type']} → {r['target']}" for r in e["relations"]),
                        "",
                    ]
                )
    lines.extend(
        [
            "## Traceability summary",
            f"{sum(len(e['relations']) for e in model['entities'].values())} typed relationships.",
            "Calculated budgets link to versioned tool executions. Requirements trace to the mission objective.",
        ]
    )
    return "\n".join(lines)


def csv_export(model):
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(
        ["id", "type", "title", "state", "classification", "owner", "revision", "data", "relations"]
    )
    for e in model["entities"].values():
        row = [
            e[k] for k in ["id", "kind", "title", "state", "classification", "owner", "revision"]
        ]
        # Prevent spreadsheet formula interpretation when users open imported text.
        writer.writerow(
            ["'" + str(v) if str(v).startswith(("=", "+", "-", "@")) else v for v in row]
            + [json.dumps(e["data"]), json.dumps(e["relations"])]
        )
    return out.getvalue()
