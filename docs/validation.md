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

## Baseline comparison — 2026-09-14

- Frontend unit regressions: 12 passed. Coverage includes directional added/removed/changed objects, quantities, missing versus null values, key and relationship ordering, metadata filtering, mission/proposal changes, same-baseline identity, failed requests, and delayed responses after switching missions.
- All three browser workflows passed. The design-iteration flow now compares two actual baselines, inspects changed duty-cycle values, checks the same-baseline empty state, and verifies both exports remain identical after comparison. The comparison screenshot was visually inspected.
- TypeScript/Vite production build, Prettier and patch whitespace validation passed. Vitest now discovers both `.test.ts` and `.test.tsx` files.
- Fixed a navigation race discovered by the broader browser regression: a delayed mission refresh cannot reopen a mission after switching away. A focused unit regression covers it.
- No backend or database schema changes in this milestone; the existing mission-scoped immutable export API is reused. Updated specification version 0.3 and MF-CFG-004/007/008 traceability. Detailed comparison of two arbitrary revisions remains outside this milestone.

## Preliminary coverage and ground access — 2026-09-15

- SQLite backend regression: 53 passed, one PostgreSQL-only skip. The 13 new access tests include analytic overhead/horizon geometry, Earth rotation, polar position, equatorial repeat timing, sampling refinement, station-union accounting, no-access/unknown cases, signed coordinates, unit and resource validation, stale criterion propagation, controlled tool failure, explicit legacy initialization and immutable baseline preservation.
- Frontend unit regression: 14 passed. Stale/failed access hides the ground track, legacy input initialization requires an explicit action, and approved baselines require reopening before new inputs.
- All four Playwright workflows passed. The new flow edits inclination, adds a southern target with negative latitude, verifies stale-state hiding while paused, resumes recalculation, and checks that delivery latency and existing link-contact assumptions remain unchanged. The ground-track screenshot was visually inspected.
- TypeScript/Vite production build, Ruff lint/format, Prettier and whitespace checks passed. Fixed an editor timing race exposed by larger snapshot responses: input inspectors cannot open while a model action is pending.
- No external orbital library, paid model call or SQL migration was introduced. PostgreSQL was not rerun in this milestone; prior database validation is recorded above. No operational or high-fidelity accuracy is claimed; the analytic and sampling tests validate the stated simplified model.
- Specification version 0.4 adds MF-ANL-013 through MF-ANL-016, and traceability retains MF-ANL-011 as partial because full regional coverage, lifetime and operational access verification remain incomplete. Method references and limits are in `docs/architecture/access-analysis.md`.

## Reversible mission archiving — 2026-09-16

- SQLite regression: 56 passed, one PostgreSQL-only skip. New archive tests cover active/archived listing, restoration of pending approvals, archived mutation guards, stale revisions, idempotent state requests, audit events and unchanged baseline exports/historical snapshots.
- Frontend unit regression: 14 passed. All five Playwright workflows passed, including archive cancellation, persistence after reload, restoration, continued approval and archiving from an open workspace.
- TypeScript/Vite production build, Ruff lint/format, Prettier and whitespace checks passed. The backward-compatible model schema includes the archive flag; no SQL migration was needed. PostgreSQL was not rerun for this milestone.
- Updated specification version 0.5 and traceability for MF-MIS-010/011. No permanent deletion endpoint was added and no user mission was archived during implementation.

## Conditional delivery simulation — 2026-09-18

- Full SQLite backend regression: 62 passed, one PostgreSQL-only skip.
- Six delivery regressions pass: analytic interrupted-contact completion times, FIFO conservation, overlapping station union, overflow drops, negative RF margin, processing beyond the horizon, unit validation, no observations, truncated observations, missed/unresolved deadlines, failed calculation evidence, legacy approval, stale checks/selection and immutable baseline exports.
- Frontend unit regression: 15 passed. Delivery tests hide stale/invalid results and enforce explicit setup for legacy missions and reopening for baselines.
- All five Playwright workflows pass, including delivery tables and queue charts in the coverage workflow. The delivery screenshot was visually inspected.
- TypeScript/Vite production build, Ruff lint/format, Prettier and patch whitespace checks pass. No SQL migration or external dependency was introduced; PostgreSQL was not rerun for this milestone.
- Specification version 0.6 adds MF-ANL-017 through MF-ANL-020 with traceability. Results validate the stated synthetic workload and scheduler, not operational delivery or ground-station availability. Existing user missions were not modified by verification.

