# Mission Foundry

## System Requirements Specification

**Version:** 0.1  
**Status:** Initial requirements baseline  
**Date:** 2026-09-09  
**Working description:** A multi-agent systems-engineering environment for designing space missions.

---

## 1. Purpose

Mission Foundry is a collaborative engineering platform in which specialized LLM agents represent the stakeholders and technical disciplines involved in designing a space mission. Starting from a high-level mission brief, the agents shall negotiate objectives, derive requirements, propose alternative architectures, perform engineering analyses, identify conflicts, and converge on a reviewable mission design baseline.

The platform is not intended to replace qualified engineers or certify a flight system. Its purpose is to:

1. demonstrate disciplined, multi-agent engineering collaboration;
2. produce a coherent conceptual or preliminary mission design;
3. make assumptions, evidence, calculations, conflicts, and decisions fully traceable;
4. provide a research environment for evaluating how reliably LLM agents can perform systems-engineering work.

## 2. Product goals

| ID | Goal |
|---|---|
| G-01 | Transform an incomplete mission idea into a structured, internally consistent mission concept. |
| G-02 | Make every accepted engineering conclusion traceable to requirements, evidence, assumptions, calculations, and decisions. |
| G-03 | Combine LLM judgment with deterministic engineering tools instead of relying on LLM-generated arithmetic. |
| G-04 | Model realistic disagreement between mission stakeholders and engineering disciplines. |
| G-05 | Let a human inspect, challenge, redirect, approve, and replay the complete design process. |
| G-06 | Produce reusable engineering artifacts rather than only an agent conversation transcript. |

## 3. Scope

### 3.1 In scope

- Conceptual and early preliminary design of a space mission.
- Mission objectives, stakeholder needs, and constraints.
- Concept of operations (CONOPS).
- Mission and orbit analysis at an appropriate preliminary-design fidelity.
- Payload and spacecraft architecture.
- Ground-segment and operations concepts.
- Functional decomposition and requirement allocation.
- Mass, power, data, link, and other preliminary budgets.
- Interfaces between major system elements.
- Trade studies, assumptions, risks, and design decisions.
- Reliability, availability, maintainability, safety, and verification considerations.
- Formal reviews and human approval of a design baseline.
- Reproducible scenarios for evaluating agent performance.

### 3.2 Out of scope for the initial product

- Detailed mechanical, electrical, thermal, or flight-software design.
- Manufacturing, procurement, or actual supplier contracting.
- Flight certification or assurance of mission feasibility.
- Autonomous commanding or control of a real spacecraft.
- Replacement of human engineering authority.
- Handling classified or export-controlled information.
- High-fidelity launch, trajectory, thermal, structural, radiation, or RF simulation in the MVP.

## 4. Guiding principles

1. **Model before conversation:** the shared engineering model is the source of truth; chat is an explanation and coordination mechanism.
2. **Tools before arithmetic:** accepted quantitative results must come from deterministic, versioned calculations.
3. **Evidence before confidence:** agents must expose what is known, derived, estimated, assumed, conflicting, or unknown.
4. **Authority is explicit:** each agent may propose broadly but may approve only within its assigned authority.
5. **No silent consensus:** disagreement, dissent, and unresolved issues remain visible until explicitly resolved.
6. **Human baseline authority:** only the human mission owner may approve the final baseline in the MVP.
7. **Everything is traceable:** every model mutation and accepted decision must be attributable and replayable.

## 5. Users and agent roles

### 5.1 Human roles

| Role | Responsibilities |
|---|---|
| Mission Owner | Supplies the mission brief, constraints, priorities, and approval decisions. |
| Engineering User | Inspects and edits requirements, architectures, analyses, and decisions. |
| Evaluator | Runs controlled scenarios and compares agent performance. |
| Administrator | Configures models, tools, permissions, limits, and integrations. |

### 5.2 Initial agent team

| Agent | Primary objective | Authority | Required outputs |
|---|---|---|---|
| Mission & Science Agent | Maximize mission value within stated constraints. | Propose and prioritize stakeholder needs; cannot approve technical feasibility. | Objectives, success criteria, observation needs, mission priorities. |
| Systems Engineering Agent | Maintain an integrated and consistent mission design. | Allocate requirements, coordinate trades, propose integrated baselines; cannot self-approve a review. | System model, requirement tree, architecture, interfaces, budgets, open issues. |
| Mission Analysis Agent | Establish a feasible mission profile and operational geometry. | Approve its analysis results when produced by validated tools. | Candidate orbits, coverage, access, eclipse, lifetime, and mission-phase results. |
| Payload Agent | Define a payload concept that satisfies mission objectives. | Propose payload parameters and constraints. | Payload concept, performance estimates, resource demands, calibration and data products. |
| Spacecraft Bus Agent | Define a platform capable of supporting the payload and mission. | Propose subsystem design and resource allocations. | Power, AOCS, OBC/CDH, thermal, propulsion, structure, and accommodation concepts. |
| Ground & Operations Agent | Ensure the mission can be commanded and its data delivered. | Propose ground architecture and operational constraints. | TT&C concept, ground coverage, operations concept, data processing and staffing assumptions. |
| Independent Review Agent | Challenge feasibility, evidence, traceability, and risk. | Raise findings and block a baseline with unresolved critical findings; cannot alter the design directly. | Review findings, evidence challenges, verification gaps, risk assessment. |

