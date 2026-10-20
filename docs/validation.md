# Validation record — 2026-09-09

## AI-assisted requirement clarification — 2026-10-20

- Full SQLite backend regression: **235 passed, one PostgreSQL-only skip** in 450.64 seconds. The interrupted earlier run had no retained completion result, so the full suite was rerun before delivery.

- **48 frontend unit tests passed**, along with TypeScript, production build, Prettier, Ruff lint/format and whitespace checks. The final display tolerates a run without a criterion and reflects an accepted or rejected proposal.
- Both browser workflows passed: owner-guided formalization and agent-assisted clarification through separate human approval. The final screen was visually inspected; criterion values use readable text and approved proposals no longer invite duplicate approval.

- Targeted PostgreSQL verification completed during implementation: **39 passed** across requirement collaboration, owner formalization and run budgets, after migration on an isolated UTF-8 PostgreSQL 16 instance with `max_connections=20`. The instance was stopped after testing; user databases were untouched. This is targeted coverage, not a full PostgreSQL-suite rerun.
- Tests cover three separate mocked live-provider calls and their shared context, source-backed criterion selection, owner thresholds, mandatory clarification pauses, reviewer blocking, immutable accepted requirements until approval, partial coverage, source-note changes, concurrent pause/cancel/edits, conservative unknown-call reservations, budget preflight, explicit recovery and round bounds. No paid provider calls were made.
- Requirements v0.22 adds MF-REQ-018–019. README, traceability and architecture describe the bounded manually advanced workflow and its limits. No migration or dependency was added. Separate review does not imply a different model or prove semantic completeness. Simulation is explicitly labeled and does not interpret free-text answers.


## Requirement clarification and formalization — 2026-10-18

- Full SQLite regression: **219 passed, one PostgreSQL-only skip** in 263.37 seconds. Two additional guard cases added during that run were subsequently included in the seven-test formalization run and the 15-test PostgreSQL run.

- Targeted SQLite requirement/formalization tests: 13 passed initially; all seven final formalization tests passed after adding confirmation, stale revision, pending proposal, thread limit and immutable reply coverage.
- Targeted PostgreSQL requirement/formalization regression: **15 passed** after migration on an isolated UTF-8 PostgreSQL 16 instance with `max_connections=20`. The temporary server was stopped after testing. User databases were untouched.
- **45 frontend unit tests passed**. The production build, TypeScript, Prettier, Ruff lint/format and whitespace checks passed.
- Browser workflow passed through recording a question, preserving its reply history, extracting the literal deadline, submitting a partial-coverage proposal and approving it. Initial browser validation exposed a global `aside` style collision; changing the suggestion container fixed navigation. The completed readiness screen was visually inspected.
- Requirements v0.21 adds MF-REQ-016–017; README, traceability and architecture describe owner-guided scope and legacy unassessed criteria. No schema migration, dependency or model call was added. Full coverage remains owner judgment; arbitrary AI requirement derivation and independent semantic validation remain outside this slice.


## Mission-requirement checks for alternatives — 2026-10-16

- Full SQLite backend regression: **214 passed, one PostgreSQL-only skip**, in 462.24 seconds.
- Targeted PostgreSQL verification: **46 passed** in 182.20 seconds across mission requirement studies, cross-discipline impacts, data alternatives and fixture lifecycle. The isolated UTF-8 PostgreSQL 16 instance was migrated to Alembic head and used `max_connections=20`; it was stopped after testing. User databases were untouched. This is targeted coverage, not a full PostgreSQL suite rerun.
- **44 frontend unit tests passed**, with TypeScript, production build, Prettier, Ruff lint/format and whitespace checks passing. The new comparison test distinguishes passed, failed and unverified proposed evidence, criteria and actual values.
- Both targeted browser workflows passed: existing cross-discipline approval and mission-check blocking for the reference scenario's unsupported narrative Must requirements. The new test confirms unchanged accepted inputs and no approval proposal. A locator was scoped to the expanded option's evidence after initially finding a hidden copy. The comparison screenshot was visually inspected; repeated blocker text was condensed and calculation JSON moved into a separate expandable section, then browser-tested again. Test data was disposable.
- New backend coverage includes fresh option-local evidence, unchanged accepted verification, source revisions, missing criteria/access/delivery inputs, failed mandatory criteria, deadline pass/fail/unverified including no observations, changed-requirement rejection, recovery and the product-workload bound. A mocked three-call live round verifies Bus and Systems receive recorded requirement comparisons. Duplicate model context was reduced after the first live-contract test exposed the transport size limit; full evidence remains persisted. No paid provider validation is claimed.
- Requirements v0.20 adds MF-COL-024–025. README, traceability and architecture document optional strict mission checking, workflow 1.6, the 3,000-product-case stage bound and unchanged legacy behavior. No dependency or schema migration was added. Main CI at the branch base `ebdb9d0` completed successfully; this does not claim CI validation of unpushed changes.

