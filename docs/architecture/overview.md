# Architecture and implementation plan

Delivery sensitivity studies run as read-only calculations over the current recorded delivery evidence, including saved baselines. One parameter varies per study; data, RF and delivery tools rerun for each case. Results remain outside mission history and may be exported as JSON or saved to a separate immutable study table. The saved-study library supports historical retrieval and comparison. See [sensitivity architecture and limits](sensitivity-analysis.md).

## Vertical slice

Point-to-point data interfaces now support reviewed structured protocol/rate declarations and deterministic consistency checks. Evidence participates in dependency invalidation and selection/baseline guards; missing declarations remain explicitly unverified. See [interface checks and limitations](interface-checks.md).

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

### Quantitative requirement verification

Optional `Requirement.data.criterion` stores a validated metric, inclusive comparator and unit-bearing threshold. `GET /api/requirement-metrics` supplies the closed output registry to the editor. The requirement-check service evaluates recorded AnalysisRun outputs per candidate after recalculation and at baseline creation. It writes VerificationItems with `verifies` and `evidenced_by` relations, criterion snapshots, converted actual values and revision provenance. Existing transitive invalidation marks these checks stale when their evidence or requirement changes. Missing/invalid evidence is unverified; signed output margins are supported.

Selection and baseline guards recompute must-priority checks from current evidence, so clients cannot bypass a failing criterion by submitting an old status. Unverified requirements and failing lower-priority criteria remain explicit outstanding obligations in conceptual baseline approval. Requirement approval is separate from calculated status. Old snapshots need no migration and their exports remain immutable; absent criteria mean unverified. Statement-to-metric semantic validation and automatic numerical extraction remain deferred.

### Baseline comparison

The workbench loads available baseline IDs and obtains both selected snapshots from the existing mission-scoped JSON export endpoint. A pure comparison function checks mission identity, compares mission-level fields, entities and proposals by stable IDs, and recursively identifies changed fields. It preserves quantities as value/unit pairs and arrays as complete stored lists. Object key ordering and typed relation ordering do not cause false differences. Added and removed objects retain their complete visible content.

The default view excludes top-level creation/modification/revision metadata and direct calculation provenance fields in entity data; a checkbox includes them. Request generations prevent late responses from replacing a newer selection or another mission's view. All state is local to the comparison component. No new API mutation or database migration is introduced. Detailed revision-to-revision comparison, normalized unit equivalence and downloadable diff reports remain outside this milestone.

### Preliminary coverage and access

The new `access` tool uses accepted mission geometry plus altitude from the existing orbit input group. New architecture proposals include explicit access assumptions; existing missions opt in through `initialize-access`, which proposes the new group for approval. Recalculation records a mission-level AnalysisRun, claims, sampled ground track, point-target windows, station windows and union contact summaries. Three finite-horizon metrics are available to the requirement evaluator. The workbench hides stale/invalid geometry and supports editing signed coordinates and named site lists. Selection/review evidence references include access results when present.

This does not substitute geometric contact for usable link-budget contact or verify delivery latency. Both reference candidates share the same declared orbit and footprint. See [access method, limits and analytic validation](access-analysis.md) and the [input schema](access-inputs.schema.json). No external orbital library or database migration is required.

The delivery calculator consumes recorded access windows, accepted payload/link inputs, RF results and approved delay parameters. It records a finite-horizon FIFO product simulation per candidate; explicit latency criteria evaluate all products rather than only successful deliveries. The Data delivery view hides stale/invalid results and links to input/evidence inspection. Legacy setup uses a reviewed proposal, and baseline history remains immutable. See [delivery assumptions and deadline semantics](delivery-analysis.md).

### Reversible mission archiving

The model has a backward-compatible `archived` flag, defaulting to false for older snapshots. `GET /missions` lists active missions; `?archived=true` lists archived missions. `POST /missions/{id}/archive` accepts the expected revision and desired boolean state. A change appends an audited model revision without modifying baseline rows or prior snapshots. Pending proposal target revisions advance with this organizational change so restoring a mission does not make its approvals unusable.

Archived missions remain readable through history and baseline export endpoints. Workflow mutation guards, baseline reopening and historical revision restoration reject archived missions until explicitly restored to the active list. Archive/restore preserves phase and pause state and uses the existing optimistic concurrency transaction. No database migration, history deletion or permanent delete endpoint is introduced. The UI confirms archiving and offers restoration from the archived list.