For the MVP, the Mission & Science responsibilities may be combined, and subsystem specialties may be grouped under one Spacecraft Bus Agent. Later releases may split the bus into dedicated Power, Thermal, AOCS, Propulsion, Avionics, Structures, and Communications agents.

## 6. System context

Mission Foundry shall contain the following logical capabilities:

- Human workspace and dashboard.
- Agent orchestrator and workflow engine.
- Versioned shared engineering model.
- Requirement, architecture, interface, and budget services.
- Sandboxed deterministic engineering tools.
- Evidence and source repository.
- Review and approval service.
- Event log, replay, evaluation, and observability services.
- Report and data export service.

External dependencies may include LLM providers, public engineering references, orbital-data services, and validated engineering libraries. The core domain model shall not depend on one LLM provider.

## 7. Functional requirements

Priority uses **Must**, **Should**, and **Could**. “Must” requirements define the intended MVP unless explicitly marked Post-MVP.

### 7.1 Mission definition

| ID | Requirement | Priority | Verification |
|---|---|---:|---|
| MF-MIS-001 | The system shall allow a user to create a mission from a natural-language brief. | Must | Demonstration |
| MF-MIS-002 | The mission record shall include a name, mission statement, target or operating domain, objectives, stakeholders, constraints, success criteria, schedule assumptions, and cost assumptions. | Must | Inspection |
| MF-MIS-003 | The system shall distinguish mandatory constraints from preferences and optimization objectives. | Must | Test |
| MF-MIS-004 | The system shall identify missing, ambiguous, conflicting, and non-verifiable statements in the mission brief. | Must | Test |
| MF-MIS-005 | The system shall request human clarification when an ambiguity could materially change the architecture. | Must | Demonstration |
| MF-MIS-006 | The system shall allow the user to accept an explicitly labelled assumption instead of answering a clarification question. | Must | Demonstration |
| MF-MIS-007 | The system shall represent quantities using explicit units and preserve their original input values. | Must | Test |
| MF-MIS-008 | The system should support reusable mission templates, initially including an Earth-observation CubeSat mission. | Should | Demonstration |
| MF-MIS-009 | The system could support planetary, lunar, communications, navigation, science, and in-orbit demonstration mission templates. | Could | Demonstration |

### 7.2 Agent definition and orchestration

| ID | Requirement | Priority | Verification |
|---|---|---:|---|
| MF-AGT-001 | Every agent shall have a versioned definition containing its role, objective, responsibilities, authority, constraints, required inputs, required outputs, and permitted tools. | Must | Inspection |
| MF-AGT-002 | The orchestrator shall assign work according to dependencies in the engineering workflow rather than invoking every agent indiscriminately. | Must | Test |
| MF-AGT-003 | An agent shall receive the relevant current model state and referenced artifacts, not rely solely on the conversation transcript. | Must | Test |
| MF-AGT-004 | Agent outputs that modify the design shall use schema-valid structured proposals. | Must | Test |
| MF-AGT-005 | The system shall reject malformed or unauthorized model mutations without corrupting the current model. | Must | Test |
| MF-AGT-006 | The system shall record the originating agent, model, agent-definition version, timestamp, inputs, tool calls, and result for every agent run. | Must | Inspection |
| MF-AGT-007 | Agents shall be able to accept, challenge, counter-propose, or request clarification on another agent's proposal. | Must | Demonstration |
| MF-AGT-008 | The orchestrator shall prevent an agent from approving an artifact for which it is the sole author when independent review is required. | Must | Test |
| MF-AGT-009 | The Systems Engineering Agent shall coordinate integration conflicts but shall preserve dissenting positions in the decision record. | Must | Demonstration |
| MF-AGT-010 | The user shall be able to pause, resume, stop, or redirect an active design run. | Must | Demonstration |
| MF-AGT-011 | The user shall be able to approve, reject, edit, or request revision of an agent proposal. | Must | Demonstration |
| MF-AGT-012 | The orchestrator shall enforce configurable limits for iteration count, elapsed time, token usage, and monetary cost. | Must | Test |
| MF-AGT-013 | The system shall detect repeated proposal cycles and escalate them as an unresolved deadlock. | Should | Test |
| MF-AGT-014 | The system should support parallel agent work when tasks are independent and merge results through conflict-checked proposals. | Should | Test |
| MF-AGT-015 | The platform should support multiple LLM providers through a provider-neutral adapter. | Should | Inspection |

