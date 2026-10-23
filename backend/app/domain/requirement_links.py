"""Validate changed requirement derivations against the whole proposed graph."""


def parent_ids(entity):
    return {r.target for r in entity.relations if r.type == "derives_from"}


def validate_links(model, proposal):
    replacements = {op.entity.id: op.entity for op in proposal.operations}
    graph = {**model.entities, **replacements}
    for op in proposal.operations:
        e = op.entity
        if e.kind != "Requirement":
            continue
        old = model.entities.get(e.id)
        parents = parent_ids(e)
        if old and parents == parent_ids(old):
            continue  # Unrelated edits do not prevent repairing legacy models in stages.
        if not parents:
            raise ValueError("Choose at least one parent requirement or objective")
        for target in parents:
            parent = graph.get(target)
            if not parent or parent.kind not in {"Requirement", "Objective"}:
                raise ValueError("Parents must be requirements or objectives in this mission")
            if target not in replacements and parent.state not in {"accepted", "stale"}:
                raise ValueError("Parents must be accepted or stale")
            if target in replacements and parent.state not in {"proposed", "accepted", "stale"}:
                raise ValueError("Proposed parents must remain active")
        # Reject reachable cycles too: attaching a child to an existing cycle is unsafe.
        visiting, done = set(), set()
        stack = [(e.id, False)]
        while stack:
            key, leaving = stack.pop()
            if leaving:
                visiting.remove(key)
                done.add(key)
                continue
            if key in visiting:
                raise ValueError("Parent links would introduce or depend on a circular derivation")
            if key in done:
                continue
            visiting.add(key)
            stack.append((key, True))
            node = graph.get(key)
            if node and node.kind == "Requirement":
                stack.extend((p, False) for p in parent_ids(node) if p in graph)
        if old:
            scope = e.data.get("formalization") or {}
            if scope.get("coverage") != "partial":
                raise ValueError("Changed parent links require renewed partial scope assessment")
