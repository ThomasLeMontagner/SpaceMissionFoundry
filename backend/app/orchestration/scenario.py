from app.domain.models import Entity, Relation

BRIEF = "Design a 12U CubeSat mission that detects and monitors wildfires over southern Europe. Deliver useful imagery within 30 minutes of acquisition, operate for at least two years, use a rideshare launch, and remain within a €12 million programme budget."


def entity(id, kind, title, owner="systems", refs=(), classification="Explicit assumption", **data):
    return Entity(
        id=id,
        kind=kind,
        title=title,
        owner=owner,
        classification=classification,
        relations=[Relation(type="depends_on", target=r) for r in refs],
        data=data,
    )


def assumptions():
    rows = [
        (
            "scope",
            "Reference scenario applies: 12U, southern Europe, 30 minutes, two years, rideshare, €12M",
            "Confirm these constraints against the supplied brief; custom missions need edited requirements.",
        ),
        (
            "observation",
            "Thermal anomalies and contextual images; assumed 100 m sampling and 100 km swath",
            "Validate detection sensitivity, geolocation, cloud effects and user needs with a payload study.",
        ),
        (
            "orbit-assumption",
            "Assume circular 550 km LEO; access windows and revisit remain unknown",
            "Propagate actual orbit and ground stations before a preliminary design review.",
        ),
        (
            "operations",
            "Assume 40 minutes of usable ground contact daily; this does not prove 30-minute delivery",
            "Simulate worst-case acquisition-to-user latency with actual station access and processing.",
        ),
        (
            "resources",
            "Resource inputs are concept estimates with 20% mass contingency and 60% battery depth of discharge",
            "Replace with qualified supplier and environmental evidence.",
        ),
    ]
    return [
        entity(
            id,
            "Assumption",
            title,
            "science",
            rationale="Incomplete brief requires a declared sizing basis",
            impact="May invalidate payload, orbit or mission feasibility",
            confidence=0.4,
            validation_plan=plan,
        )
        for id, title, plan in rows
    ]


def requirements():
    objective = entity(
        "objective",
        "Objective",
        "Detect and monitor wildfires over southern Europe",
        "science",
        refs=["scope"],
        stakeholder="Civil protection and wildfire monitoring teams",
        priority="must",
        measure_of_success="Useful thermal anomalies and contextual imagery",
    )
    rows = [
        (
            "req-observe",
            "The mission shall acquire wildfire monitoring imagery over southern Europe.",
            "stakeholder",
            "demonstration",
        ),
        (
            "req-latency",
            "The ground segment shall deliver useful imagery within 30 minutes of acquisition.",
            "system",
            "analysis",
        ),
        (
            "req-life",
            "The spacecraft shall support operations for at least two years.",
            "system",
            "analysis",
        ),
        (
            "req-launch",
            "The spacecraft shall fit a 12U rideshare deployer envelope.",
            "system",
            "inspection",
        ),
        ("req-cost", "The programme shall remain within €12 million.", "stakeholder", "review"),
    ]
    result = [objective]
    for id, title, level, method in rows:
        e = entity(
            id,
            "Requirement",
            title,
            "science",
            rationale="Derived from the mission owner brief and approved scope",
            source="Mission brief / scope assumption",
            level=level,
            priority="must",
            verification_method=method,
        )
        e.relations = [Relation(type="derives_from", target="objective")]
        result.append(e)
    return result