### 7.3 Shared engineering model

| ID | Requirement | Priority | Verification |
|---|---|---:|---|
| MF-MDL-001 | The system shall maintain one authoritative, versioned engineering model for each mission. | Must | Inspection |
| MF-MDL-002 | The model shall support objectives, requirements, functions, logical elements, physical components, interfaces, parameters, budgets, claims, evidence, assumptions, analyses, alternatives, decisions, issues, risks, verification items, agents, and baselines. | Must | Test |
| MF-MDL-003 | Every model object shall have a stable identifier, type, lifecycle state, owner, creation time, modification time, and revision. | Must | Test |
| MF-MDL-004 | Relationships between model objects shall be typed and bidirectionally navigable. | Must | Test |
| MF-MDL-005 | Model changes shall be performed as atomic transactions. | Must | Test |
| MF-MDL-006 | The system shall retain the complete before-and-after history of every accepted model mutation. | Must | Test |
| MF-MDL-007 | The system shall prevent deletion from silently removing traceability links or historical evidence. | Must | Test |
| MF-MDL-008 | All user-interface views and generated reports shall derive from the same authoritative model revision. | Must | Test |
| MF-MDL-009 | The system shall identify stale downstream objects when an upstream assumption, requirement, parameter, or analysis changes. | Must | Test |
| MF-MDL-010 | The system should support branches for competing architecture alternatives. | Should | Demonstration |
| MF-MDL-011 | The system should allow comparison and controlled merging of model branches. | Should | Demonstration |

### 7.4 Requirements engineering

| ID | Requirement | Priority | Verification |
|---|---|---:|---|
| MF-REQ-001 | Each requirement shall include a stable ID, statement, rationale, source, level, owner, priority, status, verification method, and parent or originating need. | Must | Test |
| MF-REQ-002 | The system shall support derivation, decomposition, allocation, satisfaction, and verification relationships. | Must | Test |
| MF-REQ-003 | The system shall maintain bidirectional traceability from mission objectives to system and subsystem requirements. | Must | Test |
| MF-REQ-004 | The system shall detect orphan requirements and objectives without supporting requirements. | Must | Test |
| MF-REQ-005 | The system shall flag requirements that are ambiguous, compound, solution-biased, internally conflicting, or not verifiable. | Must | Test |
| MF-REQ-006 | The system shall distinguish a requirement from a design decision, assumption, objective, and explanatory note. | Must | Test |
| MF-REQ-007 | Agents shall provide a rationale when deriving or changing a requirement. | Must | Inspection |
| MF-REQ-008 | A requirement shall not become approved solely because it was generated by an agent. | Must | Test |
| MF-REQ-009 | The user shall be able to manually create and edit requirements while preserving history. | Must | Demonstration |
| MF-REQ-010 | The system should calculate requirement coverage and traceability-completeness metrics. | Should | Test |

### 7.5 Architecture and interfaces

| ID | Requirement | Priority | Verification |
|---|---|---:|---|
| MF-ARC-001 | The system shall represent mission, system, segment, spacecraft, subsystem, and component decomposition. | Must | Test |
| MF-ARC-002 | The system shall represent functional and physical architectures separately and link allocated functions to physical elements. | Must | Test |
| MF-ARC-003 | The system shall represent interfaces with endpoints, exchanged items, direction, protocol or medium, constraints, and ownership. | Must | Test |
| MF-ARC-004 | The system shall detect unallocated required functions and components with no justified function. | Must | Test |
| MF-ARC-005 | The system shall detect incomplete, incompatible, or contradictory interface definitions. | Must | Test |
| MF-ARC-006 | The agents shall generate at least two materially different architecture candidates before concept selection, unless the user explicitly waives alternatives. | Must | Demonstration |
| MF-ARC-007 | Every architecture candidate shall identify its driving assumptions, expected benefits, disadvantages, major risks, and resource estimates. | Must | Inspection |
| MF-ARC-008 | The system shall generate synchronized functional, physical, and interface views from the model. | Must | Demonstration |
| MF-ARC-009 | The system should generate an initial interface-control document from accepted model data. | Should | Demonstration |

### 7.6 Engineering analyses and budgets

