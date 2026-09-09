# Validation record — 2026-09-09

## Exercised

- Backend on SQLite: **21 passed, 1 skipped** (the skip is PostgreSQL-specific trigger enforcement).
- Backend on a migrated temporary PostgreSQL 16 database: **22 passed**.
- PostgreSQL direct-SQL history deletion rejected by the migration trigger; optimistic concurrency and ORM immutability also tested.
- Alembic initial migration applied successfully to SQLite and PostgreSQL.
- Backend Ruff static checks and formatting: passed.
- Clean `npm ci` install and dependency audit: passed, zero reported vulnerabilities.
- Frontend TypeScript production build and Prettier formatting: passed.
- React Testing Library / Vitest: **3 passed**.
- Playwright in installed Google Chrome: complete mission-to-baseline flow, independent finding resolution, explicit confirmation, all three downloads, all workbench sections, object details, filtering, challenge, pause/resume, rejection, replay and historical restore.
- Workbench screenshot visually inspected at desktop size.
- Reference scenario generator wrote a baseline model JSON, Markdown concept report and full before/after event log.
- Docker Compose configuration validation: passed.

The PostgreSQL test instance was isolated in `/tmp/mission-foundry-pg`, bound to localhost on port 55439, with a dedicated database. It did not use or alter another project database.

## Limits of the verification

Docker's daemon was unavailable. The full container build/start path has **not** been exercised. Its configuration, database schema and application services were validated separately.

No paid LLM call was made. The optional adapter's rationale-only contract and cost preflight were tested with an HTTP mock. Provider billing reconciliation and aggregate run-cost reservations remain deferred.

No high-fidelity engineering verification is claimed. Positive resource margins are conditional on declared concept assumptions. End-to-end 30-minute delivery, coverage/revisit, detection sensitivity, lifetime, cost confidence, pointing and thermal feasibility remain unverified.

The API test client emits two upstream deprecation warnings about httpx and AnyIO compatibility; all assertions pass. File-watcher polling is enabled because this host exhausted its inotify watcher limit. Browser tests use a separate temporary SQLite database.
