import os

from sqlalchemy import JSON, Integer, String, create_engine, event, select, update
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from app.domain.models import Model, now


class Base(DeclarativeBase):
    pass


class MissionRow(Base):
    __tablename__ = "missions"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    revision: Mapped[int] = mapped_column(Integer)
    model: Mapped[dict] = mapped_column(JSON)


class RevisionRow(Base):
    __tablename__ = "revisions"
    mission_id: Mapped[str] = mapped_column(String, primary_key=True)
    revision: Mapped[int] = mapped_column(Integer, primary_key=True)
    snapshot: Mapped[dict] = mapped_column(JSON)
    event: Mapped[dict] = mapped_column(JSON)


class BaselineRow(Base):
    __tablename__ = "baselines"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    mission_id: Mapped[str] = mapped_column(String, index=True)
    snapshot: Mapped[dict] = mapped_column(JSON)


class RelationshipRow(Base):
    __tablename__ = "relationships"
    mission_id: Mapped[str] = mapped_column(String, primary_key=True)
    revision: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[str] = mapped_column(String, primary_key=True)
    target: Mapped[str] = mapped_column(String, primary_key=True)
    type: Mapped[str] = mapped_column(String, primary_key=True)


def immutable(*args):
    raise ValueError("History and baselines are append-only")


for table in [RevisionRow, BaselineRow, RelationshipRow]:
    event.listen(table, "before_update", immutable)
    event.listen(table, "before_delete", immutable)


class Store:
    def __init__(self, url=None):
        url = url or os.getenv("DATABASE_URL", "sqlite:///./mission-foundry.db")
        self.engine = create_engine(
            url, connect_args={"check_same_thread": False} if url.startswith("sqlite") else {}
        )

    def initialize(self):
        Base.metadata.create_all(self.engine)

    def get(self, mission_id):
        with Session(self.engine) as s:
            row = s.get(MissionRow, mission_id)
            if not row:
                raise KeyError("Mission does not exist")
            return Model.model_validate(row.model)

    def list(self):
        with Session(self.engine) as s:
            return [
                {"id": r.id, "name": r.model["name"], "revision": r.revision}
                for r in s.scalars(select(MissionRow))
            ]

    def save(self, model, actor, reason, previous=None, baseline=False):
        expected = previous.revision if previous else -1
        model.revision = expected + 1
        model.modified_at = now()
        for key, e in model.entities.items():
            if previous and e != previous.entities.get(key):
                e.revision = model.revision
                e.modified_at = model.modified_at
        for key, proposal in model.proposals.items():
            if previous and proposal != previous.proposals.get(key):
                proposal.revision = model.revision
                proposal.modified_at = model.modified_at
        snapshot = model.model_dump(mode="json")
        old = previous.model_dump(mode="json") if previous else None
        affected = [model.id]
        for collection in ["entities", "proposals"]:
            before = old[collection] if old else {}
            after = snapshot[collection]
            affected.extend(
                sorted(k for k in before.keys() | after.keys() if before.get(k) != after.get(k))
            )
        audit = dict(
            id=f"{model.id}:{model.revision}",
            kind="DomainEvent",
            state="accepted",
            owner=actor,
            created_at=now(),
            modified_at=now(),
            revision=model.revision,
            actor=actor,
            reason=reason,
            affected_objects=affected,
            previous_state=old,
            resulting_state=snapshot,
        )
        with Session(self.engine) as s, s.begin():
            if previous:
                result = s.execute(
                    update(MissionRow)
                    .where(MissionRow.id == model.id, MissionRow.revision == expected)
                    .values(revision=model.revision, model=snapshot)
                )
                if result.rowcount != 1:
                    raise ValueError("Stale revision; reload before retrying")
            else:
                s.add(MissionRow(id=model.id, revision=model.revision, model=snapshot))
            s.add(
                RevisionRow(
                    mission_id=model.id, revision=model.revision, snapshot=snapshot, event=audit
                )
            )
            for entity in model.entities.values():
                for rel in entity.relations:
                    s.add(
                        RelationshipRow(
                            mission_id=model.id,
                            revision=model.revision,
                            source=entity.id,
                            target=rel.target,
                            type=rel.type,
                        )
                    )
            if baseline:
                s.add(BaselineRow(id=model.baseline, mission_id=model.id, snapshot=snapshot))
        return model

    def history(self, mission_id):
        with Session(self.engine) as s:
            return [
                r.event
                for r in s.scalars(
                    select(RevisionRow)
                    .where(RevisionRow.mission_id == mission_id)
                    .order_by(RevisionRow.revision)
                )
            ]

    def revision(self, mission_id, revision):
        with Session(self.engine) as s:
            row = s.get(RevisionRow, (mission_id, revision))
            if not row:
                raise KeyError("Revision does not exist")
            return Model.model_validate(row.snapshot)

    def baseline(self, mission_id):
        model = self.get(mission_id)
        with Session(self.engine) as s:
            row = s.get(BaselineRow, model.baseline) if model.baseline else None
            if not row:
                raise ValueError("An approved baseline is required")
            return row.snapshot
