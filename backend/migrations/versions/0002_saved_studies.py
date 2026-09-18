"""Immutable sensitivity evidence stored separately from mission revisions."""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"


def upgrade():
    op.create_table(
        "sensitivity_studies",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("mission_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("created_at", sa.String(), nullable=False),
        sa.Column("result", sa.JSON(), nullable=False),
    )
    op.create_index("ix_sensitivity_studies_mission_id", "sensitivity_studies", ["mission_id"])
    if op.get_bind().dialect.name == "postgresql":
        op.execute(
            "CREATE TRIGGER immutable_studies BEFORE UPDATE OR DELETE ON sensitivity_studies FOR EACH ROW EXECUTE FUNCTION prevent_history_mutation()"
        )
    elif op.get_bind().dialect.name == "sqlite":
        for action in ["UPDATE", "DELETE"]:
            op.execute(
                f"CREATE TRIGGER immutable_studies_{action.lower()} BEFORE {action} ON sensitivity_studies BEGIN SELECT RAISE(ABORT, 'Studies are append-only'); END"
            )


def downgrade():
    raise RuntimeError("Destructive study history downgrade is intentionally unsupported")