## Cross-discipline impact checks — 2026-10-15

- Full SQLite backend regression: **201 passed, one PostgreSQL-only skip** in 312.82 seconds. Existing duty-only, alternatives, budgets, recovery and workflow behavior remain covered.
- Targeted PostgreSQL verification: **33 passed** across impact checks, data alternatives and fixture lifecycle, after Alembic migration on isolated UTF-8 PostgreSQL 16 with `max_connections=20`. The first temporary-server run received a fast shutdown signal and was interrupted; the complete retry in a persistent terminal passed in 72.90 seconds. The temporary server was stopped after verification. This is targeted PostgreSQL coverage, not a full-suite PostgreSQL rerun.
- **43 frontend unit tests passed**, including explicit assumption inputs and missing/failed impact evidence. TypeScript, production build, Prettier, Ruff lint/format and whitespace checks passed.
- Both targeted browser workflows passed: existing data-only alternatives and cross-discipline alternatives through human approval. The new test verifies that accepted mass/power inputs match the evaluated configuration. The comparison screenshot was visually inspected; numerical margins were subsequently formatted to three decimals and covered by the UI tests. Browser tests used disposable SQLite data.
- Impact tests verify Gbyte/Gbit conversion, observation/processing workload, conservative eclipse increments, no savings credit, missing assumptions and failed mass/power gates without a review call/reservation, atomic approval and reproduction of calculator outputs, revision history, recovery and stale mass-source rejection. Mock HTTP tests cover the independent review context and selection in both study types. No paid provider calls were made.
- Requirements v0.19 adds MF-COL-022–023; README, traceability and architecture document workflow 1.5 and the incremental model. No schema migration or dependency was added. Estimates depend on owner-provided coefficients and an adequate accepted baseline; hardware qualification, thermal effects, science adequacy and general mission feasibility remain unverified.

## Bounded data-system alternatives — 2026-10-13

- Full PostgreSQL backend suite: **188 passed**, no skips, after Alembic migration on an isolated UTF-8 PostgreSQL 16 instance with `max_connections=20` (416.65 seconds). The temporary server was stopped after testing; no user databases were touched.
- Full SQLite backend suite: **187 passed, one PostgreSQL-only skip**. Seventeen new cases cover strict owner bounds/options, deterministic evaluation, three-field human approval, immutable source history, infeasibility, clarification, recovery, concurrent pause/cancel/source changes, separate mocked HTTP selection and token accounting. Invalid selection fails; revise/clarify blocks; no eligible option skips the live review and reservation.
- All **41 frontend unit tests** passed; TypeScript and production build passed. Ruff lint/format and whitespace checks passed.
- Both targeted browser workflows passed: existing duty negotiation with clarification and approval, and the new alternatives comparison through approval of duty/compression/storage together. The new test's approval selector was corrected to the existing “Approve design change” label. The existing workflow completion assertion now permits 15 seconds under concurrent load. The comparison screenshot was visually inspected. Browser tests used disposable SQLite data; no user missions were changed.
- Requirements v0.18 adds MF-COL-020–021, with README, architecture and traceability updates. Workflow version 1.4 reuses existing persistence, recovery and whole-run budgets; no database migration or dependency was added. Tests use simulation and mocked provider HTTP; no paid model validation is claimed. Compression quality, science adequacy and storage hardware impacts remain unverified.

## PostgreSQL test connection cleanup — 2026-10-13

- GitHub's PostgreSQL job failed with `FATAL: sorry, too many clients already`. The shared test fixture created a new SQLAlchemy pool per test without disposing it, leaving idle connections open across the suite. The fixture now uses a managed TestClient context and disposes its engine in `finally`, including setup/test failures. Production pooling and database connection limits are unchanged.
- Two regression cases exercise the actual fixture on normal completion and an injected test failure, asserting that physical connections close and the pool retains no connections. Both passed on SQLite. Targeted SQLite workflow, background-execution and concurrency checks also passed: 24 passed, one PostgreSQL-only skip.
- Full PostgreSQL verification completed: **171 passed**, no skips, on an isolated UTF-8 PostgreSQL 16 instance with `max_connections=20`, after migrating through Alembic head. Runtime: 339.60 seconds. The temporary server used a private Unix socket and was stopped after testing; user databases were untouched. The earlier interrupted session's final outcome was unavailable, so this complete rerun is the recorded result.
- Ruff lint/format and patch whitespace checks passed. Frontend code was unchanged and browser tests were not rerun. Existing TestClient dependency deprecation warnings remain unrelated to the connection exhaustion.

