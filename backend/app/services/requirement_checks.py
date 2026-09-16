"""Requirement conclusions are computed from recorded evidence, never supplied by users."""

import math

from app.domain.models import Relation
from app.domain.requirement_checks import METRICS, Criterion
from app.engineering_tools.calculations import U, q
from app.orchestration.scenario import entity


def evaluate(model, requirement, candidate):
    criterion = requirement.data.get("criterion")
    data = dict(
        requirement=requirement.id,
        candidate=candidate,
        status="unverified",
        criterion=criterion,
        actual=None,
        evidence_revision=None,
        evaluated_revision=model.revision + 1,
        reason="No supported quantitative criterion; verification remains outstanding.",
    )
    refs = [Relation(type="verifies", target=requirement.id)]
    if criterion:
        rule = Criterion.model_validate(criterion)
        tool, output = rule.metric.split(".")
        source_id = f"{'mission' if tool in ['orbit', 'access'] else candidate}-{tool}-analysis"
        source = model.entities.get(source_id)
        if source:
            refs.append(Relation(type="evidenced_by", target=source_id))
            data["evidence_revision"] = source.revision
            data["analysis_source_revision"] = source.data.get("source_revision")
        if requirement.state == "stale" or (source and source.state == "stale"):
            data.update(status="stale", reason="Requirement or calculation evidence has changed.")
        elif requirement.state != "accepted" or not source or source.state != "accepted":
            data["reason"] = "Accepted requirement and current calculation evidence are required."
        elif source.data.get("status") != "valid":
            data["reason"] = "Calculation failed; no valid evidence is available."
        else:
            try:
                raw = source.data["outputs"][output]
                unit = METRICS[rule.metric]["unit"]
                value = U.Quantity(raw["value"], raw["unit"]).to(unit).magnitude
                if not math.isfinite(value):
                    raise ValueError("Non-finite evidence")
                limit = q(rule.threshold.model_dump(), unit)
                passed = value <= limit if rule.operator == "<=" else value >= limit
                data.update(
                    status="pass" if passed else "fail",
                    actual={"value": value, "unit": unit},
                    reason="Deterministic comparison; conditional on recorded concept assumptions.",
                )
            except Exception:
                data["reason"] = (
                    "Missing or incompatible calculation output; verification is outstanding."
                )
    elif requirement.state == "stale":
        data.update(status="stale", reason="Requirement has changed and needs review.")
    check = entity(
        f"check-{requirement.id}-{candidate}",
        "VerificationItem",
        f"{requirement.title} · {candidate}",
        "tool",
        classification="Deterministic calculation"
        if data["status"] in ["pass", "fail"]
        else "Unknown",
        **data,
    )
    check.relations = refs
    if data["status"] == "stale":
        check.state = "stale"
    return check


def refresh(model):
    requirements = [e for e in model.entities.values() if e.kind == "Requirement"]
    for requirement in requirements:
        for candidate in ("wide", "selective"):
            check = evaluate(model, requirement, candidate)
            model.entities[check.id] = check


def guard_candidate(model, candidate):
    for requirement in model.entities.values():
        if requirement.kind == "Requirement" and requirement.data.get("priority") == "must":
            check = evaluate(model, requirement, candidate)
            if check.data["status"] in ["fail", "stale"]:
                raise ValueError(f"Required criterion {requirement.id} is {check.data['status']}")
