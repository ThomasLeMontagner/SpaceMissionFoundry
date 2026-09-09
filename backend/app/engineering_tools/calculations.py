"""Versioned preliminary calculators. No network, generated code, or implicit missing inputs."""

import math
from time import perf_counter

from pint import UnitRegistry

from app.domain.models import now

U = UnitRegistry()
VERSION = "1.0"


def q(value, unit):
    if not isinstance(value, dict) or set(value) != {"value", "unit"}:
        raise ValueError("Quantities require value and unit")
    result = U.Quantity(value["value"], value["unit"]).to(unit).magnitude
    if not math.isfinite(result) or result < 0:
        raise ValueError("Quantities must be finite and nonnegative")
    return result


def quantity(value, unit):
    if not math.isfinite(value):
        raise ValueError("Non-finite result")
    return {"value": round(value, 6), "unit": unit}


def fraction(value):
    result = q(value, "dimensionless")
    if result > 1:
        raise ValueError("Fraction must be between zero and one")
    return result


def mass(i):
    entries = [
        {
            "name": e["name"],
            "cbe": quantity(q(e["mass"], "kg"), "kg"),
            "allocated": quantity(q(e["mass"], "kg") * (1 + fraction(i["margin"])), "kg"),
        }
        for e in i["entries"]
    ]
    total = sum(e["allocated"]["value"] for e in entries)
    limit = q(i["limit"], "kg")
    return dict(
        entries=entries,
        total=quantity(total, "kg"),
        limit=quantity(limit, "kg"),
        margin=quantity(limit - total, "kg"),
        compliant=total <= limit,
    )


def power(i):
    duration = q(i["period"], "hour")
    eclipse = q(i["eclipse"], "hour")
    if duration <= 0 or eclipse >= duration:
        raise ValueError("Eclipse must be shorter than a positive orbital period")
    modes = i["modes"]
    if abs(sum(fraction(m["fraction"]) for m in modes) - 1) > 1e-6:
        raise ValueError("Mode fractions must sum to one")
    load = sum(sum(q(v, "W") for v in m["loads"].values()) * fraction(m["fraction"]) for m in modes)
    generation = q(i["solar"], "W") * (duration - eclipse)
    consumption = load * duration
    battery = q(i["battery"], "Wh") * fraction(i["depth_of_discharge"])
    eclipse_load = q(i["eclipse_load"], "W") * eclipse
    return dict(
        average_load=quantity(load, "W"),
        generated=quantity(generation, "Wh"),
        consumed=quantity(consumption, "Wh"),
        margin=quantity(generation - consumption, "Wh"),
        eclipse_energy=quantity(eclipse_load, "Wh"),
        usable_battery=quantity(battery, "Wh"),
        battery_margin=quantity(battery - eclipse_load, "Wh"),
        compliant=generation >= consumption and battery >= eclipse_load,
    )


def data(i):
    rate = q(i["rate"], "bit/second")
    compression = q(i["compression"], "dimensionless")
    if compression < 1:
        raise ValueError("Compression ratio must be at least one")
    daily = rate * 86400 * fraction(i["duty"]) / compression
    storage = q(i["storage"], "bit")
    return dict(
        daily=quantity(daily, "bit"),
        storage=quantity(storage, "bit"),
        margin=quantity(storage - daily, "bit"),
        compliant=storage >= daily,
    )


def link(i):
    frequency = q(i["frequency"], "Hz")
    distance = q(i["range"], "m")
    rate = q(i["rate"], "bit/second")
    tx = q(i["tx_power"], "W")
    temperature = q(i["noise_temperature"], "K")
    if min(frequency, distance, rate, tx, temperature) <= 0:
        raise ValueError("RF inputs must be positive")
    # dB ratios are explicitly dimensionless; gains and losses are input in dB.
    gains = {
        k: q(i[k], "dimensionless")
        for k in ["tx_gain_db", "rx_gain_db", "loss_db", "required_ebn0_db"]
    }
    fspl = 20 * math.log10(4 * math.pi * distance * frequency / 299792458)
    carrier_dbw = (
        10 * math.log10(tx) + gains["tx_gain_db"] + gains["rx_gain_db"] - fspl - gains["loss_db"]
    )
    ebn0 = carrier_dbw - 10 * math.log10(1.380649e-23 * temperature) - 10 * math.log10(rate)
    rf_margin = ebn0 - gains["required_ebn0_db"]
    daily = rate * q(i["contact"], "second") * fraction(i["efficiency"]) if rf_margin >= 0 else 0
    demand = q(i["demand"], "bit")
    return dict(
        fspl_db=quantity(fspl, "dimensionless"),
        ebn0_db=quantity(ebn0, "dimensionless"),
        link_margin_db=quantity(rf_margin, "dimensionless"),
        capacity=quantity(daily, "bit"),
        margin=quantity(daily - demand, "bit"),
        compliant=rf_margin >= 0 and daily >= demand,
    )


def orbit(i):
    radius = 6371000 + q(i["altitude"], "m")
    period = 2 * math.pi * math.sqrt(radius**3 / 3.986004418e14)
    eclipse = period * math.asin(6371000 / radius) / math.pi
    return dict(
        period=quantity(period, "second"),
        eclipse=quantity(eclipse, "second"),
        coverage="Unknown: no access propagation",
        latency="Unknown: daily capacity is not latency",
    )


def trade(i):
    weights = i["weights"]
    if (
        not weights
        or any(not math.isfinite(w) or w < 0 for w in weights.values())
        or abs(sum(weights.values()) - 1) > 1e-6
    ):
        raise ValueError("Nonnegative criterion weights must sum to one")
    scores = {}
    for name, criteria in i["scores"].items():
        if set(criteria) != set(weights) or any(not 0 <= v <= 5 for v in criteria.values()):
            raise ValueError("Scores must cover criteria on a 0–5 scale")
        scores[name] = round(sum(weights[k] * criteria[k] for k in weights), 6)
    return {"scores": scores, "recommendation": max(scores, key=scores.get)}


TOOLS = dict(mass=mass, power=power, data=data, link=link, orbit=orbit, trade=trade)


def execute(name, inputs, revision, assumptions=None):
    started = perf_counter()
    record = dict(
        tool=name,
        version=VERSION,
        inputs=inputs,
        source_revision=revision,
        assumptions=assumptions or [],
        timestamp=now(),
        warnings=[
            "Preliminary concept sizing; assumed inputs are not validated hardware performance."
        ],
        errors=[],
        outputs={},
        status="valid",
    )
    try:
        record["outputs"] = TOOLS[name](inputs)
    except Exception as exc:
        record.update(status="invalid", errors=[str(exc)])
    record["elapsed_seconds"] = perf_counter() - started
    return record
