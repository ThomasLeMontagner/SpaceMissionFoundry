# Agent authority matrix

Canonical versioned definitions: `backend/app/agents/definitions.py` (prompt version 1.0). Definitions are also model entities in every mission.

| Role | Responsibilities / objective | Proposal authority | Tools | Prohibited |
|---|---|---|---|---|
| Mission & Science | Stakeholders, objectives, priorities, needs | Objective, Requirement, Assumption | None | Approve technical feasibility or baseline |
| Systems Engineering | Integration, allocation, interfaces, trade and dissent | Requirements, architecture, functions, components, interfaces, trades, decisions, risks, verification, assumptions, claims | Trade | Self-approve baseline or impersonate human |
| Mission Analysis | Orbit and eclipse, expose access uncertainty | Parameters, assumptions, claims | Orbit | Accept unsupported calculation |
| Payload | Payload, resolution, swath, pointing, calibration, data demand | Components, parameters, assumptions, claims | Data | Approve baseline |
| Bus & Ground | Power, AOCS, thermal, storage, communications, contacts | Components, interfaces, parameters, assumptions, claims | Mass, power, data, link | Approve baseline |
| Independent Review | Evidence challenges, findings, resolution checks | Findings through dedicated service only | None | Mutate design or approve baseline |

All definitions include required inputs, output contract, prohibited actions and tool allowlist. The trusted deterministic workflow dispatches short dependency-ordered steps; agents have no database handles or arbitrary tool dispatch endpoint. Human requirements and baseline decisions are API commands, never provider outputs.