| ID | Requirement | Priority | Verification |
|---|---|---:|---|
| MF-ANL-001 | Accepted quantitative results shall be produced or checked by a deterministic engineering tool, not accepted solely from free-form LLM output. | Must | Test |
| MF-ANL-002 | Each analysis run shall record tool name and version, input parameters and units, assumptions, execution time, output values and units, warnings, errors, and originating model revision. | Must | Test |
| MF-ANL-003 | Re-executing an unchanged deterministic analysis with the same tool version and inputs shall produce the same result. | Must | Test |
| MF-ANL-004 | The system shall validate dimensional compatibility and explicitly convert compatible units. | Must | Test |
| MF-ANL-005 | The system shall support preliminary mass, power, energy, data-volume, and communications-link budgets. | Must | Demonstration |
| MF-ANL-006 | Each budget shall show allocations, estimates, margins, totals, limits, and compliance status. | Must | Test |
| MF-ANL-007 | The system shall identify exceeded limits and negative margins as engineering conflicts. | Must | Test |
| MF-ANL-008 | Analysis failures or missing inputs shall produce an explicit unknown or invalid result rather than a fabricated estimate. | Must | Test |
| MF-ANL-009 | The system shall preserve uncertainty ranges or confidence intervals where the source data supports them. | Must | Test |
| MF-ANL-010 | The system should perform sensitivity analysis for user-selected design parameters. | Should | Demonstration |
| MF-ANL-011 | The system should support preliminary orbit, coverage, access-window, eclipse, and mission-lifetime calculations. | Should | Demonstration |
| MF-ANL-012 | The system could later integrate high-fidelity domain tools without changing the core model schema. | Could | Inspection |

### 7.7 Evidence, assumptions, and claims

| ID | Requirement | Priority | Verification |
|---|---|---:|---|
| MF-EVD-001 | Every substantive engineering claim shall be classified as verified fact, calculated result, engineering estimate, analogy, assumption, proposal, or unknown. | Must | Test |
| MF-EVD-002 | A claim based on a source shall link to the exact source and, where possible, the relevant page, section, table, or data item. | Must | Inspection |
| MF-EVD-003 | A calculated claim shall link to the corresponding analysis run. | Must | Test |
| MF-EVD-004 | An assumed value shall include an owner, rationale, impact, confidence, and validation plan. | Must | Test |
| MF-EVD-005 | The system shall preserve contradictory sources and flag the associated claim as disputed. | Must | Test |
| MF-EVD-006 | An agent shall explicitly report missing evidence instead of inventing a citation or source. | Must | Test |
| MF-EVD-007 | Changing or invalidating evidence shall mark dependent claims and decisions as potentially stale. | Must | Test |
| MF-EVD-008 | Imported text shall be treated as untrusted content and shall not be allowed to redefine agent instructions or permissions. | Must | Security test |

### 7.8 Trade studies and decisions

| ID | Requirement | Priority | Verification |
|---|---|---:|---|
| MF-TRD-001 | The system shall represent a trade study with alternatives, evaluation criteria, criterion weights, assumptions, analysis references, scores, sensitivities, and recommendation. | Must | Test |
| MF-TRD-002 | Trade criteria and weights shall be visible and editable by the user before final selection. | Must | Demonstration |
| MF-TRD-003 | Agents shall be able to challenge an alternative, criterion, weight, assumption, or result. | Must | Demonstration |
| MF-TRD-004 | The system shall distinguish the agent recommendation from the human decision. | Must | Test |
| MF-TRD-005 | Every accepted design decision shall include context, considered alternatives, rationale, approving authority, consequences, and linked evidence. | Must | Test |
| MF-TRD-006 | Rejected alternatives and dissenting agent opinions shall remain available in the historical record. | Must | Inspection |
| MF-TRD-007 | A change that invalidates a decision premise shall reopen or flag the decision for review. | Must | Test |
| MF-TRD-008 | The system should support Pareto views for multi-objective trades. | Should | Demonstration |

### 7.9 Conflict management and design reviews

| ID | Requirement | Priority | Verification |
|---|---|---:|---|
| MF-REV-001 | The system shall represent conflicts and review findings as first-class objects with severity, owner, status, affected items, proposed resolution, and due or review point. | Must | Test |
| MF-REV-002 | Conflicts shall be creatable by agents, users, rules, and failed engineering constraints. | Must | Test |
| MF-REV-003 | Critical findings shall block baseline approval until resolved, downgraded with rationale, or explicitly waived by the human Mission Owner. | Must | Test |
| MF-REV-004 | The Independent Review Agent shall have read access to the complete proposed baseline and shall not modify it directly. | Must | Security test |
| MF-REV-005 | A review shall use explicit entry criteria, checks, findings, actions, and exit criteria. | Must | Test |
| MF-REV-006 | The MVP shall support a Mission Concept Review and a Preliminary Design Review–style gate. | Must | Demonstration |
| MF-REV-007 | The user shall be able to resolve, reject, waive, reopen, and close a finding while preserving its history. | Must | Demonstration |
| MF-REV-008 | The system shall present unresolved disagreements and the arguments of each relevant discipline to the human decision-maker. | Must | Demonstration |

### 7.10 Baselines and configuration management