## Delivery sensitivity studies — 2026-09-18

- Full SQLite regression: 71 passed, one PostgreSQL-only skip. The sensitivity suite subsequently expanded from 9 to 11 passing tests with controlled tool-failure and product-case-bound checks. Coverage includes unit conversion, duplicate/invalid trial rejection, stale evidence/revisions, storage overflow, RF recalculation, incomplete delivery, accepted-criterion comparisons, and unchanged mission/baseline exports.
- Frontend unit tests: 18 passed, including input validation, disabled stale evidence, request failures, result invalidation and delayed-response isolation across mission/revision keys.
- All six Playwright workflows passed. The new baseline sensitivity test compares on-time and late trials, downloads JSON and verifies unchanged source data. Its browser test was rerun after improving table column widths, and the updated screenshot was visually inspected.
- Ruff, TypeScript/Vite production build, Prettier and patch whitespace checks passed. No schema migration or new dependency was needed. The local backend was restarted and its sensitivity route verified. PostgreSQL was not rerun.
- Specification version 0.7 adds MF-ANL-021–024; MF-ANL-010 is partial because only five delivery parameters support one-at-a-time sweeps. Studies are temporary and exportable, not persisted or automatically adopted.

## Saved sensitivity evidence and comparison — 2026-09-18

- Full SQLite backend regression: 76 passed, one PostgreSQL-only skip. New saved-study tests cover separate-store reloads, mission scoping, baseline preservation, archived/stale request rejection, client-result rejection, ORM immutability and an actual 0001-to-0002 SQLite migration with raw-SQL update/delete rejection.
- Frontend unit tests: 20 passed, including historical labels, incomplete latency, library failure/retry and delayed-response isolation across missions.
- Five existing browser workflows passed. The expanded sensitivity workflow passed after adding explicit accessible names to saved-study selectors; it saves two studies, reloads, compares different deadlines, downloads saved evidence and verifies unchanged mission/baseline exports. Comparison screenshots were inspected and the layout was adjusted to keep latency and deadlines visible side by side.
- Ruff, TypeScript/Vite build, Prettier and whitespace checks passed. The additive migration was applied locally and the saved-study endpoint verified. PostgreSQL migration trigger logic is included but was not exercised in this milestone.
- Specification version 0.8 adds MF-ANL-025–027 and updates MF-ANL-024. Saved studies are immutable records outside mission history; adopting inputs still requires the existing reviewed edit workflow.

## Reviewed proposals from saved trials — 2026-09-18

- Existing 76 SQLite regressions passed with one PostgreSQL-only skip. Three new trial-proposal regressions pass after correcting the rejection assertion to allow the existing audit Decision while preserving all prior design entities. They cover approval/recalculation, source provenance, baseline/study immutability, rejection, mission scoping, stale revisions, invalid indexes, blank rationale, equivalent-value no-ops, changed inputs, pending proposals and archived/baselined guards.
- Frontend unit tests: 21 passed. The new preview test covers baseline reopening, current/proposed values, required rationale and the server-resolved study/trial request.
- All six browser workflows passed. The sensitivity flow now reopens a baseline, proposes a saved trial, verifies inputs are unchanged before approval, approves and waits for fresh calculations, then verifies the saved evidence and original baseline export remain identical.
- Ruff, TypeScript/Vite build, Prettier and whitespace checks passed. The optional Proposal.source_study field is included in the schema artifact and requires no additional migration beyond the saved-study table. No user mission input or approval was changed during verification.
- Requirements version 0.9 adds MF-ANL-028–030. Trial results remain exploratory and are never copied into approved verification conclusions. Recorded input equality is deliberately conservative; changed inputs require a new study.
