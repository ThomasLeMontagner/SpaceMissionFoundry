from pydantic import BaseModel


class AgentDefinition(BaseModel):
    id: str
    role: str
    objective: str
    responsibilities: list[str]
    authority: list[str]
    prohibited_actions: list[str] = ["approve baseline", "execute code", "write database"]
    required_inputs: list[str] = ["current revision", "approved assumptions", "typed relationships"]
    structured_output_schema: str = "Proposal"
    permitted_tools: list[str] = []
    prompt_version: str = "1.0"


AGENTS = {
    "science": AgentDefinition(
        id="science",
        role="Mission & Science",
        objective="Define mission value",
        responsibilities=["Objectives", "stakeholders", "verifiable needs"],
        authority=["Objective", "Requirement", "Assumption"],
    ),
    "systems": AgentDefinition(
        id="systems",
        role="Systems Engineering",
        objective="Integrate a consistent concept",
        responsibilities=["Allocations", "interfaces", "trade studies", "preserve dissent"],
        authority=[
            "Requirement",
            "Function",
            "Component",
            "Interface",
            "ArchitectureAlternative",
            "TradeStudy",
            "Decision",
            "Risk",
            "VerificationItem",
            "Assumption",
            "Claim",
        ],
        permitted_tools=["trade"],
    ),
    "analysis": AgentDefinition(
        id="analysis",
        role="Mission Analysis",
        objective="Calculate orbital geometry",
        responsibilities=["Orbit and eclipse", "expose coverage uncertainty"],
        authority=["Parameter", "Assumption", "Claim"],
        permitted_tools=["orbit"],
    ),
    "payload": AgentDefinition(
        id="payload",
        role="Payload",
        objective="Define observation resource demands",
        responsibilities=["Resolution", "swath", "pointing", "calibration", "data production"],
        authority=["Component", "Parameter", "Assumption", "Claim"],
        permitted_tools=["data"],
    ),
    "bus": AgentDefinition(
        id="bus",
        role="Spacecraft Bus & Ground",
        objective="Support payload and deliver data",
        responsibilities=["Power", "AOCS", "storage", "communications", "ground operations"],
        authority=["Component", "Interface", "Parameter", "Assumption", "Claim"],
        permitted_tools=["mass", "power", "data", "link"],
    ),
    "review": AgentDefinition(
        id="review",
        role="Independent Review",
        objective="Challenge evidence and feasibility",
        responsibilities=["Traceability", "evidence", "critical blockers", "verify resolutions"],
        authority=["ReviewFinding"],
        structured_output_schema="ReviewFinding",
        prohibited_actions=["modify design", "approve baseline", "execute code", "write database"],
    ),
}
