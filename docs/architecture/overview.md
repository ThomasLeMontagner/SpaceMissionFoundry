# Architecture and implementation plan

## Vertical slice

1. Domain schema and proposal invariants.
2. Transactional SQL storage, revisions, relationships and migrations.
3. Unit-aware tools and fixed six-role reference workflow.
4. Human decision API, baseline exports and revision replay.
5. React engineering views, live progress and critical-action confirmation.
6. Negative governance tests, numerical tests, browser acceptance and traceability.

## Boundaries

`backend/app/domain`: Pydantic model, classifications, operations and proposal validation.
`backend/app/agents`: versioned role definitions and provider-neutral proposal interface.
`backend/app/engineering_tools`: fixed pure functions using Pint; no LLM arithmetic.
`backend/app/orchestration`: versioned reference inputs and deterministic scenario content.
`backend/app/services`: human gates and dependency-driven workflow transitions.
`backend/app/persistence`: SQLAlchemy transactional store, immutable snapshots and SQL relationships.
`backend/app/api`: authenticated FastAPI commands, queries and SSE.
`backend/app/reports`: JSON/CSV/Markdown derived from the exact baseline snapshot.
`frontend/src`: React/TypeScript workbench with object drilldown, proposals, human gates and replay.

## State and concurrency

One `missions` row points at the current JSON model. Each atomic transaction appends a full `revisions` snapshot and before/after event, and inserts that revision's typed relationships. An optimistic `UPDATE ... WHERE revision = expected` prevents lost concurrent updates on SQLite and PostgreSQL. Failed commands roll back the entire transaction. A repeated acceptance is rejected rather than creating duplicate objects.

PostgreSQL migration triggers reject UPDATE/DELETE on history, baseline and relationship tables. ORM listeners provide the same normal-application restriction in tests. Database administrators remain outside this trust boundary. Restoring a historical model appends a new current revision; baseline rows retain their original contents.

The proposal boundary enforces role/version, target revision, duplicate operations, reference validity, immutable object kinds, dimensional compatibility for parameters, supported classifications and human ownership. Tools alone create accepted calculation records. Independent review writes findings through a separate workflow branch and cannot submit design mutations.

## Engineering fidelity

Mass: sum CBE × (1 + contingency), compare to assumed allocation.
Power: weighted mode loads; sunlit generation versus whole-orbit demand; eclipse load versus usable battery energy.
Data: payload bit rate × daily observation seconds / assumed compression.
RF: free-space path loss, received carrier, Boltzmann noise density, Eb/N0 and required Eb/N0 margin. Downlink capacity is zero for a negative link margin; otherwise rate × contact seconds × efficiency.
Orbit: two-body circular period and beta-zero maximum eclipse angle using fixed SI Earth constants. No coverage, station access or end-to-end latency solution is implied.
Trade: transparent weighted sum of estimated 0–5 criterion scores. The arithmetic is deterministic; utility scores remain estimates.

## Honest simplifications

The workflow is a deterministic scenario harness, not free-form agent planning. Some system-generated records (runs, tool outputs, rule findings and trade calculations) are inserted by trusted services; agent-proposed requirements and architecture pass through human-accepted proposals. The initial extraction is a fixed reference scope confirmation. Generic entity payload dictionaries retain future extensibility but need more discriminated payload schemas before broad external proposal access.

The design has one human owner. Authentication gates all private data with one configured token. Separate missions are scoped in every API query but share that owner; no multi-tenant privacy promise is made. Short phases are serialized by explicit user advances and revision checks; there is no distributed job queue.

## Editable engineering model (2026-09-13)

Nine accepted Parameter groups hold common orbit inputs and mass/power/data/link inputs for both candidates. `domain/engineering_inputs.py` validates exact payload shapes, finite quantities, Pint-compatible dimensions, fractions and mode sums. Only the scenario proposal seeds defaults. `services/design_inputs.py` reads accepted model inputs; orbit period/eclipse and payload demand are injected from deterministic upstream outputs.

Human edits create restricted replacement proposals, retaining identifiers and original units. Acceptance marks transitive dependents stale. The workbench then requests recalculation automatically, unless paused or impact review is required. Acceptance and recalculation are distinct committed revisions, so both the stale checkpoint and new outputs are replayable. API clients perform `POST /objects/{id}/edit`, approve the returned proposal, then call `POST /advance` when its phase is `Recalculation required`. No background job or hidden model mutation is implied.

Changed assumptions/requirements may stale narrative design objects and input groups. The `review-impact` command requires explicit confirmation and rationale; it reaffirms those objects without declaring their calculations valid. Recalculation updates all preliminary budgets, rebuilds trade scores from current capacity compliance, reopens violated rule findings, supersedes stale selection/review artifacts, and requires a fresh selection and independent review. Stale or failed budgets block selection and baseline approval.

Reopening appends a new revision with `derived_from_baseline`; it never updates baseline rows. `GET /baselines` lists all immutable snapshots for a mission, and exports accept a mission-scoped `baseline_id`. Existing v1 snapshots remain readable. Optional model fields need no SQL migration; legacy input initialization is an explicit, approved proposal reconstructed from recorded analyses.

Limitations: the complete small calculation set is rerun rather than scheduling only affected tools. Power operational mode fractions and payload data observation duty remain distinct explicit assumptions. Requirement prose is not interpreted into numerical limits; the owner must review and edit the applicable quantities. General schema-free mission generation and high-fidelity access/latency analysis remain deferred.
