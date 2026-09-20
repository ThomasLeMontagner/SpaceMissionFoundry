import os
from uuid import uuid4

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


class StudyRow(Base):
    __tablename__ = "sensitivity_studies"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    mission_id: Mapped[str] = mapped_column(String, index=True)
    name: Mapped[str] = mapped_column(String)
    created_at: Mapped[str] = mapped_column(String)
    result: Mapped[dict] = mapped_column(JSON)


def immutable(*args):
    raise ValueError("History and baselines are append-only")


for table in [RevisionRow, BaselineRow, RelationshipRow, StudyRow]:
    event.listen(table, "before_update", immutable)
    event.listen(table, "before_delete", immutable)


class Store:
    def __init__(self, url=None):
        url = url or os.getenv("DATABASE_URL", "sqlite:///./mission-foundry.db")
        self.engine = create_engine(
            url,
            connect_args={"check_same_thread": False, "timeout": 30}
            if url.startswith("sqlite")
            else {},
        )
        if self.engine.dialect.name == "sqlite":
            event.listen(self.engine, "connect", self.configure_sqlite)

    @staticmethod
    def configure_sqlite(connection, record):
        # Keep readers independent of commits without weakening synchronous durability.
        cursor = connection.cursor()
        try:
            cursor.execute("PRAGMA busy_timeout=30000")
            mode = cursor.execute("PRAGMA journal_mode").fetchone()[0]
            if mode not in ["wal", "memory"]:
                actual = cursor.execute("PRAGMA journal_mode=WAL").fetchone()[0]
                if actual != "wal":
                    raise ValueError("File-backed SQLite requires WAL journal mode")
        finally:
            cursor.close()

    def initialize(self):
        Base.metadata.create_all(self.engine)

    def get(self, mission_id):
        with Session(self.engine) as s:
            row = s.get(MissionRow, mission_id)
            if not row:
                raise KeyError("Mission does not exist")
            return Model.model_validate(row.model)

    def save_study(self, mission_id, name, result):
        with Session(self.engine) as s, s.begin():
            if self.engine.dialect.name == "sqlite":
                # SQLite ignores FOR UPDATE. Reserve its writer before reading the
                # revision so a design change cannot commit between check and insert.
                s.connection().exec_driver_sql("BEGIN IMMEDIATE")
            mission = s.get(MissionRow, mission_id, with_for_update=True)
            if not mission:
                raise KeyError("Mission does not exist")
            if mission.model.get("archived"):
                raise ValueError("Restore the archived mission before saving studies")
            if mission.revision != result["source_revision"]:
                raise ValueError("Mission changed; rerun the study before saving")
            row = StudyRow(
                id=str(uuid4()), mission_id=mission_id, name=name, created_at=now(), result=result
            )
            s.add(row)
            return dict(
                id=row.id,
                mission_id=mission_id,
                name=name,
                created_at=row.created_at,
                result=result,
            )

    def studies(self, mission_id):
        self.get(mission_id)
        with Session(self.engine) as s:
            return [
                dict(
                    id=r.id,
                    name=r.name,
                    created_at=r.created_at,
                    source_revision=r.result["source_revision"],
                    candidate=r.result["candidate"],
                    parameter=r.result["parameter"],
                )
                for r in s.scalars(
                    select(StudyRow)
                    .where(StudyRow.mission_id == mission_id)
                    .order_by(StudyRow.created_at.desc(), StudyRow.id)
                )
            ]

    def study(self, mission_id, study_id):
        self.get(mission_id)
        with Session(self.engine) as s:
            row = s.get(StudyRow, study_id)
            if not row or row.mission_id != mission_id:
                raise KeyError("Saved study does not belong to this mission")
            return dict(
                id=row.id,
                mission_id=mission_id,
                name=row.name,
                created_at=row.created_at,
                result=row.result,
            )

    def list(self, archived=False):
        with Session(self.engine) as s:
            return [
                {
                    "id": r.id,
                    "name": r.model["name"],
                    "revision": r.revision,
                    "archived": r.model.get("archived", False),
                }
                for r in s.scalars(select(MissionRow))
                if r.model.get("archived", False) == archived
            ]

    def save(self, model, actor, reason, previous=None, baseline=False):
        expected = previous.revision if previous else -1
        model.revision = expected + 1
        model.modified_at = now()
        for key, e in model.entities.items():
            if previous and e != previous.entities.get(key):
                if key in previous.entities:
                    e.created_at = previous.entities[key].created_at
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

    def baselines(self, mission_id):
        self.get(mission_id)
        with Session(self.engine) as s:
            return sorted(
                [
                    {
                        "id": row.id,
                        "revision": row.snapshot["revision"],
                        "name": row.snapshot["entities"][row.id]["title"],
                    }
                    for row in s.scalars(
                        select(BaselineRow).where(BaselineRow.mission_id == mission_id)
                    )
                ],
                key=lambda item: item["revision"],
            )

    def baseline(self, mission_id, baseline_id=None):
        model = self.get(mission_id)
        with Session(self.engine) as s:
            key = baseline_id or model.baseline
            row = s.get(BaselineRow, key) if key else None
            if not row or row.mission_id != mission_id:
                raise ValueError("An approved baseline belonging to this mission is required")
            return row.snapshot
