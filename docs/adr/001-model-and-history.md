# ADR 001: Versioned engineering model with append-only snapshots

Accepted. PostgreSQL stores current model, complete revision snapshots, before/after audit events, immutable baselines and typed relationship rows. SQLAlchemy and Alembic own persistence. Use JSON for extensible engineering payloads and relational keys for mission/revision identity and typed edges. Avoid a graph database in this MVP.

Consequences: simple reproducible replay and atomic changes; larger storage footprint. Generic payload fields are intentionally a partial schema solution. Snapshot compaction and indexed entity projections require future profiling. Historical restore creates a new revision.