## Collaboration run budgets and usage monitoring — 2026-10-12

- Complete SQLite regression coverage passed in two disjoint groups: 66 collaboration/budget/recovery cases and 102 other backend cases, with one PostgreSQL-only skip. Total: 168 passed, one skipped. Eighteen new budget cases cover pre-call admission, cumulative reported usage across rounds, retained unknown reservations after failure/cancellation/recovery, a reopened Store, deadline checks before/after calls, reported overruns, changed pricing, legacy guards and bounded finite inputs. Existing mocked HTTP Systems review tests now verify three-call token accounting and retained reservations for invalid reviews.
- All 38 frontend unit tests passed. Usage tests cover per-task totals, unknown contributions, an 80% warning, live countdown and honest legacy labeling. TypeScript/Vite production build, Prettier, Ruff lint/format and patch whitespace checks passed.
- Targeted browser workflows passed for owner-configured elapsed limits/cancellation, zero-cost simulation with usage rows and human review, and checkpoint recovery preserving accounting. The first concurrent run passed the first two workflows but timed out after five seconds while recovery was still progressing. The completion assertion now allows 15 seconds; the isolated recovery rerun passed. Browser tests used only the disposable test database. Other browser workflows and PostgreSQL were not rerun.
- Requirements v0.17 adds MF-COL-018–019 and updates traceability, README and architecture. Workflow version 1.3 keeps limits, deadline, configured price and per-attempt reservations in existing revision snapshots. No dependencies or database schema changes were needed. Billing remains unknown; conservative configured estimates do not guarantee provider tokenization or charges. Existing legacy runs without complete ledgers require cancellation and a new run before further execution.
- Started the local app with `scripts/dev.sh`; frontend on port 5173 and backend on port 8000 responded successfully. Read-only OpenAPI inspection confirmed the new limit fields. No live/paid provider calls or user mission edits were made.

## Durable collaboration execution and recovery — 2026-10-06

- Complete SQLite backend regression passed in two disjoint groups: 85 passed / one PostgreSQL-only skip for collaboration, recovery and core workflows; 65 passed for remaining calculations and persistence. Total: 150 passed, one skipped. Sixteen recovery cases cover a worker exit after the persisted start, a fresh Store connection, preservation of completed results and immutable history, expired claims between tasks, stale attempt fencing, late responses, unknown live outcomes, strict confirmation, read-only inspection, revision/source/authority/attempt guards, legacy timestamps and mission scoping.
- Frontend: all 35 unit tests passed, including confirmation gating, lease-expiry polling without revision events, cleanup and stale/blocked/busy controls. TypeScript/Vite production build, Prettier, Ruff lint/format and patch whitespace checks passed.
- Both collaboration browser tests passed. The new recovery test seeds an expired task-start checkpoint only in the disposable Playwright database, opens it in the workbench, preserves two completed tasks, explicitly recovers and executes the three remaining tasks to human review. Accepted mission inputs stay unchanged. The recovery-panel screenshot was visually inspected. This models persisted interruption; it does not kill a real provider process. Backend tests recreate the service/database connection without in-memory state.
- Requirements v0.16 adds MF-COL-016–017; README, traceability and architecture describe explicit checkpoint recovery and its limits. Workflow version 1.2 uses existing revision snapshots; no dependencies or schema migrations changed. Recovery makes no provider calls, and unknown live-call retries require acknowledgement of possible duplicate charges. Automatic restart scheduling, exactly-once provider billing and generalized workflow recovery remain outside this slice.
- PostgreSQL and unrelated browser workflows were not rerun. No paid model calls or user mission data changes were made. No local development server was running during the final port check; the app was not restarted.

## Independent Systems review before submission — 2026-10-02

