"""Deterministic finite-horizon FIFO delivery of products from sampled target windows."""

import math
from collections import deque

from app.domain.engineering_inputs import validate_inputs
from app.engineering_tools.calculations import U, fraction, q, quantity


def simulate(inputs):
    delays = validate_inputs("delivery", inputs["delays"])
    payload = validate_inputs("data", inputs["payload"])
    link = validate_inputs("link", inputs["link"])
    access = inputs["access"]
    horizon = q(access["horizon"], "s")
    if not 0 < horizon <= 604800:
        raise ValueError("Delivery requires a finite access horizon of at most 7 days")
    onboard, ground, dissemination = [
        q(delays[k], "s") for k in ["onboard_delay", "ground_delay", "dissemination_delay"]
    ]
    production_rate = (
        q(payload["rate"], "bit/s") * fraction(payload["duty"]) / q(payload["compression"], "")
    )
    storage = q(payload["storage"], "bit")
    margin = inputs["link_result"]["link_margin_db"]
    rf_margin = U.Quantity(margin["value"], margin["unit"]).to("").magnitude
    if not math.isfinite(rf_margin):
        raise ValueError("A valid RF result is required")
    rate = q(link["rate"], "bit/s") * fraction(link["efficiency"]) if rf_margin >= 0 else 0.0

    def interval(window):
        start, end = window["start_s"], window["end_s"]
        if not (math.isfinite(start) and math.isfinite(end) and 0 <= start < end <= horizon):
            raise ValueError("Access windows must lie within the analysis horizon")
        return float(start), float(end)

    # Re-union contacts defensively: parallel stations do not multiply the one-radio rate.
    contacts = []
    for start, end in sorted(interval(w) for w in access["network_windows"]):
        if contacts and start <= contacts[-1][1]:
            contacts[-1][1] = max(contacts[-1][1], end)
        else:
            contacts.append([start, end])
    jobs = []
    for target in access["targets"]:
        for index, window in enumerate(target["windows"]):
            start, end = interval(window)
            bits = production_rate * (end - start)
            if bits <= 0:
                continue
            jobs.append(
                dict(
                    id=f"{target['name']}:{index + 1}",
                    target=target["name"],
                    acquired_at_s=start,
                    queued_at_s=end,
                    ready_at_s=end + onboard,
                    size_bits=bits,
                    remaining_bits=bits,
                    transmitted_bits=0.0,
                    downlinked_at_s=None,
                    delivered_at_s=None,
                    projected_delivery_at_s=None,
                    latency_s=None,
                    status="queued",
                    boundary_truncated=window.get("boundary_truncated", False),
                )
            )
    if len(jobs) > 10000:
        raise ValueError("Delivery analysis exceeds 10,000 observation products")
    jobs.sort(key=lambda job: (job["queued_at_s"], job["id"]))
    times = sorted(
        {
            0.0,
            horizon,
            *(t for w in contacts for t in w),
            *(t for job in jobs for t in [job["queued_at_s"], job["ready_at_s"]] if t <= horizon),
        }
    )
    queue = deque()
    buffer = peak = transferred = 0.0
    incoming = contact_index = 0
    trace = []
    for index, t in enumerate(times):
        # The preceding interval completes transfers before new products at this timestamp.
        while incoming < len(jobs) and jobs[incoming]["queued_at_s"] <= t:
            job = jobs[incoming]
            incoming += 1
            if buffer + job["size_bits"] > storage:
                job["status"] = "dropped"
                job["remaining_bits"] = 0.0
            else:
                queue.append(job)
                buffer += job["size_bits"]
                peak = max(peak, buffer)
        trace.append(dict(time_s=t, queued_bits=buffer))
        if index == len(times) - 1:
            break
        end = times[index + 1]
        while contact_index < len(contacts) and contacts[contact_index][1] <= t:
            contact_index += 1
        active = (
            contact_index < len(contacts)
            and contacts[contact_index][0] <= t < contacts[contact_index][1]
        )
        cursor = t
        while active and rate > 0 and queue and cursor < end:
            job = queue[0]
            cursor = max(cursor, job["ready_at_s"])
            if cursor >= end:
                break
            amount = min(job["remaining_bits"], rate * (end - cursor))
            cursor += amount / rate
            job["remaining_bits"] -= amount
            job["transmitted_bits"] += amount
            transferred += amount
            buffer = max(0, buffer - amount)
            if job["remaining_bits"] <= 0:
                queue.popleft()
                job["downlinked_at_s"] = cursor
                job["projected_delivery_at_s"] = cursor + ground + dissemination
                if job["projected_delivery_at_s"] <= horizon:
                    job["status"] = "delivered"
                    job["delivered_at_s"] = job["projected_delivery_at_s"]
                    job["latency_s"] = job["delivered_at_s"] - job["acquired_at_s"]
                else:
                    job["status"] = "ground_processing"
            else:
                job["status"] = "queued"
        trace.append(dict(time_s=end, queued_bits=buffer))
    delivered = [job for job in jobs if job["status"] == "delivered"]
    dropped = [job for job in jobs if job["status"] == "dropped"]
    pending = [job for job in jobs if job["status"] in ["queued", "ground_processing"]]
    complete = (
        bool(jobs)
        and len(delivered) == len(jobs)
        and not any(j["boundary_truncated"] for j in jobs)
    )
    stride = max(1, math.ceil(len(trace) / 2000))
    return dict(
        horizon=quantity(horizon, "s"),
        observations=jobs,
        observation_count=len(jobs),
        delivered_count=len(delivered),
        dropped_count=len(dropped),
        pending_count=len(pending),
        maximum_latency=quantity(max(j["latency_s"] for j in delivered), "s") if complete else None,
        delivered_only_maximum_latency=quantity(max(j["latency_s"] for j in delivered), "s")
        if delivered
        else None,
        delivered_fraction=quantity(len(delivered) / len(jobs), "dimensionless") if jobs else None,
        produced=quantity(sum(j["size_bits"] for j in jobs), "bit"),
        transmitted=quantity(transferred, "bit"),
        dropped=quantity(sum(j["size_bits"] for j in dropped), "bit"),
        queued=quantity(buffer, "bit"),
        peak_queue=quantity(peak, "bit"),
        effective_rate=quantity(rate, "bit/s"),
        queue_trace=trace[::stride] + ([trace[-1]] if trace and (len(trace) - 1) % stride else []),
        assessment="Complete modeled workload"
        if complete
        else "Incomplete or horizon-censored workload",
        limitations=[
            "One product per sampled target window; size = payload rate × duty fraction × window duration / compression. Overlapping target windows are separate products.",
            "Products enter storage at window end, become ready after a fixed onboard delay, and transmit FIFO with one radio. Storage is freed as bits transmit; overflow drops the entire newly arriving product.",
            "Usable rate is declared link rate × efficiency, or zero for a negative recorded RF margin. Station windows are unioned; geometric availability is assumed booked and usable.",
            "Ground processing and dissemination are fixed delays per product with unlimited parallel processing; no shared ground CPU queues, retry, packet overhead beyond efficiency, contention or background traffic.",
            "Only delivery completed within the finite horizon is counted. Truncated observation windows prevent a full-workload pass. No observations means unverified, not success.",
            "This target-window workload differs from the continuous daily data budget. Results inherit access sampling uncertainty and do not certify operational delivery performance.",
        ],
    )


def assess_deadline(outputs, limit):
    """Return conditional pass, decisive fail, or unresolved finite-horizon evidence."""
    outcomes = []
    horizon = q(outputs["horizon"], "s")
    for job in outputs["observations"]:
        missed = (
            job["status"] == "dropped"
            or (job["latency_s"] is not None and job["latency_s"] > limit)
            or (
                job["status"] in ["queued", "ground_processing"]
                and horizon - job["acquired_at_s"] > limit
            )
        )
        status = (
            "missed"
            if missed
            else "met"
            if job["status"] == "delivered" and not job["boundary_truncated"]
            else "unresolved"
        )
        outcomes.append(
            dict(id=job["id"], deadline_at_s=job["acquired_at_s"] + limit, status=status)
        )
    missed = sum(o["status"] == "missed" for o in outcomes)
    unresolved = sum(o["status"] == "unresolved" for o in outcomes)
    status = "fail" if missed else "pass" if outcomes and not unresolved else "unverified"
    return dict(
        status=status,
        missed_deadlines=missed,
        unresolved_deadlines=unresolved,
        deadline_outcomes=outcomes,
        reason="Conditional on the recorded finite-horizon workload and delivery assumptions; dropped/late products fail, incomplete evidence cannot pass.",
    )
