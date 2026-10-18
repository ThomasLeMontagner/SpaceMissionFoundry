# Owner-guided requirement formalization

The Requirements readiness endpoint is read-only. It reports accepted/stale requirements, existing criteria, owner-assessed scope and recorded clarification history. A deterministic parser suggests only a literal acquisition-to-delivery deadline with its source phrase. It does not derive arbitrary requirements or call an LLM.

Clarification notes are immutable AgentRun records labeled `requirement-formalization` and `owner-guided; no model call`. Replies link to the previous note without replacing it. They bind to the complete source requirement snapshot; stale-source replies are rejected. Ten current threads are allowed per source requirement. Notes use ordinary revision-checked store transactions and baseline/archive/pending-proposal guards.

Formalization creates an ordinary human design-change proposal. Accepted requirements remain unchanged until approval. Current leaf notes are automatically linked as evidence; unanswered questions prevent full coverage. Full coverage also requires a supported criterion and explicit confirmation. Approval uses the existing invalidation and recalculation workflow.

Scope metadata captures the exact statement, criterion, coverage, basis, outstanding questions and clarification references. The shared verification evaluator preserves numerical failures but changes a numeric pass to unverified for partial or obsolete scope. Consequently strict mission-check alternatives cannot treat a partial pass as fulfillment of a mandatory requirement. Owner assessment does not establish the scientific adequacy of the criterion. Legacy criteria without metadata retain previous semantics, explicitly labeled unassessed.

No migration or provider configuration is needed. General AI requirement derivation, multiple criteria per requirement and independent semantic scope validation remain outside this slice.