| ID | Requirement | Priority | Verification |
|---|---|---:|---|
| MF-CFG-001 | The user shall be able to create an immutable named baseline from a selected model revision. | Must | Test |
| MF-CFG-002 | A baseline shall contain its model revision, requirements, architectures, analyses, assumptions, decisions, risks, findings, and generated artifacts. | Must | Test |
| MF-CFG-003 | Baseline approval shall require an explicit human action. | Must | Test |
| MF-CFG-004 | The system shall display the differences between two model revisions or baselines. | Must | Demonstration |
| MF-CFG-005 | The system shall allow a user to return to an earlier revision by creating a new revision based on it; immutable history shall remain intact. | Must | Test |
| MF-CFG-006 | Generated artifacts shall identify the source baseline and generation time. | Must | Inspection |

### 7.11 User interface

| ID | Requirement | Priority | Verification |
|---|---|---:|---|
| MF-UI-001 | The primary dashboard shall summarize mission objectives, design maturity, budget margins, active agents, open conflicts, critical risks, and current review status. | Must | Demonstration |
| MF-UI-002 | The application shall provide dedicated views for mission definition, requirements, architecture, interfaces, budgets, analyses, evidence, decisions, risks, reviews, and agent activity. | Must | Demonstration |
| MF-UI-003 | The user shall be able to trace any displayed requirement, claim, parameter, or decision to its upstream and downstream relationships. | Must | Demonstration |
| MF-UI-004 | The interface shall clearly distinguish accepted model data from pending agent proposals. | Must | Demonstration |
| MF-UI-005 | The interface shall clearly distinguish calculated values, sourced facts, estimates, assumptions, and unknowns. | Must | Demonstration |
| MF-UI-006 | The user shall be able to inspect the rationale, evidence, tool outputs, objections, and approval state of any proposal or decision. | Must | Demonstration |
| MF-UI-007 | The user shall be able to filter and search model objects by ID, text, type, owner, status, agent, and lifecycle state. | Must | Demonstration |
| MF-UI-008 | The interface shall provide live progress without requiring a page refresh during an active design run. | Must | Demonstration |
| MF-UI-009 | The user shall be able to compare architecture alternatives and baselines side by side. | Must | Demonstration |
| MF-UI-010 | Diagrams and summary tables shall remain synchronized with the authoritative model. | Must | Test |
| MF-UI-011 | Critical actions such as approving a baseline or waiving a critical finding shall require clear confirmation and shall not be represented by ambiguous icon-only controls. | Must | Usability test |
| MF-UI-012 | All essential workflows shall be keyboard accessible and shall provide visible focus, descriptive labels, sufficient contrast, loading states, empty states, and actionable error states. | Must | Usability test |
| MF-UI-013 | The initial interface shall be optimized for desktop engineering work and remain usable on tablet-sized displays. | Should | Usability test |
| MF-UI-014 | The system should provide an interactive mission and spacecraft visualization linked to model elements. | Should | Demonstration |

### 7.12 Reports, import, and export

| ID | Requirement | Priority | Verification |
|---|---|---:|---|
| MF-IO-001 | The system shall export the complete mission model in a documented machine-readable format. | Must | Test |
| MF-IO-002 | The system shall export requirements, budgets, interfaces, assumptions, risks, findings, and decisions to human-readable Markdown and CSV where applicable. | Must | Test |
| MF-IO-003 | The system shall generate a mission concept report from an approved baseline. | Must | Demonstration |
| MF-IO-004 | The generated report shall include scope, CONOPS, requirements, architecture, analyses, budgets, assumptions, trades, risks, findings, and traceability summary. | Must | Inspection |
| MF-IO-005 | The system shall import a previously exported mission model without losing identifiers or relationships. | Must | Round-trip test |
| MF-IO-006 | The system should provide a documented API for model queries, proposals, workflow control, and exports. | Should | Inspection |
| MF-IO-007 | The system could later support SysML v2 or another standard systems-engineering exchange format. | Could | Demonstration |

### 7.13 Replay and evaluation

| ID | Requirement | Priority | Verification |
|---|---|---:|---|
| MF-EVL-001 | The system shall preserve an ordered event log of user actions, agent actions, tool executions, proposals, decisions, and model changes. | Must | Test |
| MF-EVL-002 | The user shall be able to replay a completed design run and inspect the model state at each recorded step. | Must | Demonstration |
| MF-EVL-003 | The system shall support named, versioned evaluation scenarios with fixed briefs, constraints, injected conflicts, tool versions, and expected checks. | Must | Test |
| MF-EVL-004 | An evaluation run shall report requirement coverage, traceability completeness, unresolved conflicts, constraint violations, unsupported accepted claims, tool failures, elapsed time, token usage, and estimated cost. | Must | Test |
| MF-EVL-005 | The system shall distinguish deterministic calculation reproducibility from nondeterministic LLM behavior. | Must | Inspection |
| MF-EVL-006 | The system should allow two agent configurations or model versions to be compared on the same scenario. | Should | Demonstration |
| MF-EVL-007 | The system should detect when an agent cites nonexistent evidence, exceeds its authority, or accepts an unsupported numerical result. | Should | Test |

