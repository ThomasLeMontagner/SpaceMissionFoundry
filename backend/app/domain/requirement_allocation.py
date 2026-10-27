"""Explicit requirement responsibility links, never satisfaction evidence."""


def allocation_ids(entity):
    return {r.target for r in entity.relations if r.type == "allocated_to"}


def validate_allocations(model, proposal):
    proposed = {op.entity.id: op.entity for op in proposal.operations}
    graph = {**model.entities, **proposed}
    for op in proposal.operations:
        requirement = op.entity
        if requirement.kind != "Requirement":
            continue
        targets = allocation_ids(requirement)
        old = model.entities.get(requirement.id)
        if old and targets == allocation_ids(old):
            continue
        if len(targets) > 20:
            raise ValueError("A requirement may have at most twenty allocation targets")
        for key in targets:
            target = graph.get(key)
            if not target or target.kind not in {"Function", "Component"}:
                raise ValueError(
                    "Allocate requirements only to functions or components in this mission"
                )
            states = {"accepted", "stale", "proposed"} if key in proposed else {"accepted", "stale"}
            if target.state not in states:
                raise ValueError("Allocation targets must be active accepted or stale records")
        if old and (requirement.data.get("formalization") or {}).get("coverage") != "partial":
            raise ValueError("Changed allocations require renewed partial scope assessment")
