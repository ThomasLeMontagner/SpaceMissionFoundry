# ADR 004: Explicit model inputs and revisioned design iteration

Accepted, 2026-09-13. Represent editable calculator inputs as typed Parameter groups and keep derived inputs tool-owned. Human changes are proposals and do not mutate accepted values until approval. Record approval/invalidation and recalculation as separate revisions; the UI automatically requests the latter when no human impact gate or pause blocks it.

Recalculate the whole small reference analysis set for predictable ordering. Mark downstream selections and review artifacts stale, preserve them through history, and require renewed selection/review before a second baseline. Reaffirming narrative content is a distinct human decision, never a claim that numerical feasibility is proven.

Reopen baselines into new working revisions. Retain every baseline row and expose mission-scoped historical exports. For older models, reconstruct inputs explicitly from saved executions through approval, never silent defaults. No database rewrite or migration of immutable snapshots is needed.