- Complete SQLite regression coverage passed in two disjoint groups after the original all-in-one run was terminated: 69 passed / one PostgreSQL-only skip for core workflow and collaboration; 65 passed for the remaining calculations and persistence tests. Total: 134 passed, one skipped. Thirteen new review cases cover submit/revise/clarify, recorded evidence, prior-review handoff to both disciplines, stale/pause/cancel interruption, failed-tool gating, a separate third mocked provider call and invalid/unactionable review responses. No paid provider calls were made.
- Frontend: 30 unit tests passed, including findings/evidence display, feedback reuse, legacy labeling and directing blocked-review attention to the owner. TypeScript/Vite build, Prettier, Ruff lint/format and whitespace checks passed. The collaboration browser workflow passed through automatic Systems review, retained review events across refresh/revision and separate human approval. The review-panel screenshot was visually inspected. Unrelated browser workflows and PostgreSQL were not rerun.
- Requirements v0.15 adds MF-COL-014–015; README, traceability and architecture document separate live review, strict output validation and explicit rules-based simulation. Independent prompting with the configured model is not a guarantee of correctness or independence between providers. Historical pending proposals are preserved and labeled when no independent assessment was recorded.
- The local app was started and frontend/backend health checked read-only. No user mission data, dependencies or database schemas were changed. Workflow version 1.1 stores review outcomes, evidence context and usage in existing AgentRun snapshots; accepted design inputs still require normal human approval.

## Bounded automatic collaboration progression — 2026-09-29

- Full SQLite backend suite: 121 passed, one PostgreSQL-only skip. Six execution cases cover completion without approval, duplicate/manual claim rejection, pause followed by quick resume, cancellation, provider failure without retry, and a concurrent human proposal remaining approvable. All six passed again after the final stop-message refinement. No paid model calls were made.
- Frontend unit suite: 25 passed; production build, Prettier, Ruff lint/format and whitespace checks passed. The collaboration browser flow passed with Run until review, automatic stop at approval, recorded graph/timeline evidence, refresh, a manually initiated revision round and final human approval. Other browser workflows and PostgreSQL were not rerun for this change.
- The local app was restarted and the new run endpoint verified read-only. No user mission data was edited. No dependency or database schema changes were required.
- Requirements v0.14 and supporting documentation distinguish this bounded in-process worker from durable job scheduling. Browser closure does not stop execution; server-crash recovery remains explicit. Automatic approval, retry and continuation into a new revision round are not implemented. Pause/cancel invalidate the execution claim, with an in-flight call allowed to finish or be discarded respectively.

## Collaboration clarification and revision — 2026-09-29

- Full SQLite backend suite: 115 passed, one PostgreSQL-only skip. All 13 collaboration tests passed, including new feasible/infeasible minimum-duty requests, old-proposal supersession, unchanged accepted inputs until approval, fresh tool evidence, historical snapshot preservation, paused revision preparation, stale-source rejection and blocking provider results below the owner minimum.
- Frontend: 25 unit tests passed; TypeScript/Vite build, Prettier, Ruff lint/format and patch whitespace checks passed. The collaboration browser workflow passed with challenge, clarification, a 3.5% minimum duty request, five new tasks, 23 retained timeline events and approval of the revised value. Existing unrelated browser workflows were not rerun for this change.
- No paid model calls were made. The app was started and its clarification endpoint verified read-only. No user mission records were edited. No database migration or dependency change was required; PostgreSQL was not rerun.
- Requirements v0.13, traceability, README and architecture describe up to three human-requested revision rounds. Simulation applies numeric constraints but does not interpret free-text feedback; general task replanning, independent Systems model review and cumulative cost accounting remain deferred.

## Recorded collaboration interaction graph — 2026-09-22

- Frontend unit suite: 25 passed, including recorded-edge navigation, historical tool-recipient normalization, new-event filtering and paused/terminal status checks. TypeScript/Vite build, Prettier and patch whitespace checks passed.
- The collaboration Playwright workflow passed with graph connection selection, exact timeline filtering, clearing selection, refresh recovery and human approval. The updated graph screenshot was visually inspected. No live model calls or user mission changes were needed.
- Requirements version 0.12.1 and MF-COL-013 traceability describe the partial delivery: recorded exchanges and current attention are visible, while general dependency and unresolved-disagreement semantics remain deferred. Backend code is unchanged from the initial slice, so backend tests were not repeated for this UI addition.

## Initial agent collaboration slice — 2026-09-22

- Full SQLite backend suite: 109 passed, one PostgreSQL-only skip. Two further baseline/scoping and generated-value/rejection cases were subsequently added; all nine collaboration cases passed. Tests cover durable proposal evidence, unchanged inputs before approval, immutable source revisions, retry, pause, cancellation, concurrent source changes and strict mocked provider responses. No paid model calls were made.
- Frontend: 22 unit tests passed; TypeScript/Vite build and Prettier passed. All seven existing Playwright workflows passed. The new collaboration workflow passed after correcting a test locator and explicitly reopening the saved mission after refresh; it exercises five tasks, pause/resume, timeline filtering, refresh without duplicate events and human approval. The resulting collaboration screenshot was visually inspected.
- Ruff lint/format and patch whitespace checks passed. No database schema changes or dependencies were introduced. PostgreSQL was not rerun for this slice; existing revision-snapshot persistence is reused.
- Requirements version 0.12, traceability, README and collaboration architecture document the bounded duty-cycle scope. General mission design, independent Systems LLM review, background scheduling, clarification/replanning and interaction graphs remain incomplete. The live provider HTTP contract is mock-tested only.