## 8. Non-functional requirements

### 8.1 Reliability and data integrity

| ID | Requirement | Priority |
|---|---|---:|
| MF-NFR-REL-001 | A failed agent or tool execution shall not corrupt the last valid model revision. | Must |
| MF-NFR-REL-002 | Retrying an operation shall not create duplicate accepted proposals or model objects. | Must |
| MF-NFR-REL-003 | The system shall validate persisted model data against a versioned schema. | Must |
| MF-NFR-REL-004 | The system shall provide recoverable checkpoints during long-running workflows. | Must |

### 8.2 Auditability and reproducibility

| ID | Requirement | Priority |
|---|---|---:|
| MF-NFR-AUD-001 | Every state-changing action shall record actor, timestamp, reason, request, outcome, and affected object revisions. | Must |
| MF-NFR-AUD-002 | Audit records and approved baselines shall be immutable through normal application operations. | Must |
| MF-NFR-AUD-003 | Recorded runs shall remain replayable even when the current agent definitions have changed. | Must |
| MF-NFR-AUD-004 | Prompt templates, model identifiers, tool versions, and configuration used in a run shall be versioned. | Must |

### 8.3 Performance and scalability

| ID | Requirement | Priority |
|---|---|---:|
| MF-NFR-PER-001 | Normal model browsing and filtering operations should respond within two seconds for a mission containing 10,000 model objects, excluding external model calls. | Should |
| MF-NFR-PER-002 | The MVP shall support at least six active role agents within one mission workflow. | Must |
| MF-NFR-PER-003 | Long-running agent and analysis tasks shall execute asynchronously and expose progress and cancellation. | Must |
| MF-NFR-PER-004 | The system should support multiple missions without mixing their data or agent context. | Should |

### 8.4 Security and permissions

| ID | Requirement | Priority |
|---|---|---:|
| MF-NFR-SEC-001 | The system shall enforce least-privilege access for users, agents, engineering tools, and external integrations. | Must |
| MF-NFR-SEC-002 | Agent-generated code or tool input shall execute only in an isolated environment with explicit resource and network limits. | Must |
| MF-NFR-SEC-003 | Secrets shall not be stored in prompts, engineering artifacts, logs, or exported mission models. | Must |
| MF-NFR-SEC-004 | External documents and retrieved content shall be isolated from system and agent-control instructions. | Must |
| MF-NFR-SEC-005 | The system shall require authentication before access to non-public mission data. | Must |
| MF-NFR-SEC-006 | The system shall prevent one mission workspace from accessing another mission's private artifacts. | Must |

### 8.5 Explainability and usability

| ID | Requirement | Priority |
|---|---|---:|
| MF-NFR-UX-001 | The system shall expose concise human-readable explanations for recommendations, conflicts, and decisions. | Must |
| MF-NFR-UX-002 | The user shall never need to inspect raw LLM prompts to understand why a design item was accepted. | Must |
| MF-NFR-UX-003 | Errors shall state what failed, what data was affected, and what the user can do next. | Must |
| MF-NFR-UX-004 | Agent uncertainty and unresolved engineering uncertainty shall be visible and not represented as certainty. | Must |

### 8.6 Maintainability and extensibility

| ID | Requirement | Priority |
|---|---|---:|
| MF-NFR-MNT-001 | Agent definitions, domain tools, workflow definitions, and report templates shall be replaceable without modifying the core model. | Must |
| MF-NFR-MNT-002 | The system shall use versioned interfaces between orchestration, model, tool, and presentation layers. | Must |
| MF-NFR-MNT-003 | Core model validation, calculations, permissions, and lifecycle transitions shall have automated tests. | Must |
| MF-NFR-MNT-004 | Database migrations shall preserve historical model revisions and audit records. | Must |

### 8.7 Observability and cost control

| ID | Requirement | Priority |
|---|---|---:|
| MF-NFR-OBS-001 | The system shall record structured logs and traces across an end-to-end agent workflow. | Must |
| MF-NFR-OBS-002 | The user shall be able to inspect latency, failures, retry count, token use, and estimated model cost by agent and run. | Must |
| MF-NFR-OBS-003 | The system shall warn the user before a run exceeds a configurable cost or iteration threshold. | Must |
| MF-NFR-OBS-004 | Personally identifiable information and secrets shall be redacted from operational telemetry. | Must |

## 9. Core domain objects

The minimum shared model should contain the following entities:

