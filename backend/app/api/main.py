import asyncio
import hmac
import json
import os

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import Response, StreamingResponse
from pydantic import Field

from app.domain.models import Proposal, Strict
from app.orchestration.scenario import BRIEF
from app.persistence.store import Store
from app.reports.export import csv_export, report
from app.services.workflow import Workflow


def authorize(request: Request):
    token = os.getenv("MISSION_OWNER_TOKEN")
    if token and not hmac.compare_digest(
        request.headers.get("Authorization", ""), "Bearer " + token
    ):
        raise HTTPException(401, "A valid mission owner token is required")
    if not token and os.getenv("DEMO_MODE", "true").lower() != "true":
        raise HTTPException(503, "Set MISSION_OWNER_TOKEN or explicitly enable local DEMO_MODE")


class Create(Strict):
    name: str = Field(min_length=1, max_length=120)
    brief: str = Field(min_length=20, max_length=12000)


class Command(Strict):
    revision: int = Field(ge=0)


class Decide(Command):
    action: str
    reason: str = Field(min_length=3, max_length=2000)


class Select(Command):
    candidate: str
    weights: dict[str, float]
    reason: str = Field(min_length=3, max_length=2000)


class Approve(Command):
    name: str = Field(min_length=1, max_length=120)
    confirm: bool


class Restore(Command):
    source_revision: int = Field(ge=0)


def create_app(store=None):
    store = store or Store()
    service = Workflow(store)
    app = FastAPI(title="Mission Foundry", version="0.1.0", dependencies=[Depends(authorize)])
    app.state.store = store

    @app.exception_handler(ValueError)
    async def invalid(request, exc):
        return Response(
            json.dumps({"detail": str(exc)}), status_code=409, media_type="application/json"
        )

    @app.exception_handler(KeyError)
    async def missing(request, exc):
        return Response(
            json.dumps({"detail": str(exc)}), status_code=404, media_type="application/json"
        )

    @app.get("/api/scenario")
    def scenario():
        return {"name": "Pyra · Southern Europe Wildfire Monitor", "brief": BRIEF, "version": "1.0"}

    @app.get("/api/missions")
    def missions():
        return store.list()

    @app.post("/api/missions", status_code=201)
    def create(body: Create):
        return service.create(body.name, body.brief)

    @app.get("/api/missions/{id}")
    def get(id: str):
        return store.get(id)

    @app.post("/api/missions/{id}/advance")
    def advance(id: str, body: Command):
        return service.advance(id, body.revision)

    @app.post("/api/missions/{id}/proposals")
    def submit(id: str, body: Proposal):
        return service.submit(id, body)

    @app.post("/api/missions/{id}/proposals/{pid}/decision")
    def decide(id: str, pid: str, body: Decide):
        return service.decide(id, pid, body.action, body.reason, body.revision)

    @app.post("/api/missions/{id}/select")
    def select(id: str, body: Select):
        return service.select(id, **body.model_dump())

    @app.post("/api/missions/{id}/baseline")
    def baseline(id: str, body: Approve):
        return service.baseline(id, **body.model_dump())

    @app.post("/api/missions/{id}/pause")
    def pause(id: str, body: Command):
        old = store.get(id)
        service.guard(old, body.revision)
        m = old.model_copy(deep=True)
        m.paused = not m.paused
        for p in m.proposals.values():
            if p.status in ["submitted", "challenged"] and p.target_revision == old.revision:
                p.target_revision = old.revision + 1
        return store.save(m, "human", "Paused workflow" if m.paused else "Resumed workflow", old)

    @app.get("/api/missions/{id}/history")
    def history(id: str):
        store.get(id)
        return [
            {k: v for k, v in event.items() if k not in ["previous_state", "resulting_state"]}
            for event in store.history(id)
        ]

    @app.get("/api/missions/{id}/revisions/{revision}")
    def revision(id: str, revision: int):
        return store.revision(id, revision)

    @app.post("/api/missions/{id}/restore")
    def restore(id: str, body: Restore):
        old = store.get(id)
        if body.revision != old.revision:
            raise ValueError("Stale revision")
        m = store.revision(id, body.source_revision)
        m.baseline = None
        m.entities = {
            k: v for k, v in m.entities.items() if v.kind != "Baseline" and k != "baseline-approval"
        }
        if m.phase == "Baselined":
            m.phase = "Ready for baseline"
        for p in m.proposals.values():
            if p.status in ["submitted", "challenged"]:
                p.target_revision = old.revision + 1
        return store.save(
            m, "human", f"Restored from revision {body.source_revision}; history retained", old
        )

    @app.get("/api/missions/{id}/objects/{object_id}/relations")
    def relations(id: str, object_id: str):
        m = store.get(id)
        if object_id not in m.entities:
            raise KeyError("Object does not exist")
        return {
            "outgoing": m.entities[object_id].relations,
            "incoming": [
                {"source": e.id, "type": r.type}
                for e in m.entities.values()
                for r in e.relations
                if r.target == object_id
            ],
        }

    @app.get("/api/missions/{id}/export/{format}")
    def export(id: str, format: str):
        m = store.baseline(id)
        if format == "json":
            data, media = json.dumps(m, indent=2), "application/json"
        elif format == "md":
            data, media = report(m), "text/markdown"
        elif format == "csv":
            data, media = csv_export(m), "text/csv"
        else:
            raise HTTPException(404, "Use json, md, or csv")
        return Response(
            data,
            media_type=media,
            headers={
                "Content-Disposition": f'attachment; filename="mission-{m["baseline"]}.{format}"'
            },
        )

    @app.get("/api/missions/{id}/events")
    async def events(id: str, request: Request):
        store.get(id)

        async def stream():
            last = -1
            for _ in range(120):
                if await request.is_disconnected():
                    break
                current = await asyncio.to_thread(store.get, id)
                if current.revision != last:
                    last = current.revision
                    yield f"event: revision\ndata: {json.dumps({'revision': last, 'phase': current.phase})}\n\n"
                else:
                    yield ": heartbeat\n\n"
                await asyncio.sleep(1)

        return StreamingResponse(
            stream(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"}
        )

    return app


app = create_app()
