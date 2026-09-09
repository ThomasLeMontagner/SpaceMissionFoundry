import pytest

from app.engineering_tools.calculations import execute
from app.orchestration.scenario import Q, inputs


def test_known_mass_and_unit_conversion():
    values = {
        "entries": [{"name": "a", "mass": Q(1000, "g")}, {"name": "b", "mass": Q(2, "kg")}],
        "margin": Q(0.2, ""),
        "limit": Q(4, "kg"),
    }
    r = execute("mass", values, 7)
    assert r["outputs"]["total"] == Q(3.6, "kg")
    assert r["outputs"]["margin"] == Q(0.4, "kg")
    assert r["source_revision"] == 7
    assert execute("mass", values, 7)["outputs"] == r["outputs"]


def test_known_data():
    r = execute(
        "data",
        {
            "rate": Q(1, "Mbit/s"),
            "duty": Q(0.1, ""),
            "compression": Q(2, ""),
            "storage": Q(1, "Gbyte"),
        },
        0,
    )
    assert r["outputs"]["daily"] == Q(4.32e9, "bit")
    assert r["outputs"]["compliant"]


def test_known_power():
    r = execute(
        "power",
        {
            "modes": [{"fraction": Q(1, ""), "loads": {"bus": Q(10, "W")}}],
            "period": Q(90, "minute"),
            "eclipse": Q(30, "minute"),
            "solar": Q(20, "W"),
            "battery": Q(20, "Wh"),
            "depth_of_discharge": Q(0.5, ""),
            "eclipse_load": Q(10, "W"),
        },
        0,
    )
    assert r["outputs"]["margin"] == Q(5, "Wh")
    assert r["outputs"]["battery_margin"] == Q(5, "Wh")


def test_link_physics_capacity_and_conflict():
    orbit = execute("orbit", {"altitude": Q(550, "km")}, 0)["outputs"]
    assert 5600 < orbit["period"]["value"] < 5800
    for candidate, compliant in [("wide", False), ("selective", True)]:
        i = inputs(candidate, orbit)
        i["link"]["demand"] = execute("data", i["data"], 0)["outputs"]["daily"]
        result = execute("link", i["link"], 0)["outputs"]
        assert result["compliant"] is compliant
        assert result["link_margin_db"]["value"] > 0
        assert result["capacity"]["value"] == pytest.approx(16.8e9 if compliant else 1.68e9)
    assert result["fspl_db"]["value"] == pytest.approx(174.246, abs=0.02)


@pytest.mark.parametrize(
    "tool,values",
    [
        ("mass", {}),
        ("data", {"rate": Q(1, "kg")}),
        ("orbit", {"altitude": Q(-5, "km")}),
        ("trade", {"weights": {"a": 2}, "scores": {}}),
    ],
)
def test_invalid_explicit(tool, values):
    r = execute(tool, values, 0)
    assert r["status"] == "invalid" and r["errors"] and r["outputs"] == {}


def test_reference_extraction_preserves_unknowns_and_original_units():
    from app.orchestration.scenario import BRIEF
    from app.services.brief import extract

    complete = extract(BRIEF)
    assert complete["constraints"]["latency"]["original"] == "30 minutes"
    incomplete = extract("Monitor wildfires")
    assert incomplete["constraints"]["latency"]["status"] == "unknown"
    assert incomplete["operating_domain"] == "Unknown"