| Entity | Essential fields |
|---|---|
| Mission | ID, name, statement, lifecycle phase, owner, current revision, current baseline. |
| Objective | Statement, stakeholder, priority, measure of success, parent objective. |
| Requirement | Statement, rationale, source, level, priority, owner, status, verification method. |
| Function | Inputs, outputs, performance, allocated element, linked requirements. |
| Component | Type, parent, functions, parameters, interfaces, maturity, supplier or analogy if applicable. |
| Interface | Endpoints, exchanges, direction, medium/protocol, constraints, owner, status. |
| Parameter | Name, value/range, unit, uncertainty, source, applicability, status. |
| Budget | Type, entries, allocation, estimate, margin policy, total, limit, compliance. |
| Claim | Statement, classification, confidence, evidence, owner, lifecycle state. |
| Evidence | Source identity, location, excerpt or data reference, provenance, access date, trust assessment. |
| Assumption | Statement, rationale, owner, impact, confidence, validation plan, status. |
| AnalysisRun | Tool/version, inputs, outputs, warnings, model revision, reproducibility information. |
| Alternative | Architecture branch, assumptions, benefits, drawbacks, risks, linked trade study. |
| Decision | Context, alternatives, rationale, authority, consequences, evidence, state. |
| Issue/Finding | Severity, owner, affected objects, proposed resolution, lifecycle state. |
| Risk | Cause, event, consequence, likelihood, severity, mitigation, residual risk. |
| VerificationItem | Requirement, method, level, success criterion, evidence, status. |
| AgentRun | Agent/version, model, context references, tool calls, proposal, result, cost. |
| Baseline | Name, immutable model revision, approval, contents, generated artifacts. |

## 10. Lifecycle states

### 10.1 Proposal

`Drafted → Submitted → Challenged → Accepted | Rejected | Superseded`

### 10.2 Requirement

`Proposed → Reviewed → Approved → Allocated → Verified`, with `Rejected`, `Deferred`, and `Retired` side states.

### 10.3 Issue or finding

`Open → Assigned → Resolution proposed → Resolved → Verified → Closed`, with a controlled `Waived` state.

### 10.4 Mission design

`Brief → Needs defined → Candidate concepts → Selected concept → Review → Baselined`

State transitions shall be explicit, authorized, and recorded. An agent shall not silently treat a proposal as accepted merely by referring to it in a later response.

## 11. MVP definition

### 11.1 Recommended reference mission

The first controlled scenario should be a **12U Earth-observation CubeSat for wildfire detection and monitoring in low Earth orbit**, with defined targets for ground sampling distance, swath, revisit time, alert latency, mission lifetime, budget, and rideshare constraints.

This scenario exercises payload sizing, orbital coverage, power generation, eclipse energy balance, pointing, onboard storage, downlink capacity, ground-station access, thermal assumptions, and competing mission priorities without requiring a high-fidelity interplanetary trajectory model.

### 11.2 MVP capabilities

The MVP shall include:

- One mission workspace and one reference mission template.
- Six active roles: Mission & Science, Systems Engineering, Mission Analysis, Payload, Spacecraft Bus, and Independent Review. Ground/Operations may be a seventh role or combined with the bus for the first iteration.
- A structured shared model stored persistently.
- Natural-language mission brief ingestion and clarification.
- Objective and requirement generation with human approval.
- At least two architecture candidates.
- Deterministic mass, power/energy, data-volume, and simple link-budget tools.
- Explicit proposals, objections, conflicts, and decisions.
- One formal concept review.
- Human-approved immutable baseline.
- Dashboard, requirements, architecture, budgets, conflicts, evidence, decisions, and agent-run views.
- Complete event log and replay.
- Markdown, CSV, and machine-readable model export.

### 11.3 Explicitly deferred from MVP

- Detailed thermal-node or structural finite-element analysis.
- High-fidelity trajectory optimization.
- Real supplier catalogues or procurement workflows.
- Full SysML import/export.
- Multi-user real-time editing.
- Automated detailed subsystem design.
- A photorealistic or engineering-grade 3D spacecraft model.
- Autonomous approval of the mission baseline.

## 12. MVP end-to-end acceptance scenario

The MVP is accepted when the following scenario can be completed:

1. A user creates the reference mission from an incomplete natural-language brief.
2. The system identifies material ambiguities and either obtains clarification or records approved assumptions.
3. Agents derive a traceable objective and requirement hierarchy.
4. Agents create at least two meaningfully different mission or spacecraft concepts.
5. Deterministic tools calculate mass, power/energy, data, and link budgets for each candidate.
6. The scenario introduces at least one genuine cross-disciplinary conflict, such as payload duty cycle causing a negative eclipse-energy margin or data production exceeding downlink capacity.
7. The responsible agents identify the conflict, propose alternatives, and create a documented trade study.
8. The Systems Engineering Agent recommends an integrated concept while preserving dissent and uncertainty.
9. The Independent Review Agent finds at least one deliberately seeded traceability, evidence, or feasibility defect.
10. The design team resolves the finding and the reviewer verifies the resolution.
11. The human Mission Owner approves the selected concept and creates an immutable baseline.
12. The system generates a mission concept report and exports the full model.
13. A user can select any accepted quantitative value and trace it to its tool execution, inputs, units, source model revision, affected requirements, and resulting decision.
14. A user can replay the run and observe how the model evolved from brief to baseline.

