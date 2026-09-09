"""Deterministic acceptance fixture. Human actions are simulated explicitly, never production defaults."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from app.persistence.store import Store
from app.services.workflow import Workflow
from app.orchestration.scenario import BRIEF
from app.reports.export import report

output = Path(__file__).parent / "output"
output.mkdir(exist_ok=True)
with TemporaryDirectory() as temp:
    store = Store("sqlite:///" + temp + "/scenario.db")
    store.initialize()
    workflow = Workflow(store)
    m = workflow.create("Pyra · Wildfire CubeSat", BRIEF)
    for stage in range(3):
        p = next(p for p in m.proposals.values() if p.status == "submitted")
        m = workflow.decide(
            m.id,
            p.id,
            "accept",
            "Simulated human acceptance for reproducible test fixture",
            m.revision,
        )
        m = workflow.advance(m.id, m.revision)
    m = workflow.select(
        m.id,
        m.revision,
        "selective",
        {"science": 0.35, "capacity": 0.45, "simplicity": 0.2},
        "Simulated human selection: positive capacity with acknowledged science dissent",
    )
    for _ in range(3):
        m = workflow.advance(m.id, m.revision)
    m = workflow.baseline(m.id, m.revision, "Reference conceptual baseline — test fixture", True)
    snapshot = store.baseline(m.id)
    (output / "mission-model.json").write_text(json.dumps(snapshot, indent=2))
    (output / "mission-concept.md").write_text(report(snapshot))
    (output / "events.json").write_text(json.dumps(store.history(m.id), indent=2))
    print(f"Baseline generated at revision {m.revision}: {output}")
