"""Deterministic checks of explicitly declared point-to-point data contracts."""

from app.domain.interfaces import DataContract
from app.domain.models import Relation
from app.engineering_tools.calculations import q
from app.orchestration.scenario import entity


def evaluate(model, interface):
    checks = []
    refs = [Relation(type="depends_on", target=interface.id)]
    endpoints = interface.data.get("endpoints", [])

    def add(key, status, reason, **evidence):
        checks.append(dict(check=key, status=status, reason=reason, **evidence))

    if len(endpoints) != 2 or len(set(endpoints)) != 2:
        add("endpoints", "fail", "A point-to-point data interface requires two distinct endpoints.")
    else:
        missing = [
            key
            for key in endpoints
            if key not in model.entities or model.entities[key].kind != "Component"
        ]
        add(
            "endpoints",
            "fail" if missing else "pass",
            "Endpoints must resolve to physical Component objects.",
            invalid_endpoints=missing,
        )
    for key in endpoints:
        if key in model.entities:
            refs.append(Relation(type="depends_on", target=key))
    stale = interface.state == "stale" or any(
        model.entities[key].state == "stale" for key in endpoints if key in model.entities
    )
    accepted = interface.state == "accepted" and all(
        model.entities[key].state == "accepted" for key in endpoints if key in model.entities
    )
    raw = interface.data.get("data_contract")
    if not raw:
        add(
            "contract",
            "unverified",
            "No approved structured data contract; descriptive text is not calculation evidence.",
        )
    else:
        try:
            contract = DataContract.model_validate(raw)
            add(
                "direction",
                "pass"
                if contract.source_endpoint != contract.sink_endpoint
                and {contract.source_endpoint, contract.sink_endpoint} == set(endpoints)
                and len(endpoints) == 2
                else "fail",
                "Sender and receiver must be distinct declared interface endpoints.",
                source=contract.source_endpoint,
                sink=contract.sink_endpoint,
            )
            protocols = [
                (value or "").strip().casefold()
                for value in [contract.source_protocol, contract.sink_protocol]
            ]
            add(
                "protocol",
                "unverified"
                if not all(protocols)
                else "pass"
                if protocols[0] == protocols[1]
                else "fail",
                "Exact declared protocol names must agree; matching names do not certify physical implementation.",
                source_protocol=contract.source_protocol,
                sink_protocol=contract.sink_protocol,
            )
            if contract.source_rate is None or contract.sink_capacity is None:
                add(
                    "rate",
                    "unverified",
                    "Sender peak rate and receiver capacity are both required.",
                )
            else:
                source = q(contract.source_rate.model_dump(), "bit/s")
                capacity = q(contract.sink_capacity.model_dump(), "bit/s")
                add(
                    "rate",
                    "pass" if source <= capacity else "fail",
                    "Declared sender peak rate must not exceed receiver capacity.",
                    source_rate=contract.source_rate.model_dump(),
                    sink_capacity=contract.sink_capacity.model_dump(),
                    margin_bits_per_second=capacity - source,
                )
        except ValueError as exc:
            add("contract", "unverified", f"Invalid structured contract: {exc}")
    status = (
        "stale"
        if stale
        else "unverified"
        if not accepted
        else "fail"
        if any(c["status"] == "fail" for c in checks)
        else "unverified"
        if any(c["status"] == "unverified" for c in checks)
        else "pass"
    )
    result = entity(
        f"interface-check-{interface.id}",
        "VerificationItem",
        f"Interface consistency · {interface.title}",
        "tool",
        classification="Deterministic calculation" if status in ["pass", "fail"] else "Unknown",
        check_type="interface_consistency",
        interface=interface.id,
        status=status,
        checks=checks,
        tool="data-interface-consistency",
        tool_version="1.0",
        source_revision=model.revision,
        interface_revision=interface.revision,
        inputs=dict(endpoints=endpoints, data_contract=raw),
        endpoint_evidence=[
            dict(
                id=key,
                kind=model.entities[key].kind,
                state=model.entities[key].state,
                revision=model.entities[key].revision,
            )
            for key in endpoints
            if key in model.entities
        ],
        limitations=[
            "Checks only declared point-to-point data contracts shared by both reference candidates.",
            "Protocol name equality and peak-rate allocation do not verify electrical signaling, connectors, timing, packet formats, power, thermal or mechanical compatibility.",
            "Interface rates are separate approved assumptions; payload/link budgets and narrative direction/medium text are not inferred or synchronized automatically.",
        ],
    )
    result.relations = list({(r.type, r.target): r for r in refs}.values())
    if stale:
        result.state = "stale"
    return result


def refresh_interfaces(model):
    for interface in list(model.entities.values()):
        if interface.kind == "Interface":
            check = evaluate(model, interface)
            model.entities[check.id] = check


def guard_interfaces(model):
    for interface in model.entities.values():
        if interface.kind == "Interface":
            check = evaluate(model, interface)
            if check.data["status"] in ["fail", "stale"]:
                raise ValueError(
                    f"Interface {interface.id} is {check.data['status']}; review its contract and recalculate"
                )
