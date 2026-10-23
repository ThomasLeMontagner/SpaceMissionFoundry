"""Read-only, deterministic advisory checks; never verification evidence."""

import re
from collections import defaultdict

from app.domain.formalization import Formalization
from app.domain.requirement_checks import Criterion

ACTIVE = {"accepted", "stale"}


def report(model):
    nodes = {
        e.id: e
        for e in model.entities.values()
        if e.kind in {"Requirement", "Objective"} and e.state in ACTIVE
    }
    requirements = {key: e for key, e in nodes.items() if e.kind == "Requirement"}
    findings = []

    def add(e, code, message, action, related=(), quote=None):
        findings.append(
            dict(
                id=f"{e.id}:{code}",
                requirement_id=e.id,
                code=code,
                title=e.title,
                message=message,
                action=action,
                related_ids=sorted(set(related)),
                source_quote=quote,
            )
        )

    parents = {}
    duplicates = defaultdict(list)
    for e in requirements.values():
        links = [r.target for r in e.relations if r.type == "derives_from"]
        parents[e.id] = [target for target in links if target in nodes]
        invalid = [target for target in links if target not in nodes]
        if invalid:
            add(
                e,
                "invalid_parent",
                "A parent link is missing, inactive or not a requirement/objective.",
                "Review the originating need and correct the derivation link.",
                invalid,
            )
        if not parents[e.id]:
            add(
                e,
                "orphan",
                "No active parent requirement or originating objective is linked.",
                "Identify the originating need and review its traceability link.",
            )
        normalized = " ".join(e.title.casefold().split()).rstrip(".!?")
        if normalized:
            duplicates[normalized].append(e.id)
        match = re.search(
            r"\b(tbd|tbc|appropriate|adequate|user[- ]friendly|as soon as possible|useful|fast|efficient)\b",
            e.title,
            re.I,
        )
        if match:
            add(
                e,
                "ambiguous_wording",
                "This wording may need an observable definition.",
                "Record a clarification defining the term, conditions and acceptance target.",
                quote=match[0],
            )
        match = re.search(r"\b(and|or)\b|;", e.title, re.I)
        if match:
            add(
                e,
                "possibly_compound",
                "The statement may contain multiple obligations or alternatives.",
                "Review whether separate child requirements are needed; conjunctions alone do not prove a defect.",
                quote=match[0],
            )
        raw = e.data.get("criterion")
        try:
            if raw is None:
                raise ValueError("missing")
            Criterion.model_validate(raw)
        except ValueError:
            add(
                e,
                "unsupported_verification",
                "No valid supported calculator criterion is recorded.",
                "Propose a supported criterion, or document the separate review/test needed; missing calculator support does not prove the requirement is unverifiable.",
            )
        scope = e.data.get("formalization")
        try:
            if scope is None:
                raise ValueError("unassessed")
            parsed = Formalization.model_validate(scope)
            rule = parsed.criterion.model_dump() if parsed.criterion else None
            if parsed.statement != e.title or rule != raw or parsed.coverage != "full":
                raise ValueError("partial or outdated")
        except ValueError:
            add(
                e,
                "unresolved_scope",
                "Criterion coverage is partial, unassessed or needs review.",
                "Resolve scope questions in Requirement readiness and submit any changes for approval.",
            )

    # Iterative reachability avoids recursion limits on long imported hierarchies.
    supported = set()
    for e in requirements.values():
        seen = set()
        pending = list(parents[e.id])
        while pending:
            target = pending.pop()
            if target in seen:
                continue
            seen.add(target)
            if nodes[target].kind == "Objective":
                supported.add(target)
            pending.extend(parents.get(target, []))
        if e.id in seen:
            add(
                e,
                "derivation_cycle",
                "This requirement is part of a circular derivation.",
                "Review parent links and remove the circular dependency through a reviewed correction.",
            )
    for ids in duplicates.values():
        if len(ids) > 1:
            for key in ids:
                add(
                    requirements[key],
                    "duplicate_statement",
                    "Another active requirement has the same normalized statement.",
                    "Compare applicability and sources before deciding whether these are duplicates.",
                    [i for i in ids if i != key],
                )
    for e in nodes.values():
        if e.kind == "Objective" and e.id not in supported:
            add(
                e,
                "unsupported_objective",
                "No active requirement traces to this objective.",
                "Identify supporting requirements and review their originating-need links.",
            )
    return dict(
        revision=model.revision,
        checked_requirements=len(requirements),
        findings=sorted(findings, key=lambda f: (f["requirement_id"], f["code"])),
        advisory=True,
    )
