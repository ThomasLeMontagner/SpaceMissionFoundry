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

## Design iteration milestone — 2026-09-13

- SQLite regression: 32 passed, one PostgreSQL-only skip.
- PostgreSQL 16 regression: 33 passed, including the database immutability trigger and two-baseline change workflow. The isolated test database uses port 55440.
- Vitest / React Testing Library: 6 passed, including quantity and requirement edit submission and draft preservation on validation failure.
- Playwright: original workflow plus design iteration. The latter changes duty cycle, exercises stale state while paused, recalculates on resume, blocks noncompliant selection, corrects contact duration, creates a second baseline, exports the original unchanged, and reviews the impact of an edited requirement.
- Ruff, TypeScript/Vite build and Prettier checks pass. Browser tests use separate app ports 5174/8011.
- GitHub Actions configuration added for these checks using SQLite, a PostgreSQL service and Playwright. Its commands are exercised locally; no hosted Actions run is claimed until the changes are pushed.
- Existing sample exports remain the historical v0.1 fixture. The new code reads those schema-compatible snapshots without rewriting their baseline contents.

## Quantitative requirement checks — 2026-09-14

- Existing SQLite regressions: 32 passed, one PostgreSQL-only skip. New requirement regressions: 8 passed. These cover compatible units, invalid criteria, upper/lower bounds, signed calculated margins, missing/failed/stale evidence, input invalidation, required-criterion selection blocking, removal, and preserved baseline exports.
- Frontend unit tests: 6 passed; production build and formatting checks passed.
- All three Playwright workflows passed, including criterion editing, conversion from grams to kilograms, per-candidate pass status and navigation to recorded analysis evidence. The evidence detail screenshot was inspected.
- Backend lint/format checks and patch whitespace checks passed. No SQL schema changes were required. PostgreSQL was not rerun for this milestone; its previous validation is recorded above.
- Updated the authoritative specification to version 0.2, adding MF-REQ-011 through MF-REQ-015. Semantic statement-to-metric matching remains an explicit owner review responsibility.