## PostgreSQL saved-study reload test correction — 2026-09-20

- Reproduced the pipeline failure against an isolated PostgreSQL 16 database on localhost port 55447, migrated to head and configured with SCRAM password authentication. The original saved-study reload test failed because `str(engine.url)` substituted a masked password when constructing its second Store.
- The test now renders the connection URL with credentials preserved for internal connection creation only, and closes the reopened client and engine afterward. No credentials are logged by the fix. Production code, requirements and database schemas are unchanged.
- Full migrated PostgreSQL regression: 103 passed, including the previously failing reload test and PostgreSQL immutability trigger test. SQLite saved-study regressions: 3 passed. Ruff lint/format and patch whitespace checks passed. The disposable PostgreSQL instance was stopped after verification; no hosted pipeline rerun is claimed.

## SQLite contention and study-save consistency — 2026-09-20

- Full SQLite backend regression: 102 passed, one PostgreSQL-only skip. Seven added cases cover a reader snapshot surviving a concurrent commit, two competing updates accepting exactly one revision, saved-study insertion waiting for an edit or archive then rejecting the outdated source, API lock exhaustion rolling back with HTTP 503 and succeeding on retry, in-memory compatibility, and unrelated operational errors remaining server errors. Original revision and baseline snapshots remain unchanged.
- All seven Playwright workflows passed using two workers (1.3 minutes). The captured server log contained no SQLite lock or OperationalError messages. This checks the workload that previously showed contention; it does not guarantee unlimited concurrent writes.
- Ruff lint/format and patch whitespace checks passed. Frontend source and dependencies were unchanged, so unit/build checks were not rerun. PostgreSQL was not rerun; its existing row-lock path is unchanged.
- The local app was started, its mission-list endpoint was read successfully, and the database journal mode was verified as WAL. No user mission records were edited. The connection policy requires no table migration. SQLite still has a single writer; bounded waiting, explicit retry responses and backup constraints are documented in `docs/architecture/sqlite-concurrency.md`.
- Specification version 0.10.2 adds MF-NFR-REL-005 and matching traceability. Saved-study revision/archive checks now run under a SQLite write reservation; no engineering action is automatically replayed.

## Business-logic sanity fixes — 2026-09-19

- Full SQLite backend regression: 95 passed, one PostgreSQL-only skip.
- Added 12 passing backend regression cases for pending-proposal selection blocking without revision changes, successful subsequent approval, custom component replacements entering impact review and recalculation, stage-label/phase/content mismatches, and malformed interface endpoint rejection with safe legacy evaluation.
- Frontend unit tests: 22 passed. All seven browser workflows passed; the interface workflow now checks the pending-proposal notice and disabled selection before approving the unchanged proposal.
- The parallel browser run logged transient SQLite database-lock errors while using the shared browser-test database, although every workflow passed. SQLite contention remains a separate limitation; these fixes do not change persistence concurrency or claim to resolve that behavior.
- Ruff lint/format, TypeScript/Vite production build, Prettier and patch whitespace checks passed. The local app was restarted and its read-only scenario endpoint checked. PostgreSQL was not rerun, and no user mission data was edited.
- Requirements clarification version 0.10.1 updates MF-AGT-004, MF-MDL-009 and MF-TRD-007 with corresponding traceability. No schema migration or dependency change was needed.

## Declared data-interface consistency — 2026-09-18

- Full SQLite backend regression: 83 passed, one PostgreSQL-only skip. Four new tests cover reviewed contract edits, compatible rate units, missing declarations, protocol/rate/endpoint failures, stale dependencies, selection guards, outstanding baseline evidence and unchanged historical exports.
- Frontend unit tests: 22 passed. All seven browser workflows passed, including approval while paused, stale-result hiding, failed-rate selection blocking and correction using compatible units. The interface-check screenshot was visually inspected.
- Ruff lint/format, TypeScript/Vite production build, Prettier and patch whitespace checks passed. The local app was restarted and the API's DataContract schema verified. No database migration or new dependency was required; PostgreSQL was not rerun.
- Requirements version 0.10 adds MF-ARC-010–013 and updates traceability. Checks validate declared shared point-to-point data contracts only; physical interface verification remains deferred. Existing user missions were not edited during verification.

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
