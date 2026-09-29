# Bounded agent collaboration

The first slice negotiates one candidate's observation duty fraction. It runs five explicit tasks: Payload proposal, data/link evaluation, Bus & Ground response, fresh evaluation, Systems submission. The two discipline proposals may come from an OpenAI-compatible model; tool results and Systems submission are deterministic. The default simulation supplies labeled scripted proposals. A passing data/link check does not establish science adequacy, coverage, delivery deadlines or whole-mission feasibility.

## Execution and persistence

`POST /api/missions/{id}/collaboration` starts a run. Revision-checked `/collaboration/{run}/step` executes one task; `/cancel` cancels active work. Each run is an `AgentRun` entity in the existing atomic revision snapshots, requiring no table migration. Its stable UUID scopes task names and ordered, uniquely identified events. Events retain sender, recipient, preceding exchange ID, affected input ID, source revision, timestamp, concise summary and available evidence. SSE revision notifications refresh the displayed run; refreshes reconstruct the same event IDs rather than append duplicate messages. Historical snapshots retain original activity.

The task-start revision is saved before any provider call. Completion re-reads the mission and checks the active attempt, cancellation, archive/baseline state and a fingerprint of engineering source objects. Changed sources discard results as stale. Concurrent saves use the Store's compare-and-swap protection. A server crash or losing completion write leaves visibly interrupted work; cancel and start a new run. There is no automatic retry or background resumption. Ten task attempts bound each round; at most three revision rounds follow the initial round.

Mission pause prevents the next task; it does not terminate an already-running HTTP call. Cancellation discards an in-flight result if its cancellation revision wins. During a pending browser request the local controls are busy; another session can pause/cancel, or the user can refresh to recover interrupted work. Baselines require active runs to be finished or cancelled. Historical and baselined records are read-only under existing guards.

## Proposal safety

The provider contract accepts only a finite duty fraction in [0,1] and a short rationale. It cannot supply tool results or arbitrary model operations. Bus & Ground receives the recorded Payload proposal and calculator outputs. Systems only submits when the revised data and link checks pass, using normal proposal validation and linking the run as evidence. Approval is a separate human action; challenge/reject/accept decisions are recorded in the timeline. Accepted changes follow the existing invalidation and recalculation flow. A response equal to the accepted duty completes without a proposal.

Live mode is explicit and requires backend provider configuration. Its provider model is recorded and must remain unchanged during the run. Calls have a 30-second timeout, JSON response contract, bounded context and 1,024 output tokens. A conservative per-call cost preflight uses configured EUR prices; this is not a cumulative run budget or billing guarantee. Provider-reported tokens are shown in evidence when available, otherwise unknown; billed cost is unknown. Simulation records zero model tokens/cost. Error events omit raw provider exceptions and credentials. Tests use mocked HTTP, never paid models.

## Remaining scope

This is not autonomous mission design from arbitrary briefs. Independent Systems model review, generalized clarification/replanning, broader design parameters, a scheduler, task reassignment, generalized disagreements, full dependency-graph semantics and aggregate accounting remain future work. Current task cards and timeline cover only this duty negotiation. Historical evidence is available through existing revision replay and run inspection; the collaboration view does not yet provide an interactive historical playback control.

## Interaction graph

The workbench builds a directed graph from the selected run’s recorded sender/recipient pairs. Counts represent persisted events, not fabricated messages or task-completion percentages. Historical `evaluate_*` recipients map to Engineering tools. Configured roles with no events remain visible with zero counts; no unrecorded connections are drawn. The current role needing attention is highlighted only for active or blocked runs, with explicit pause and simulation/live labels. Terminal runs show recorded activity.

Selecting a role or connection filters the timeline and clears other filters. The filter is scoped to its run and recomputed as new events arrive. Numbered connections and role nodes support keyboard Enter/Space activation, accessible labels and selection state. Timeline entries retain affected-input inspection and expandable evidence. Historical failed tool results do not imply unresolved disagreements; generalized conflict resolution and planned dependencies are not inferred from message order.

## Clarification and revision

`POST /api/missions/{id}/collaboration/{run}/clarify` accepts a revision, feedback (3–2,000 characters) and optional minimum duty fraction in [0,1]. It is available for a challenged collaboration proposal or a blocked negotiation. Source fingerprints, archive/baseline guards, other pending proposals and other active runs are checked before saving. A new round atomically supersedes the challenged proposal, archives the previous responses and calculations in the run, records a clarification event and resets the five tasks. Existing historical snapshots are unchanged. A maximum of three revision rounds prevents unbounded cycling; requests execute no provider call themselves.

Both discipline agents receive clarification history, the challenge reason, previous Bus response and the numeric minimum. The simulation honors the minimum through deterministic proposals and explicitly does not interpret free text. Fresh calculations must pass, and Systems separately checks the final duty against the owner minimum before submission. This constraint applies to this collaboration, not to accepted mission requirements or science verification. Blank minimum retains the previous value; an explicit zero relaxes a prior positive minimum. If it is infeasible, the run remains blocked for human clarification instead of silently relaxing it. All revised proposals require normal human approval. Superseded proposals cannot be accepted.

Revision events carry a round number (older events display round zero). Timeline and graph retain events across rounds; task progress describes only the current round. Paused missions may record clarification but cannot execute tasks until resumed. Changed design inputs require a new collaboration rather than reusing old tool evidence. Aggregate cost limits remain deferred; per-call preflights and explicit task execution still apply in live mode.
