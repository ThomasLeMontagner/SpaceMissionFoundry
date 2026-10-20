"""Persisted, conservative accounting for a bounded collaboration, across all rounds."""

import math
import os
from datetime import timedelta

from pydantic import Field

from app.agents.design_provider import CALL_TOKEN_RESERVATION
from app.domain.models import Strict
from app.services import data_alternatives
from app.services import execution_recovery as clock


class Limits(Strict):
    cost_eur: float = Field(default=1, ge=0, le=10000, allow_inf_nan=False)
    tokens: int = Field(default=100000, ge=0, le=10000000, strict=True)
    elapsed_seconds: int = Field(default=3600, ge=1, le=86400, strict=True)


def configured_price():
    try:
        value = float(os.environ["LLM_MAX_PRICE_PER_MILLION"])
        if not math.isfinite(value) or value <= 0:
            raise ValueError()
        return value
    except (KeyError, ValueError):
        raise ValueError(
            "Configure a positive finite maximum EUR token price before starting live work"
        ) from None


def create(limits, mode):
    started = clock.utc_now()
    return dict(
        limits=limits.model_dump(),
        price_per_million=configured_price() if mode == "live" else 0,
        started_at=started.isoformat(),
        deadline=(started + timedelta(seconds=limits.elapsed_seconds)).isoformat(),
        attempts=[],
    )


def totals(budget):
    entries = budget["attempts"]
    return dict(
        tokens=sum(e["accounted_tokens"] for e in entries),
        cost_eur=sum(e["accounted_tokens"] for e in entries) * budget["price_per_million"] / 1e6,
    )


def live_task(data):
    if data.get("workflow") == "requirement-collaboration":
        return data["mode"] == "live" and data["stage"] in ["mission", "formalize", "review"]
    if data["mode"] != "live" or data["stage"] not in ["payload", "bus", "systems"]:
        return False
    if data["stage"] == "systems":
        if data.get("study") in ["data-system", "cross-discipline"]:
            return bool(data_alternatives.eligible(data))
        minimum = data.get("minimum_duty")
        return (minimum is None or data["bus"]["duty"] >= minimum) and all(
            data["evaluate_bus"][tool]["outputs"].get("compliant") is True
            for tool in ["data", "link"]
        )
    return True


def reason(data, before=False):
    budget = data.get("budget")
    if not budget:
        return "This legacy run has no complete usage ledger. Cancel and start a collaboration with limits."
    if clock.lease_expired(budget["deadline"]):
        return "Elapsed-time budget exhausted (including pauses); cancel and start a new collaboration."
    usage = totals(budget)
    reserve = CALL_TOKEN_RESERVATION if before and live_task(data) else 0
    if reserve:
        try:
            price = configured_price()
        except ValueError:
            return "Maximum token price is unavailable; restore configuration before starting a new collaboration."
        if price != budget["price_per_million"]:
            return "Configured token price changed; restore it or cancel and start a new collaboration."
    if usage["tokens"] + reserve > budget["limits"]["tokens"]:
        return "Token budget cannot cover recorded usage and the next call reservation. Cancel and start a new collaboration."
    if (
        usage["cost_eur"] + reserve * budget["price_per_million"] / 1e6
        > budget["limits"]["cost_eur"]
    ):
        return "Estimated cost budget cannot cover recorded usage and the next call reservation. Cancel and start a new collaboration."
    return None


def reserve(data, attempt):
    live = live_task(data)
    data["budget"]["attempts"].append(
        dict(
            id=attempt,
            agent=data["stage"],
            round=data.get("round", 0),
            live=live,
            status="unknown" if live else "running",
            reported_tokens=None if live else 0,
            accounted_tokens=CALL_TOKEN_RESERVATION if live else 0,
            elapsed_seconds=None,
        )
    )


def settle(data, attempt, result, elapsed):
    entry = next(e for e in data["budget"]["attempts"] if e["id"] == attempt)
    entry["elapsed_seconds"] = elapsed
    if not entry["live"]:
        entry["status"] = "finished"
        return
    tokens = (result or {}).get("usage", {}).get("tokens")
    if type(tokens) is int and tokens >= 0:
        entry.update(status="reported", reported_tokens=tokens, accounted_tokens=tokens)