The acceptance run fails if an unsupported numerical claim is accepted as authoritative, a critical finding remains unresolved without an explicit human waiver, or any accepted requirement or decision lacks an attributable source and history.

## 13. Suggested delivery roadmap

### Phase 0 — Foundations

- Define domain schema and lifecycle rules.
- Define agent contracts and authority matrix.
- Implement append-only events and versioned model mutations.
- Build one deterministic budget tool and validate the proposal workflow.

### Phase 1 — Vertical MVP

- Implement the reference mission workflow end to end.
- Add the six initial agents.
- Add mass, power/energy, data, and simple link budgets.
- Add core dashboard and review workflow.
- Generate and approve a first mission baseline.

### Phase 2 — Engineering depth

- Add orbit/coverage/access analysis.
- Split the spacecraft-bus role into subsystem agents.
- Add interface consistency, risk, FMEA, and verification planning.
- Add architecture branching and side-by-side trades.

### Phase 3 — Research and evaluation platform

- Add controlled scenario suites and seeded defects.
- Compare agent teams, prompts, models, and governance rules.
- Add quantitative quality and hallucination metrics.
- Publish reproducible benchmark runs.

### Phase 4 — Ecosystem integration

- Add standard systems-engineering exchange formats.
- Integrate higher-fidelity engineering tools.
- Support organizational and supplier agents with contractual interfaces.
- Connect an approved design baseline to a simulator such as ADSOP while keeping the projects independently usable.

## 14. Key risks and mitigations

| Risk | Consequence | Required mitigation |
|---|---|---|
| Agents confidently invent engineering facts | Plausible but unsafe design | Claim classification, evidence requirements, deterministic checks, independent review. |
| Agents agree too easily | Superficial consensus and missed defects | Conflicting objectives, explicit challenge actions, independent reviewer, seeded faults. |
| Endless debate | High cost without convergence | Iteration budgets, deadlock detection, escalation, human decision gates. |
| Conversation becomes the real state | Inconsistent artifacts and lost context | Schema-validated shared model as the sole source of truth. |
| LLM arithmetic errors | Invalid budgets | Deterministic unit-aware engineering tools for accepted calculations. |
| Upstream changes leave stale conclusions | Hidden inconsistency | Dependency graph and automatic stale-state propagation. |
| Scope grows to full spacecraft design | Project never reaches an MVP | One reference mission, grouped roles, preliminary fidelity, explicit deferred scope. |
| Attractive UI hides weak engineering | Portfolio demo lacks substance | Traceability, evaluation scenarios, exported artifacts, and measurable acceptance criteria. |
| Retrieved documents manipulate agents | Prompt injection or authority bypass | Treat sources as untrusted data and enforce tool/permission boundaries outside prompts. |

## 15. Definition of done for the first public release

The first public release is done when:

- the reference acceptance scenario passes automatically except for intentional human approvals;
- all Must requirements assigned to the release have tests or documented demonstrations;
- engineering calculations have unit tests against known cases;
- agent authority and schema violations are rejected by automated tests;
- a complete run can be replayed after the original agent session has ended;
- the generated report and exported model are internally consistent with the approved baseline;
- limitations and non-certification status are clearly documented;
- a new user can run the reference mission locally from documented setup instructions.

---

## Appendix A — Example mission brief

> Design a 12U CubeSat mission that detects and monitors wildfires over southern Europe. The mission should provide useful imagery within 30 minutes of acquisition, operate for at least two years, use a rideshare launch, and remain within a €12 million programme budget. Determine a plausible payload, orbit, spacecraft architecture, ground segment, operational concept, and preliminary engineering budgets. Explicitly identify assumptions and unresolved feasibility questions.

## Appendix B — Initial success metrics

| Metric | Initial target |
|---|---:|
| Accepted requirements with an originating objective or parent | 100% |
| Accepted quantitative claims linked to deterministic analyses | 100% |
| Accepted sourced claims with resolvable evidence | 100% |
| Critical findings open at baseline approval | 0, unless explicitly waived by the human Mission Owner |
| Budget categories with visible assumptions and margins | 100% of implemented categories |
| Unauthorized model mutations accepted | 0 |
| Seeded critical defects detected during review | 100% in the reference scenario |
| Complete run replay available | 100% of baselined runs |

