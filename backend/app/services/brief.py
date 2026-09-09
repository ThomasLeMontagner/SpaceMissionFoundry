"""Conservative reference-brief extraction; unmatched information remains explicitly unknown."""

import re


def extract(brief: str) -> dict:
    patterns = {
        "form_factor": r"\b(\d+)\s*U\b",
        "latency": r"\b(\d+)\s*minutes?\b",
        "programme_budget": r"(?:€|EUR\s*)(\d+(?:\.\d+)?)\s*million",
        "lifetime": r"\b(\d+|two)\s*years?\b",
    }
    constraints = {}
    for name, pattern in patterns.items():
        match = re.search(pattern, brief, re.IGNORECASE)
        constraints[name] = (
            {"original": match.group(0), "status": "stated"} if match else {"status": "unknown"}
        )
    constraints["launch"] = (
        {"original": "rideshare", "status": "stated"}
        if "rideshare" in brief.lower()
        else {"status": "unknown"}
    )
    return {
        "mission_statement": brief,
        "operating_domain": "southern Europe" if "southern europe" in brief.lower() else "Unknown",
        "objectives": ["Detect and monitor wildfires"]
        if "wildfire" in brief.lower()
        else ["Unknown"],
        "constraints": constraints,
        "preferences": ["No additional preferences extracted; confirm with mission owner"],
        "stakeholders": ["Civil protection teams — proposed assumption"],
        "success_criteria": "Detection sensitivity, spatial sampling, swath and revisit need clarification",
        "schedule_assumptions": "Launch date unknown",
        "cost_assumptions": "Programme ceiling is a constraint, not a validated cost estimate",
        "missing_information": [
            "Detection sensitivity",
            "Cloud tolerance",
            "Revisit",
            "Ground stations and contact timing",
            "Launch date",
        ],
        "clarification_questions": [
            "What fire size and detection probability are required?",
            "What revisit and cloud availability are acceptable?",
            "Which ground network can support worst-case 30-minute delivery?",
        ],
        "extraction_method": "Deterministic reference patterns v1.0; approve the explicit scenario assumptions before design",
    }
