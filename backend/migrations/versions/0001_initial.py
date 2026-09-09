"""Versioned model snapshots, append-only audit and typed relationships."""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None


def upgrade():
    op.create_table(
        "missions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("model", sa.JSON(), nullable=False),
    )
    op.create_table(
        "revisions",
        sa.Column("mission_id", sa.String(), primary_key=True),
        sa.Column("revision", sa.Integer(), primary_key=True),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.Column("event", sa.JSON(), nullable=False),
    )
    op.create_table(
        "baselines",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("mission_id", sa.String(), nullable=False),
        sa.Column("snapshot", sa.JSON(), nullable=False),
    )
    op.create_index("ix_baselines_mission_id", "baselines", ["mission_id"])
    op.create_table(
        "relationships",
        sa.Column("mission_id", sa.String(), primary_key=True),
        sa.Column("revision", sa.Integer(), primary_key=True),
        sa.Column("source", sa.String(), primary_key=True),
        sa.Column("target", sa.String(), primary_key=True),
        sa.Column("type", sa.String(), primary_key=True),
    )
    if op.get_bind().dialect.name == "postgresql":
        op.execute(
            "CREATE FUNCTION prevent_history_mutation() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'History is append-only'; END; $$"
        )
        for table in ["revisions", "baselines", "relationships"]:
            op.execute(
                f"CREATE TRIGGER immutable_history BEFORE UPDATE OR DELETE ON {table} FOR EACH ROW EXECUTE FUNCTION prevent_history_mutation()"
            )


def downgrade():
    raise RuntimeError("Destructive history downgrade is intentionally unsupported")
