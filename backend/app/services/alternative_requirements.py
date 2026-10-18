"""Candidate-local exploratory checks; never overwrite accepted verification evidence."""

from types import SimpleNamespace

from app.domain.models import Entity
from app.engineering_tools.calculations import execute
from app.orchestration.scenario import entity
from app.services import requirement_checks


def geometry(data, count):
    orbit = execute("orbit", data["inputs"]["orbit"], data["source_revision"])
    access = execute(
        "access",
        {**data["inputs"].get("access", {}), "altitude": data["inputs"]["orbit"]["altitude"]},
        data["source_revision"],
    )
    products = sum(len(t["windows"]) for t in access["outputs"].get("targets", []))
    if products * count > 3000:
        access.update(
            status="invalid",
            outputs={},
            errors=["Study exceeds 3,000 product cases per stage; shorten the access horizon."],
        )
    return dict(orbit=orbit, access=access)


def evaluate(data, option_inputs, row, shared):
    access = shared["access"]
    outputs = access["outputs"] if access["status"] == "valid" else {}
    delivery = execute(
        "delivery",
        dict(
            delays=data["inputs"].get("delivery", {}),
            payload=option_inputs,
            link=data["inputs"]["link"],
            link_result=row["link"]["outputs"],
            access={
                k: outputs[k]
                for k in ["horizon", "targets", "network_windows", "sample_step"]
                if k in outputs
            },
        ),
        data["source_revision"],
    )
    # Only freshly evaluated option evidence is available. No accepted source analyses
    # can accidentally satisfy a requirement about this proposed configuration.
    model = SimpleNamespace(revision=data["source_revision"], entities={})
    for tool, result in {
        **shared,
        **{k: row[k] for k in ["data", "link", "mass", "power"] if k in row},
        "delivery": delivery,
    }.items():
        ident = f"{'mission' if tool in ['access', 'orbit'] else data['candidate']}-{tool}-analysis"
        source = entity(ident, "AnalysisRun", tool, "tool", **result)
        source.revision = data["source_revision"]
        model.entities[ident] = source
    checks = []
    for raw in data["requirements"]:
        requirement = Entity.model_validate(raw)
        try:
            check = requirement_checks.evaluate(model, requirement, data["candidate"]).data
        except ValueError:
            check = dict(
                status="unverified",
                reason="Unsupported or malformed quantitative criterion",
                actual=None,
                criterion=requirement.data.get("criterion"),
            )
        check.update(
            requirement=requirement.id,
            title=requirement.title,
            priority=requirement.data.get("priority"),
            evaluated_revision=data["source_revision"],
            scope="proposed alternative",
        )
        checks.append(check)
    blockers = list(data.get("requirement_input_blockers", []))
    for tool, result in [("access", access), ("delivery", delivery)]:
        if result["status"] != "valid":
            blockers.append(
                f"{tool.capitalize()} evidence unavailable: " + "; ".join(result["errors"])
            )
    mandatory = [c for c in checks if c["priority"] == "must"]
    if not mandatory:
        blockers.append("No accepted mandatory requirements are available for this study")
    blockers += [
        f"Requirement {c['requirement']}: {c['status']} — {c['reason']}"
        for c in mandatory
        if c["status"] != "pass"
    ]
    return dict(
        requirement_checks=checks,
        delivery=delivery,
        requirement_blockers=blockers,
        requirements_eligible=not blockers,
    )


def summary(row):
    """Bound provider context without hiding failed/unknown checks or their basis."""
    return dict(
        id=row["id"],
        eligible=row["eligible"],
        blockers=row.get("blockers", []),
        checks=[
            {
                k: check.get(k)
                for k in ["requirement", "priority", "status", "criterion", "actual", "reason"]
            }
            for check in row.get("requirement_checks", [])
        ],
        delivery={
            k: v
            for k, v in row.get("delivery", {}).get("outputs", {}).items()
            if k not in ["observations", "limitations"]
        },
    )
