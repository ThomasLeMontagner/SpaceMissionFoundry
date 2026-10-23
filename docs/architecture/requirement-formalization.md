# Owner-guided requirement formalization

The Requirements readiness endpoint is read-only. It reports accepted/stale requirements, existing criteria, owner-assessed scope and recorded clarification history. A deterministic parser suggests only a literal acquisition-to-delivery deadline with its source phrase. It does not derive arbitrary requirements or call an LLM.

Clarification notes are immutable AgentRun records labeled `requirement-formalization` and `owner-guided; no model call`. Replies link to the previous note without replacing it. They bind to the complete source requirement snapshot; stale-source replies are rejected. Ten current threads are allowed per source requirement. Notes use ordinary revision-checked store transactions and baseline/archive/pending-proposal guards.

Formalization creates an ordinary human design-change proposal. Accepted requirements remain unchanged until approval. Current leaf notes are automatically linked as evidence; unanswered questions prevent full coverage. Full coverage also requires a supported criterion and explicit confirmation. Approval uses the existing invalidation and recalculation workflow.

Scope metadata captures the exact statement, criterion, coverage, basis, outstanding questions and clarification references. The shared verification evaluator preserves numerical failures but changes a numeric pass to unverified for partial or obsolete scope. Consequently strict mission-check alternatives cannot treat a partial pass as fulfillment of a mandatory requirement. Owner assessment does not establish the scientific adequacy of the criterion. Legacy criteria without metadata retain previous semantics, explicitly labeled unassessed.

No migration or provider configuration is needed. General AI requirement derivation, multiple criteria per requirement and independent semantic scope validation remain outside this slice.

## Bounded AI assistance (v0.22)

`requirement-collaboration` AgentRun records are separate from immutable owner-guided notes. The run snapshots one accepted/stale requirement and the current clarification history. Mission questions pause for owner answers; Systems selects only a catalogue key, never numerical values. The catalogue contains accepted criteria, literal deadline extraction, and optional typed owner criteria with provenance. A separate reviewer sees the proposal, source statement, catalogue and answers, then recommends submit/revise/clarify. Simulation is explicitly labeled and does not interpret free-text intent.

Tasks are manually advanced, with a persisted claim and conservative token reservation before any provider call. Completion checks the attempt identity, lease, unchanged source, mission pause/archive/baseline and pending proposals. Failed calls retain unknown usage and require explicit retry; expired working claims can be recovered after two minutes. Recovery fences late responses and preserves previous completed task results. Three answer rounds, ten attempts and whole-run token/cost/elapsed limits bound work. No durable automatic scheduler is added.

Submission rechecks the requirement and clarification history. A favorable review and a supported selection create an ordinary partial formalization proposal atomically with the run's submission marker and event; the run is linked as proposal evidence. Source clarification questions answered within the run are linked to those recorded answers. Generic approval/invalidation/recalculation is unchanged. Independent review means a separate call and role contract; it may use the same configured model. Context and provider responses are bounded and validated; oversized contexts fail safely. General autonomous derivation and semantic completeness validation remain unsupported.

## Explicit automatic progression (v0.23)

The run endpoint persists an exclusive execution ID and two-minute lease before scheduling a background worker. A worker processes at most three remaining role tasks and never crosses an owner clarification boundary, submits a proposal or approves one. Every task retains the existing provider, source, budget, attempt and task-lease checks. Starting a task renews the execution lease. Manual tasks, answers and submission reject active automatic ownership; revision-checked saves prevent duplicate claims.

Pause and cancellation stop the execution claim. Completion checks both task and execution identities, status and leases, fencing late responses even after rapid pause/resume. Unknown usage reservations remain accounted. Exceptions stop the worker without retries. Bookkeeping writes preserve unrelated pending proposal target revisions; competing writes are never overwritten.

Explicit recovery can clear an expired idle claim while preserving ready, awaiting-answers or review-ready state. No call acknowledgement is needed for an idle checkpoint. Failed or interrupted live tasks still require acknowledgement of uncertain charges. Recovery never starts work itself. Historical manual runs with no execution metadata remain supported. A server restart does not reschedule workers; this is bounded background progression rather than a general durable job scheduler.

## Source-bound decomposition (v0.24)

The requirement run's optional `study` is `formalization` (legacy default) or `decomposition`. Both modes share role stages, budgets, exclusive automatic progression, task leases, clarification rounds, review and human submission gates. Decomposition returns a strict two-to-five-child contract. Each child quotes a substring of the parent title or a recorded owner answer, references an existing criterion catalogue key or null, and records rationale plus unresolved obligations. Exact-source and distinct-statement validation runs before review and again at submission. Simulation supports literal delivery-deadline separation only; live mode uses three separate bounded provider calls.

A new `requirement decomposition` proposal adds Requirements owned by Systems; it never replaces the parent. The protocol validates the unchanged parent snapshot, completed independent review, single referenced run, exact reviewed child operations and one child set per parent. Child priority is inherited, coverage is partial, and relations identify both the parent and source run. Approval revalidates the same contract, creates all children atomically and requires recalculation when analyses exist. Rejection and challenge create no entities; revision snapshots preserve history.

Existing requirement evaluation treats children independently. Missing criteria and partial coverage remain unverified, and no child-to-parent pass aggregation is introduced. Source quotation proves provenance, not semantic adequacy, independence or complete coverage; independent review and owner approval assess those limitations. Later parent edits invalidate dependent children through existing traceability. General requirement synthesis, recursive automatic decomposition and multiple competing accepted decompositions are outside this slice.

## Advisory quality checks (v0.25)

The existing read-only readiness endpoint includes a `quality` report computed from the same model snapshot. Stable finding IDs combine entity ID and check code; the report carries its source revision. The UI isolates mission/revision responses and offers type filters and navigation to affected requirements. There are no new writes, migrations or provider calls.

Active accepted/stale requirements and objectives are checked using exact derivation IDs, iterative graph reachability, whitespace/case-normalized duplicate titles, a small explicit English wording lexicon and conjunction pattern, and existing typed criterion/scope validators. Proposed/rejected records are excluded. Cycles are reported only for their members; objective support is structural reachability, not adequacy. Criterion support and owner scope are distinct from calculated pass/fail evidence. These checks do not detect all semantic contradictions, solution bias, overlaps or omissions and do not gate approvals. Parent derivations can be corrected through the reviewed editor described below. Other relationship types remain outside that editor.

## Reviewed parent links (v0.26)

`EditChanges.parent_ids` exposes a bounded replacement set, retaining non-derivation relations. The existing design-change proposal and decision workflow provides revision, pending-proposal, archive and baseline guards. `requirement_links.validate_links` validates the complete proposed graph at both submission and acceptance, including multi-operation cycles; unchanged legacy links are tolerated so unrelated repairs remain possible. Accepted/stale parents are allowed, as are active parents introduced within the same validated proposal.

Changing parent IDs produces a partial formalization bound to the unchanged/current statement and criterion, with an explicit applicability question. Protocol validation rejects attempts to bypass this reassessment. Existing invalidation and impact/recalculation behavior applies to replacement requirements. Decomposition metadata retains the original derivation source for audit, independently of current parent links. No criterion inference, semantic sufficiency or parent verification aggregation is introduced.