def architectures():
    return [
        entity(
            "wide",
            "ArchitectureAlternative",
            "A · Wide-area continuous imaging",
            refs=["req-observe", "resources"],
            benefits=["More contextual imagery"],
            disadvantages=["Data volume exceeds S-band downlink"],
            risks=["Contact assumptions", "Payload sensitivity unverified"],
            conops="Acquire thermal strips and store complete imagery; daily S-band ground delivery.",
            payload="Thermal imager with contextual channel; 5% observation duty cycle",
            ground="Single-network S-band contacts",
            cost_estimate_eur=10500000,
            cost_basis="Explicit programme estimate, not a quotation",
        ),
        entity(
            "selective",
            "ArchitectureAlternative",
            "B · Event-selective imaging + X-band",
            refs=["req-observe", "resources"],
            benefits=["Lower data demand", "Higher downlink capacity"],
            disadvantages=[
                "Onboard filtering can miss weak anomalies",
                "Larger ground antenna dependency",
            ],
            risks=["False negatives", "Unverified latency and revisit"],
            conops="Observe targeted strips, filter events onboard, retain context, downlink via X-band; S-band for TT&C.",
            payload="Thermal imager with event filtering; 2% observation duty cycle",
            ground="Scheduled X-band network",
            cost_estimate_eur=11500000,
            cost_basis="Explicit programme estimate, not a quotation",
        ),
        entity(
            "detect",
            "Function",
            "Detect, locate and prioritize thermal anomalies",
            refs=["req-observe"],
            inputs=["Thermal radiance"],
            outputs=["Geolocated events"],
            performance="Sensitivity unknown",
            allocated_element="imager",
        ),
        entity(
            "deliver",
            "Function",
            "Store and deliver imagery to mission users",
            refs=["req-latency"],
            inputs=["Image products"],
            outputs=["Ground products"],
            performance="30 minutes required; unverified",
            allocated_element="bus-component",
        ),
        entity(
            "imager",
            "Component",
            "Thermal payload",
            refs=["detect"],
            type="payload",
            parent="spacecraft",
            pointing="Ground-target tracking; accuracy TBD",
            calibration="Onboard reference and vicarious calibration; validation pending",
            maturity="concept",
        ),
        entity(
            "bus-component",
            "Component",
            "12U platform and ground service",
            refs=["deliver"],
            type="platform",
            parent="spacecraft",
            aocs="Three-axis stabilized; pointing budget TBD",
            thermal="Passive concept; thermal balance unverified",
            obc="Event filtering and solid-state storage",
            maturity="concept",
        ),
        entity(
            "interface",
            "Interface",
            "Payload → onboard data handling",
            refs=["imager", "bus-component"],
            endpoints=["imager", "bus-component"],
            exchanges=["Image packets", "Time tags"],
            direction="payload to bus",
            medium="SpaceWire assumed",
            constraints=["Peak input rate 20 Mbit/s; verify hardware compatibility"],
        ),
        entity(
            "mission-risk",
            "Risk",
            "Latency, coverage, lifetime and cost remain unverified",
            refs=["req-latency", "req-life", "req-cost"],
            cause="Concept inputs lack detailed orbit, environmental and supplier analysis",
            event="Mission cannot satisfy user constraints",
            consequence="Concept redesign",
            likelihood="medium",
            severity="high",
            mitigation="Complete access, radiation, reliability and cost studies",
            residual_risk="open",
        ),
    ]


def Q(v, u):
    return {"value": v, "unit": u}


def inputs(candidate, orbital):
    selective = candidate == "selective"
    return {
        "mass": {
            "entries": [
                {"name": n, "mass": Q(v, "kg")}
                for n, v in [
                    ("Payload", 3),
                    ("Structure", 2),
                    ("Power", 2.5),
                    ("Avionics/AOCS", 2),
                    ("Communications", 1.5 if selective else 1),
                ]
            ],
            "margin": Q(0.2, ""),
            "limit": Q(20, "kg"),
        },
        "power": {
            "modes": [
                {
                    "name": "observe",
                    "fraction": Q(0.2, ""),
                    "loads": {"payload": Q(20, "W"), "bus": Q(10, "W")},
                },
                {"name": "standby", "fraction": Q(0.8, ""), "loads": {"bus": Q(10, "W")}},
            ],
            "period": orbital["period"],
            "eclipse": orbital["eclipse"],
            "solar": Q(45, "W"),
            "battery": Q(40, "Wh"),
            "depth_of_discharge": Q(0.6, ""),
            "eclipse_load": Q(14, "W"),
        },
        "data": {
            "rate": Q(20, "Mbit/s"),
            "duty": Q(0.02 if selective else 0.05, ""),
            "compression": Q(4 if selective else 2, ""),
            "storage": Q(32, "Gbyte"),
        },
        "link": {
            "frequency": Q(8.2 if selective else 2.2, "GHz"),
            "range": Q(1500, "km"),
            "rate": Q(10 if selective else 1, "Mbit/s"),
            "tx_power": Q(5, "W"),
            "tx_gain_db": Q(8 if selective else 3, ""),
            "rx_gain_db": Q(42 if selective else 30, ""),
            "loss_db": Q(3, ""),
            "required_ebn0_db": Q(5, ""),
            "noise_temperature": Q(300, "K"),
            "contact": Q(40, "minute"),
            "efficiency": Q(0.7, ""),
        },
    }
