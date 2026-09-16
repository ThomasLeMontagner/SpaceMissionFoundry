"""Bounded, sampled circular-orbit geometry on a rotating spherical Earth.

Relative epoch: the Earth rotation angle at t=0 is an explicit input, not a date.
No SGP4, J2, atmosphere, terrain, payload scheduling or data-transfer simulation.
"""

import math

from app.domain.engineering_inputs import validate_inputs
from app.engineering_tools.calculations import U, q, quantity

RADIUS = 6371000.0
MU = 3.986004418e14
ROTATION = 7.292115e-5


def radians(value):
    return U.Quantity(value["value"], value["unit"]).to("radian").magnitude


def position(t, radius, inclination, raan, argument, earth_angle):
    u = argument + math.sqrt(MU / radius**3) * t
    node = raan - earth_angle - ROTATION * t
    return (
        radius
        * (math.cos(node) * math.cos(u) - math.sin(node) * math.sin(u) * math.cos(inclination)),
        radius
        * (math.sin(node) * math.cos(u) + math.cos(node) * math.sin(u) * math.cos(inclination)),
        radius * math.sin(u) * math.sin(inclination),
    )


def normal(site):
    lat, lon = radians(site["latitude"]), radians(site["longitude"])
    return (math.cos(lat) * math.cos(lon), math.cos(lat) * math.sin(lon), math.sin(lat))


def elevation(satellite, site_normal):
    line = tuple(satellite[i] - RADIUS * site_normal[i] for i in range(3))
    distance = math.sqrt(sum(x * x for x in line))
    return math.asin(max(-1, min(1, sum(line[i] * site_normal[i] for i in range(3)) / distance)))


def windows(flags, dt, horizon):
    result = []
    start = None
    for index in range(len(flags) + 1):
        visible = index < len(flags) and flags[index]
        if visible and start is None:
            start = index * dt
        if not visible and start is not None:
            end = min(horizon, index * dt)
            result.append(
                dict(
                    start_s=round(start, 6),
                    end_s=round(end, 6),
                    duration_s=round(end - start, 6),
                    boundary_truncated=start == 0 or end == horizon,
                )
            )
            start = None
    return result


def largest_gap(events, horizon):
    cursor, gap = 0.0, 0.0
    for event in events:
        gap = max(gap, event["start_s"] - cursor)
        cursor = event["end_s"]
    return max(gap, horizon - cursor)


def calculate(inputs):
    altitude = q(inputs["altitude"], "m")
    if not 100000 <= altitude <= 2000000:
        raise ValueError("Preliminary access model supports LEO altitudes from 100 to 2000 km")
    values = validate_inputs("access", {k: v for k, v in inputs.items() if k != "altitude"})
    radius = RADIUS + altitude
    duration = q(values["duration"], "s")
    count = math.ceil(duration / q(values["step"], "s"))
    dt = duration / count
    angles = [
        radians(values[k])
        for k in ["inclination", "raan", "argument_of_latitude", "earth_rotation_angle"]
    ]
    # Surface footprint is capped at the geometric horizon to prevent seeing through Earth.
    cap = min(q(values["footprint_width"], "m") / (2 * RADIUS), math.acos(RADIUS / radius))
    cosine = math.cos(cap)
    mask = radians(values["minimum_elevation"])
    targets, stations = values["targets"], values["stations"]
    normals = [normal(s) for s in targets + stations]
    flags = [[] for _ in normals]
    union = []
    track = []
    stride = max(1, math.ceil(count / 2000))
    for index in range(count):
        t = (index + 0.5) * dt
        sat = position(t, radius, *angles)
        for j, n in enumerate(normals):
            visible = (
                sum(sat[k] * n[k] for k in range(3)) / radius >= cosine
                if j < len(targets)
                else elevation(sat, n) >= mask
            )
            flags[j].append(visible)
        union.append(any(f[-1] for f in flags[len(targets) :]))
        if index % stride == 0 or index == count - 1:
            track.append(
                dict(
                    time_s=round(t, 3),
                    latitude=round(math.degrees(math.asin(max(-1, min(1, sat[2] / radius)))), 5),
                    longitude=round(math.degrees(math.atan2(sat[1], sat[0])), 5),
                )
            )
    station_events = windows(union, dt, duration)
    target_results = []
    waits = []
    unmatched = 0
    for site, flag in zip(targets, flags):
        events = windows(flag, dt, duration)
        intervals = [b["start_s"] - a["start_s"] for a, b in zip(events, events[1:])]
        for event in events:
            next_contact = next((w for w in station_events if w["end_s"] > event["start_s"]), None)
            if next_contact:
                waits.append(max(0, next_contact["start_s"] - event["start_s"]))
            else:
                unmatched += 1
        target_results.append(
            dict(
                **site,
                windows=events,
                observed=bool(events),
                largest_gap=quantity(largest_gap(events, duration), "s"),
                max_observed_revisit=quantity(max(intervals), "s") if intervals else None,
            )
        )
    station_results = [
        dict(**site, windows=windows(flag, dt, duration), contact=quantity(sum(flag) * dt, "s"))
        for site, flag in zip(stations, flags[len(targets) :])
    ]
    return dict(
        horizon=quantity(duration, "s"),
        sample_step=quantity(dt, "s"),
        samples=count,
        earth_model="Spherical Earth; circular two-body orbit; constant Earth rotation; relative epoch",
        targets=target_results,
        stations=station_results,
        network_windows=station_events,
        contact=quantity(sum(union) * dt, "s"),
        daily_contact=quantity(sum(union) * dt / duration * 86400, "s"),
        observed_fraction=quantity(
            sum(t["observed"] for t in target_results) / len(targets), "dimensionless"
        ),
        largest_target_gap=quantity(max(t["largest_gap"]["value"] for t in target_results), "s"),
        ground_track=track,
        opportunity_wait=quantity(max(waits), "s") if waits and not unmatched else None,
        observations_without_later_contact=unmatched,
        delivery_latency="Unverified: contact opportunities omit transmission duration, queues, processing and dissemination",
        limitations=[
            "Point targets only, not regional area coverage. Both candidates share the declared orbit and footprint geometry.",
            "Midpoint sampling can miss short passes; window boundaries have sample-scale uncertainty. Refine the step before drawing conclusions.",
            "Revisit is start-to-start between observed windows; fewer than two windows means unknown. Edge gaps are finite-horizon censored values.",
            "Contact totals are a union across stations, not booked capacity. Daily contact is a horizon-average, not a guaranteed daily minimum.",
            "Opportunity wait uses observation-window starts and next geometric contact; it is optimistic and is not delivery latency.",
            "No J2, eccentricity, terrain, weather, illumination, pointing, scheduling, RF acquisition or station availability constraints.",
        ],
    )
