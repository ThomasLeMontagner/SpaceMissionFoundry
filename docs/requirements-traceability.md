# MVP requirements traceability

Aligned with specification version 0.6. **Implemented** refers to the reference vertical slice, not universal mission support. **Partial** explicitly denotes an incomplete requirement. **Deferred** is outside this delivered slice. This is not a claim that all Must requirements are met.

Evidence: `backend/tests/test_workflow.py`, `backend/tests/test_tools.py`, `frontend/src/App.test.tsx`, `frontend/tests/workflow.spec.ts`, versioned scenario exports, source inspection. Execution results are recorded separately in `docs/validation.md`.

| ID | Status | Scope / evidence |
|---|---|---|
| MF-MIS-001 | Implemented | Fixed reference scope confirmation; general extraction and clarification editing incomplete. |
| MF-MIS-002 | Partial | Fixed reference scope confirmation; general extraction and clarification editing incomplete. |
| MF-MIS-003 | Partial | Fixed reference scope confirmation; general extraction and clarification editing incomplete. |
| MF-MIS-004 | Partial | Fixed reference scope confirmation; general extraction and clarification editing incomplete. |
| MF-MIS-005 | Partial | Fixed reference scope confirmation; general extraction and clarification editing incomplete. |
| MF-MIS-006 | Implemented | Fixed reference scope confirmation; general extraction and clarification editing incomplete. |
| MF-MIS-007 | Implemented | Unit-bearing editable calculator inputs preserve original values and compatible units; test_iteration.py tests percent and seconds. |
| MF-MIS-008 | Partial | Fixed reference scope confirmation; general extraction and clarification editing incomplete. |
| MF-MIS-009 | Deferred | Fixed reference scope confirmation; general extraction and clarification editing incomplete. |
| MF-MIS-010 | Implemented | Archive actions in saved-mission list and workspace, archived list and restore action; browser regression. Permanent deletion is not provided. |
| MF-MIS-011 | Implemented | Revision-checked audit events, archived edit guards, preserved baseline/revision exports and resumable pending approvals; test_archive.py. |
| MF-AGT-001 | Implemented | Dependency-ordered mock roles; real adapter rationale-only; no durable jobs or general agent negotiation. |
| MF-AGT-002 | Implemented | Dependency-ordered mock roles; real adapter rationale-only; no durable jobs or general agent negotiation. |
| MF-AGT-003 | Partial | Dependency-ordered mock roles; real adapter rationale-only; no durable jobs or general agent negotiation. |
| MF-AGT-004 | Implemented | Dependency-ordered mock roles; real adapter rationale-only; no durable jobs or general agent negotiation. |
| MF-AGT-005 | Implemented | Dependency-ordered mock roles; real adapter rationale-only; no durable jobs or general agent negotiation. |
| MF-AGT-006 | Partial | Dependency-ordered mock roles; real adapter rationale-only; no durable jobs or general agent negotiation. |
| MF-AGT-007 | Partial | Dependency-ordered mock roles; real adapter rationale-only; no durable jobs or general agent negotiation. |
| MF-AGT-008 | Implemented | Dependency-ordered mock roles; real adapter rationale-only; no durable jobs or general agent negotiation. |
| MF-AGT-009 | Implemented | Dependency-ordered mock roles; real adapter rationale-only; no durable jobs or general agent negotiation. |
| MF-AGT-010 | Partial | Dependency-ordered mock roles; real adapter rationale-only; no durable jobs or general agent negotiation. |
| MF-AGT-011 | Partial | Human edit proposals, before/after inspection, acceptance/rejection/challenge; general agent counter-proposals deferred. |
| MF-AGT-012 | Partial | Dependency-ordered mock roles; real adapter rationale-only; no durable jobs or general agent negotiation. |
| MF-AGT-013 | Deferred | Dependency-ordered mock roles; real adapter rationale-only; no durable jobs or general agent negotiation. |
| MF-AGT-014 | Deferred | Dependency-ordered mock roles; real adapter rationale-only; no durable jobs or general agent negotiation. |
| MF-AGT-015 | Partial | Dependency-ordered mock roles; real adapter rationale-only; no durable jobs or general agent negotiation. |
| MF-MDL-001 | Implemented | Common typed entity metadata and selected required payload fields; generic engineering dictionaries remain. |
| MF-MDL-002 | Partial | Common typed entity metadata and selected required payload fields; generic engineering dictionaries remain. |
| MF-MDL-003 | Partial | Common typed entity metadata and selected required payload fields; generic engineering dictionaries remain. |
| MF-MDL-004 | Implemented | Common typed entity metadata and selected required payload fields; generic engineering dictionaries remain. |
| MF-MDL-005 | Implemented | Common typed entity metadata and selected required payload fields; generic engineering dictionaries remain. |
| MF-MDL-006 | Implemented | Common typed entity metadata and selected required payload fields; generic engineering dictionaries remain. |
| MF-MDL-007 | Implemented | Common typed entity metadata and selected required payload fields; generic engineering dictionaries remain. |
| MF-MDL-008 | Implemented | Common typed entity metadata and selected required payload fields; generic engineering dictionaries remain. |
| MF-MDL-009 | Implemented | Transitive invalidation, human impact review and recalculation of the reference model; test_iteration.py. |
| MF-MDL-010 | Deferred | Common typed entity metadata and selected required payload fields; generic engineering dictionaries remain. |
| MF-MDL-011 | Deferred | Common typed entity metadata and selected required payload fields; generic engineering dictionaries remain. |
| MF-REQ-001 | Implemented | Reference requirement hierarchy and approval gates; general linting and coverage evaluator deferred. |
| MF-REQ-002 | Partial | Reference requirement hierarchy and approval gates; general linting and coverage evaluator deferred. |
| MF-REQ-003 | Implemented | Reference requirement hierarchy and approval gates; general linting and coverage evaluator deferred. |
| MF-REQ-004 | Partial | Reference requirement hierarchy and approval gates; general linting and coverage evaluator deferred. |
| MF-REQ-005 | Partial | Reference requirement hierarchy and approval gates; general linting and coverage evaluator deferred. |
| MF-REQ-006 | Implemented | Reference requirement hierarchy and approval gates; general linting and coverage evaluator deferred. |
| MF-REQ-007 | Implemented | Reference requirement hierarchy and approval gates; general linting and coverage evaluator deferred. |
| MF-REQ-008 | Implemented | Reference requirement hierarchy and approval gates; general linting and coverage evaluator deferred. |
| MF-REQ-009 | Partial | Existing requirements can be edited through reviewed replacement proposals with history. Manual creation remains deferred. |
| MF-REQ-010 | Partial | Reference requirement hierarchy and approval gates; general linting and coverage evaluator deferred. |
| MF-REQ-011 | Implemented | Typed criterion, closed metric registry, unit conversion and invalid-input tests. |
| MF-REQ-012 | Implemented | Per-candidate VerificationItems link requirements and AnalysisRuns with criterion, actual value and revision provenance. |
| MF-REQ-013 | Implemented | Pass/fail/stale/unverified checks; transitive invalidation and recalculation regression tests. |
| MF-REQ-014 | Implemented | Must-priority failures/stale checks block selection and baseline; outstanding obligations recorded in approval. |
| MF-REQ-015 | Implemented | Reviewed criterion editor, per-candidate evidence navigation, immutable export and criterion-removal tests. |
| MF-ARC-001 | Partial | Reference functional/physical records and interface drilldown; no general compatibility engine. |
| MF-ARC-002 | Partial | Reference functional/physical records and interface drilldown; no general compatibility engine. |
| MF-ARC-003 | Partial | Reference functional/physical records and interface drilldown; no general compatibility engine. |
| MF-ARC-004 | Partial | Reference functional/physical records and interface drilldown; no general compatibility engine. |
| MF-ARC-005 | Deferred | Reference functional/physical records and interface drilldown; no general compatibility engine. |
| MF-ARC-006 | Implemented | Reference functional/physical records and interface drilldown; no general compatibility engine. |
| MF-ARC-007 | Implemented | Reference functional/physical records and interface drilldown; no general compatibility engine. |
| MF-ARC-008 | Partial | Reference functional/physical records and interface drilldown; no general compatibility engine. |
| MF-ARC-009 | Deferred | Reference functional/physical records and interface drilldown; no general compatibility engine. |
| MF-ANL-001 | Implemented | Tested resource budgets and circular orbit; sampled point coverage/station access added. Full regional coverage, operational latency and lifetime remain unverified. |
| MF-ANL-002 | Implemented | Versioned executions record accepted inputs/units, source revision, elapsed time, outputs and failures; test_iteration.py. |
| MF-ANL-003 | Implemented | Tested resource budgets and circular orbit; sampled point coverage/station access added. Full regional coverage, operational latency and lifetime remain unverified. |
| MF-ANL-004 | Implemented | Tested resource budgets and circular orbit; sampled point coverage/station access added. Full regional coverage, operational latency and lifetime remain unverified. |
| MF-ANL-005 | Implemented | Tested resource budgets and circular orbit; sampled point coverage/station access added. Full regional coverage, operational latency and lifetime remain unverified. |
| MF-ANL-006 | Partial | Tested resource budgets and circular orbit; sampled point coverage/station access added. Full regional coverage, operational latency and lifetime remain unverified. |
| MF-ANL-007 | Implemented | Tested resource budgets and circular orbit; sampled point coverage/station access added. Full regional coverage, operational latency and lifetime remain unverified. |
| MF-ANL-008 | Implemented | Tested resource budgets and circular orbit; sampled point coverage/station access added. Full regional coverage, operational latency and lifetime remain unverified. |
| MF-ANL-009 | Deferred | Tested resource budgets and circular orbit; sampled point coverage/station access added. Full regional coverage, operational latency and lifetime remain unverified. |
| MF-ANL-010 | Deferred | Tested resource budgets and circular orbit; sampled point coverage/station access added. Full regional coverage, operational latency and lifetime remain unverified. |
| MF-ANL-011 | Partial | Tested resource budgets and circular orbit; sampled point coverage/station access added. Full regional coverage, operational latency and lifetime remain unverified. |
| MF-ANL-012 | Partial | Tested resource budgets and circular orbit; sampled point coverage/station access added. Full regional coverage, operational latency and lifetime remain unverified. |
| MF-ANL-013 | Implemented | Validated geometry and named point/station inputs, bounded circular propagation and analytic reference tests. |
| MF-ANL-014 | Implemented | Sampled observation/visibility windows, finite-horizon gaps, repeated-window revisit and union network contact; test_access.py. |
| MF-ANL-015 | Implemented | Explicit sampling/censoring/model limits; latency remains unverified and approved link-contact assumptions remain unchanged. |
| MF-ANL-016 | Implemented | Ground-track/window view, approved legacy initialization, stale/failure hiding, evidence and immutable-baseline tests. |
| MF-ANL-017 | Implemented | engineering_tools/delivery.py; analytical fragmented-contact, FIFO, storage overflow, RF gate and delay tests in test_delivery.py. |
| MF-ANL-018 | Implemented | Recorded per-product events, pending/dropped totals, queue trace, conservation tests and explicit model limits; docs/architecture/delivery-analysis.md. |
| MF-ANL-019 | Implemented | Explicit delivery.maximum_latency criterion; per-product deadline evaluation and selection/baseline guards. Missing or censored evidence never produces a full-workload pass. Operational validation remains outstanding. |
| MF-ANL-020 | Implemented | DeliveryView.tsx, legacy initialization approval, transitive evidence invalidation and regression tests; immutable baseline storage retained. |
| MF-EVD-001 | Partial | Assumptions and deterministic provenance; no external evidence ingestion or contradiction engine. |
| MF-EVD-002 | Partial | Assumptions and deterministic provenance; no external evidence ingestion or contradiction engine. |
| MF-EVD-003 | Implemented | Assumptions and deterministic provenance; no external evidence ingestion or contradiction engine. |
| MF-EVD-004 | Implemented | Assumptions and deterministic provenance; no external evidence ingestion or contradiction engine. |
| MF-EVD-005 | Deferred | Assumptions and deterministic provenance; no external evidence ingestion or contradiction engine. |
| MF-EVD-006 | Implemented | Assumptions and deterministic provenance; no external evidence ingestion or contradiction engine. |
| MF-EVD-007 | Partial | Assumptions and deterministic provenance; no external evidence ingestion or contradiction engine. |
| MF-EVD-008 | Partial | Assumptions and deterministic provenance; no external evidence ingestion or contradiction engine. |
| MF-TRD-001 | Partial | Editable weights and deterministic totals over explicit estimated scores; no automatic sensitivity sweep. |
| MF-TRD-002 | Implemented | Editable weights and deterministic totals over explicit estimated scores; no automatic sensitivity sweep. |
| MF-TRD-003 | Partial | Editable weights and deterministic totals over explicit estimated scores; no automatic sensitivity sweep. |
| MF-TRD-004 | Implemented | Editable weights and deterministic totals over explicit estimated scores; no automatic sensitivity sweep. |
| MF-TRD-005 | Partial | Editable weights and deterministic totals over explicit estimated scores; no automatic sensitivity sweep. |
| MF-TRD-006 | Implemented | Editable weights and deterministic totals over explicit estimated scores; no automatic sensitivity sweep. |
| MF-TRD-007 | Implemented | Input changes stale dependent selection decisions and force recalculation and reselection; test_iteration.py. |
| MF-TRD-008 | Deferred | Editable weights and deterministic totals over explicit estimated scores; no automatic sensitivity sweep. |
| MF-REV-001 | Implemented | One concept review with seeded defect and verified evidence correction; no broad finding lifecycle editor. |
| MF-REV-002 | Partial | One concept review with seeded defect and verified evidence correction; no broad finding lifecycle editor. |
| MF-REV-003 | Implemented | One concept review with seeded defect and verified evidence correction; no broad finding lifecycle editor. |
| MF-REV-004 | Implemented | One concept review with seeded defect and verified evidence correction; no broad finding lifecycle editor. |
| MF-REV-005 | Partial | One concept review with seeded defect and verified evidence correction; no broad finding lifecycle editor. |
| MF-REV-006 | Partial | One concept review with seeded defect and verified evidence correction; no broad finding lifecycle editor. |
| MF-REV-007 | Partial | One concept review with seeded defect and verified evidence correction; no broad finding lifecycle editor. |
| MF-REV-008 | Implemented | One concept review with seeded defect and verified evidence correction; no broad finding lifecycle editor. |
| MF-CFG-001 | Implemented | Immutable snapshots, new-revision restore and object comparison; no branch merging. |
| MF-CFG-002 | Implemented | Immutable snapshots, new-revision restore and object comparison; no branch merging. |
| MF-CFG-003 | Implemented | Immutable snapshots, new-revision restore and object comparison; no branch merging. |
| MF-CFG-004 | Implemented | Revision replay comparison plus dedicated comparison of two immutable baselines, including directional field changes. |
| MF-CFG-005 | Implemented | Immutable snapshots, new-revision restore and object comparison; no branch merging. |
| MF-CFG-006 | Implemented | Immutable snapshots, new-revision restore and object comparison; no branch merging. |
| MF-CFG-007 | Implemented | Baseline selectors, directional object/field comparison, type and text filters; browser and unit regressions. |
| MF-CFG-008 | Implemented | Read-only snapshot exports, explicit audit metadata toggle, missing/null and identity tests, stale-request isolation, immutable-export browser checks. |
| MF-UI-001 | Partial | Workbench and object inspector; browser-tested primary flow; no formal accessibility certification. |
| MF-UI-002 | Partial | Workbench and object inspector; browser-tested primary flow; no formal accessibility certification. |
| MF-UI-003 | Partial | Workbench and object inspector; browser-tested primary flow; no formal accessibility certification. |
| MF-UI-004 | Implemented | Workbench and object inspector; browser-tested primary flow; no formal accessibility certification. |
| MF-UI-005 | Implemented | Workbench and object inspector; browser-tested primary flow; no formal accessibility certification. |
| MF-UI-006 | Implemented | Workbench and object inspector; browser-tested primary flow; no formal accessibility certification. |
| MF-UI-007 | Implemented | Workbench and object inspector; browser-tested primary flow; no formal accessibility certification. |
| MF-UI-008 | Implemented | Workbench and object inspector; browser-tested primary flow; no formal accessibility certification. |
| MF-UI-009 | Partial | Workbench and object inspector; browser-tested primary flow; no formal accessibility certification. |
| MF-UI-010 | Implemented | Workbench and object inspector; browser-tested primary flow; no formal accessibility certification. |
| MF-UI-011 | Implemented | Workbench and object inspector; browser-tested primary flow; no formal accessibility certification. |
| MF-UI-012 | Partial | Workbench and object inspector; browser-tested primary flow; no formal accessibility certification. |
| MF-UI-013 | Partial | Workbench and object inspector; browser-tested primary flow; no formal accessibility certification. |
| MF-UI-014 | Deferred | Workbench and object inspector; browser-tested primary flow; no formal accessibility certification. |
| MF-IO-001 | Implemented | Baseline JSON/Markdown/CSV export; general import deferred. |
| MF-IO-002 | Implemented | Baseline JSON/Markdown/CSV export; general import deferred. |
| MF-IO-003 | Implemented | Baseline JSON/Markdown/CSV export; general import deferred. |
| MF-IO-004 | Implemented | Baseline JSON/Markdown/CSV export; general import deferred. |
| MF-IO-005 | Deferred | Baseline JSON/Markdown/CSV export; general import deferred. |
| MF-IO-006 | Implemented | Baseline JSON/Markdown/CSV export; general import deferred. |
| MF-IO-007 | Deferred | Baseline JSON/Markdown/CSV export; general import deferred. |
| MF-EVL-001 | Implemented | Versioned deterministic scenario and full replay; aggregate quality/cost metrics incomplete. |
| MF-EVL-002 | Implemented | Versioned deterministic scenario and full replay; aggregate quality/cost metrics incomplete. |
| MF-EVL-003 | Implemented | Versioned deterministic scenario and full replay; aggregate quality/cost metrics incomplete. |
| MF-EVL-004 | Partial | Versioned deterministic scenario and full replay; aggregate quality/cost metrics incomplete. |
| MF-EVL-005 | Implemented | Versioned deterministic scenario and full replay; aggregate quality/cost metrics incomplete. |
| MF-EVL-006 | Deferred | Versioned deterministic scenario and full replay; aggregate quality/cost metrics incomplete. |
| MF-EVL-007 | Partial | Versioned deterministic scenario and full replay; aggregate quality/cost metrics incomplete. |
| MF-NFR-REL-001 | Implemented | See architecture and README limitations; local single-owner reference workflow only. |
| MF-NFR-REL-002 | Implemented | See architecture and README limitations; local single-owner reference workflow only. |
| MF-NFR-REL-003 | Partial | See architecture and README limitations; local single-owner reference workflow only. |
| MF-NFR-REL-004 | Partial | See architecture and README limitations; local single-owner reference workflow only. |
| MF-NFR-AUD-001 | Implemented | See architecture and README limitations; local single-owner reference workflow only. |
| MF-NFR-AUD-002 | Implemented | See architecture and README limitations; local single-owner reference workflow only. |
| MF-NFR-AUD-003 | Implemented | See architecture and README limitations; local single-owner reference workflow only. |
| MF-NFR-AUD-004 | Partial | See architecture and README limitations; local single-owner reference workflow only. |
| MF-NFR-PER-001 | Deferred | See architecture and README limitations; local single-owner reference workflow only. |
| MF-NFR-PER-002 | Partial | See architecture and README limitations; local single-owner reference workflow only. |
| MF-NFR-PER-003 | Partial | See architecture and README limitations; local single-owner reference workflow only. |
| MF-NFR-PER-004 | Partial | See architecture and README limitations; local single-owner reference workflow only. |
| MF-NFR-SEC-001 | Partial | See architecture and README limitations; local single-owner reference workflow only. |
| MF-NFR-SEC-002 | Partial | See architecture and README limitations; local single-owner reference workflow only. |
| MF-NFR-SEC-003 | Partial | See architecture and README limitations; local single-owner reference workflow only. |
| MF-NFR-SEC-004 | Partial | See architecture and README limitations; local single-owner reference workflow only. |
| MF-NFR-SEC-005 | Partial | See architecture and README limitations; local single-owner reference workflow only. |
| MF-NFR-SEC-006 | Partial | See architecture and README limitations; local single-owner reference workflow only. |
| MF-NFR-UX-001 | Implemented | See architecture and README limitations; local single-owner reference workflow only. |
| MF-NFR-UX-002 | Implemented | See architecture and README limitations; local single-owner reference workflow only. |
| MF-NFR-UX-003 | Implemented | See architecture and README limitations; local single-owner reference workflow only. |
| MF-NFR-UX-004 | Implemented | See architecture and README limitations; local single-owner reference workflow only. |
| MF-NFR-MNT-001 | Partial | See architecture and README limitations; local single-owner reference workflow only. |
| MF-NFR-MNT-002 | Partial | See architecture and README limitations; local single-owner reference workflow only. |
| MF-NFR-MNT-003 | Implemented | See architecture and README limitations; local single-owner reference workflow only. |
| MF-NFR-MNT-004 | Partial | See architecture and README limitations; local single-owner reference workflow only. |
| MF-NFR-OBS-001 | Partial | See architecture and README limitations; local single-owner reference workflow only. |
| MF-NFR-OBS-002 | Partial | See architecture and README limitations; local single-owner reference workflow only. |
| MF-NFR-OBS-003 | Partial | See architecture and README limitations; local single-owner reference workflow only. |
| MF-NFR-OBS-004 | Partial | See architecture and README limitations; local single-owner reference workflow only. |
