"""Durable lease and checkpoint inspection. Reads never execute work or modify history."""

import hashlib
import json
import os
from datetime import UTC, datetime, timedelta

from app.services.design_inputs import IMPACT_KINDS

STAGES = ["payload", "evaluate_payload", "bus", "evaluate_bus", "systems"]
LEASE_SECONDS = 120


def utc_now():
    return datetime.now(UTC)


def lease_deadline():
    return (utc_now() + timedelta(seconds=LEASE_SECONDS)).isoformat()


def parse_time(value):
    try:
        parsed = datetime.fromisoformat(value)
        return parsed if parsed.tzinfo else None
    except (TypeError, ValueError):
        return None


def lease_expired(value):
    deadline = parse_time(value)
    return deadline is not None and utc_now() >= deadline


def fingerprint(model):
    values = {
        k: e.model_dump(mode="json") for k, e in model.entities.items() if e.kind in IMPACT_KINDS
    }
    return hashlib.sha256(json.dumps(values, sort_keys=True).encode()).hexdigest()


def recovery_details(model, run):
    data = run.data
    execution = data.get("execution", {})
    working = data["status"] in ["working", "interrupted"]
    claimed = execution.get("status") == "running"
    deadline = data.get("task_lease") if working else execution.get("lease_expires_at")
    if (working or claimed) and not deadline:
        # Older deployments recorded starts but no lease. Wait a full lease interval.
        started = (
            next((e["timestamp"] for e in reversed(data["events"]) if e["type"] == "started"), None)
            if working
            else execution.get("started_at")
        )
        timestamp = parse_time(started)
        deadline = (timestamp + timedelta(seconds=LEASE_SECONDS)).isoformat() if timestamp else None
    expired = lease_expired(deadline)
    result = dict(
        available=False,
        interrupted=False,
        requires_confirmation=False,
        lease_expires_at=deadline,
        stage=data["stage"],
        completed=data["completed"],
        round=data.get("round", 0),
        revision=model.revision,
        reason="No interrupted execution to recover",
    )
    if not working and not (claimed and data["status"] == "ready"):
        return result
    if not expired:
        result["reason"] = (
            "Execution lease is still active; wait for completion or lease expiry"
            if parse_time(deadline)
            else "Cannot establish a safe recovery point; cancel this run"
        )
        return result
    result.update(
        interrupted=True,
        requires_confirmation=working
        and data["mode"] == "live"
        and data["stage"] in ["payload", "bus", "systems"],
    )
    reason = None
    if model.archived or model.baseline:
        reason = "Restore or reopen the mission before recovery"
    elif model.paused:
        reason = "Resume the mission before recovering its checkpoint"
    elif any(p.status in ["submitted", "challenged"] for p in model.proposals.values()):
        reason = "Resolve pending proposals before recovery"
    elif fingerprint(model) != data["fingerprint"]:
        reason = "Design inputs changed; start a new collaboration"
    elif data["attempts"] >= 10:
        reason = "Task attempt limit reached; cancel and start a new collaboration"
    elif data["mode"] == "live" and os.getenv("LLM_MODEL") != data["provider_model"]:
        reason = "Provider model changed; restore its configuration or start a new run"
    elif data["stage"] not in STAGES or data["completed"] != STAGES[: STAGES.index(data["stage"])]:
        reason = "Checkpoint is inconsistent; cancel and start a new collaboration"
    else:
        keys = ["payload", "evaluate_payload", "bus", "evaluate_bus"][: STAGES.index(data["stage"])]
        if any(not isinstance(data.get(key), dict) for key in keys):
            reason = "Checkpoint evidence is missing; cancel and start a new collaboration"
    result.update(
        available=reason is None,
        reason=reason
        or "Execution interrupted. Completed tasks are preserved; recover the next unfinished task.",
    )
    return result
