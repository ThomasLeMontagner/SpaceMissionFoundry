import os
from uuid import uuid4

from app.agents.definitions import AGENTS
from app.agents.providers import provider
from app.domain.models import Model, Operation, Proposal, now
from app.domain.protocol import accept, validate
from app.engineering_tools.calculations import execute
from app.orchestration.scenario import Q, architectures, assumptions, entity, inputs, requirements
from app.services.brief import extract


class Workflow:
    def __init__(self, store):
        self.store = store

    def create(self, name, brief):
        m = Model(name=name, brief=brief)
        m.entities["brief"] = entity(
            "brief", "Mission", name, "human", classification="Human decision", **extract(brief)
        )
        for key, definition in AGENTS.items():
            m.entities["agent-" + key] = entity(
                "agent-" + key,
                "AgentDefinition",
                definition.role,
                key,
                **definition.model_dump(exclude={"id"}),
            )
        self.propose(m, "science", assumptions(), "assumptions")
        return self.store.save(
            m, "human", "Created mission; reference extraction requires explicit scope approval"
        )

    def propose(self, m, agent, entities, kind):
        for item in entities:
            item.state = "proposed"
        proposal = Proposal(
            proposal_type=kind,
            agent=agent,
            target_revision=m.revision,
            operations=[Operation(action="add", entity=e) for e in entities],
            rationale=f"{AGENTS[agent].role} proposes {kind} from the current engineering model",
            expected_consequences="Review engineering assumptions before acceptance",
            confidence=0.6,
        )
        proposal = provider().propose(
            {
                "mission_id": m.id,
                "revision": m.revision,
                "phase": m.phase,
                "object_ids": list(m.entities),
            },
            proposal,
        )
        validate(m, proposal)
        # Submission itself creates the next revision; target that reviewed snapshot.
        proposal.target_revision = m.revision + 1 if m.steps or m.phase != "Brief" else m.revision
        m.proposals[proposal.id] = proposal
        run_id = str(uuid4())
        m.entities[run_id] = entity(
            run_id,
            "AgentRun",
            f"{AGENTS[agent].role}: {kind}",
            agent,
            agent_version="1.0",
            model=os.getenv("LLM_PROVIDER", "mock"),
            input_revision=m.revision,
            context_references=list(m.entities),
            tool_calls=[],
            proposal=proposal.id,
            result="submitted",
            tokens=0 if os.getenv("LLM_PROVIDER", "mock") == "mock" else "bounded by configuration",
            cost=0 if os.getenv("LLM_PROVIDER", "mock") == "mock" else "unknown",
            timestamp=now(),
        )
        return proposal

    def decide(self, id, proposal_id, action, reason, revision):
        old = self.store.get(id)
        self.guard(old, revision)
        m = old.model_copy(deep=True)
        p = m.proposals.get(proposal_id)
        if not p or p.status not in ["submitted", "challenged"]:
            raise ValueError("Proposal is not pending")
        if action == "accept":
            accept(m, p)
            if p.proposal_type == "assumptions":
                m.phase = "Needs defined"
            elif p.proposal_type == "requirements":
                m.phase = "Requirements approved"
            elif p.proposal_type == "architectures":
                m.phase = "Candidate concepts"
        elif action in ["reject", "challenge"]:
            p.status = "rejected" if action == "reject" else "challenged"
            if action == "challenge":
                p.target_revision = m.revision + 1
        else:
            raise ValueError("Unknown proposal action")
        d = entity(
            str(uuid4()),
            "Decision",
            f"{action.title()} {p.proposal_type}",
            "human",
            classification="Human decision",
            rationale=reason,
            alternatives=["accept", "reject", "challenge"],
            consequences=f"Proposal {p.id} {p.status}",
            context=p.rationale,
        )
        m.entities[d.id] = d
        return self.store.save(m, "human", reason, old)

    def submit(self, id, p):
        old = self.store.get(id)
        self.guard(old, p.target_revision)
        validate(old, p)
        m = old.model_copy(deep=True)
        p.target_revision += 1
        m.proposals[p.id] = p
        return self.store.save(m, p.agent, p.rationale, old)

    def guard(self, m, revision):
        if m.revision != revision:
            raise ValueError("Stale revision; reload and retry")
        if m.baseline:
            raise ValueError("Baseline is immutable; restore a revision to continue")

    def analysis(self, m, tool, values, refs, prefix):
        record = execute(
            tool,
            values,
            m.revision,
            ["Concept estimates; approved resources and operations assumptions"],
        )
        id = f"{prefix}-{tool}-analysis"
        e = entity(
            id,
            "AnalysisRun",
            f"{prefix} · {tool} calculation",
            "tool",
            refs=refs,
            classification="Deterministic calculation",
            **record,
        )
        m.entities[id] = e
        if record["status"] != "valid":
            raise ValueError(f"{tool} calculation invalid: {record['errors']}")
        if tool in ["mass", "power", "data", "link"]:
            b = entity(
                f"{prefix}-{tool}",
                "Budget",
                f"{prefix} · {tool}",
                "tool",
                refs=[id],
                classification="Deterministic calculation",
                candidate=prefix,
                **record["outputs"],
            )
            m.entities[b.id] = b
        claim = entity(
            f"{prefix}-{tool}-claim",
            "Claim",
            f"{prefix}: preliminary {tool} results",
            "tool",
            refs=[id],
            classification="Deterministic calculation",
            outputs=record["outputs"],
            validity="Conditional on recorded assumptions",
        )
        m.entities[claim.id] = claim
        if tool == "mass":
            for index, entry in enumerate(record["outputs"]["entries"]):
                item = entity(
                    f"{prefix}-mass-entry-{index}",
                    "BudgetEntry",
                    entry["name"],
                    "tool",
                    refs=[f"{prefix}-mass", id],
                    classification="Deterministic calculation",
                    **entry,
                )
                m.entities[item.id] = item
        return record["outputs"]

    def advance(self, id, revision):
        old = self.store.get(id)
        self.guard(old, revision)
        if old.paused:
            raise ValueError("Workflow paused; resume to continue")
        if old.steps >= int(os.getenv("MAX_ITERATIONS", "30")):
            raise ValueError("Iteration limit reached; review the run configuration")
        if any(p.status in ["submitted", "challenged"] for p in old.proposals.values()):
            raise ValueError("Resolve pending proposals before advancing")
        m = old.model_copy(deep=True)
        m.steps += 1
        phase = m.phase
        if phase == "Brief":
            self.propose(m, "science", assumptions(), "assumptions")
        elif phase == "Needs defined":
            self.propose(m, "science", requirements(), "requirements")
        elif phase == "Requirements approved":
            self.propose(m, "systems", architectures(), "architectures")
        elif phase == "Candidate concepts":
            orbital = self.analysis(
                m, "orbit", {"altitude": Q(550, "km")}, ["orbit-assumption"], "mission"
            )
            for candidate in ["wide", "selective"]:
                values = inputs(candidate, orbital)
                for tool in ["mass", "power", "data"]:
                    result = self.analysis(
                        m, tool, values[tool], [candidate, "resources", "operations"], candidate
                    )
                    if tool == "data":
                        values["link"]["demand"] = result["daily"]
                result = self.analysis(
                    m,
                    "link",
                    values["link"],
                    [candidate, f"{candidate}-data", "operations"],
                    candidate,
                )
                if not result["compliant"]:
                    finding = entity(
                        f"{candidate}-conflict",
                        "ReviewFinding",
                        "Payload production exceeds daily downlink capacity",
                        "systems",
                        refs=[f"{candidate}-link", f"{candidate}-data"],
                        severity="critical",
                        resolution="",
                        disciplines=[
                            "Payload: preserve contextual imagery",
                            "Bus & Ground: finite contact capacity",
                        ],
                    )
                    finding.state = "open"
                    m.entities[finding.id] = finding
            for role, tools in [
                ("analysis", ["orbit"]),
                ("payload", ["data"]),
                ("bus", ["mass", "power", "link"]),
            ]:
                r = entity(
                    str(uuid4()),
                    "AgentRun",
                    AGENTS[role].role + ": deterministic analysis",
                    role,
                    agent_version="1.0",
                    model="deterministic mock",
                    input_revision=old.revision,
                    context_references=list(old.entities),
                    tool_calls=tools,
                    result="completed",
                    tokens=0,
                    cost=0,
                )
                m.entities[r.id] = r
            weights = {"science": 0.35, "capacity": 0.45, "simplicity": 0.20}
            scores = {
                "wide": {"science": 5, "capacity": 0, "simplicity": 4},
                "selective": {"science": 3, "capacity": 5, "simplicity": 3},
            }
            calculated = self.analysis(
                m,
                "trade",
                {"weights": weights, "scores": scores},
                ["wide-link", "selective-link"],
                "concept",
            )
            t = entity(
                "trade",
                "TradeStudy",
                "Resolve the payload–ground capacity conflict",
                refs=["concept-trade-analysis"],
                criteria=list(weights),
                weights=weights,
                scores=scores,
                recommendation=calculated["recommendation"],
                dissent="Payload favors complete images; event filtering risks missed weak anomalies.",
                sensitivities="Recommendation depends on assumed science utility scores; weights editable before selection.",
                alternatives=["wide", "selective"],
                score_basis="Engineering estimate on a 0–5 ordinal scale",
            )
            m.entities[t.id] = t
            m.phase = "Trade study"
        elif phase == "Selected concept":
            f = entity(
                "review-latency",
                "ReviewFinding",
                "Daily downlink capacity does not establish 30-minute delivery",
                "review",
                refs=["req-latency", f"{m.selected}-link"],
                severity="critical",
                resolution="",
                entry_criteria="Requirements approved; two concepts analyzed; selection recorded",
                checks=["Latency evidence", "Traceability", "Resource compliance"],
                exit_criteria="Explicit unverified status, verification allocation and human acknowledgement",
            )
            f.state = "open"
            m.entities[f.id] = f
            run = entity(
                "review-run",
                "AgentRun",
                "Independent Mission Concept Review",
                "review",
                agent_version="1.0",
                model="deterministic mock",
                input_revision=old.revision,
                context_references=list(old.entities),
                tool_calls=[],
                result="Critical finding raised",
                tokens=0,
                cost=0,
            )
            m.entities[run.id] = run
            m.phase = "Review"
        elif phase == "Review":
            verification = entity(
                "verify-latency",
                "VerificationItem",
                "Demonstrate worst-case acquisition-to-user latency",
                refs=["req-latency", "operations"],
                method="Orbit access and processing simulation",
                success_criterion="All required acquisitions delivered within 30 minutes",
                status="not verified",
                evidence="Unknown: no propagated access evidence",
                review_point="Before preliminary design review",
            )
            m.entities[verification.id] = verification
            m.entities["review-latency"].state = "resolved"
            m.entities["review-latency"].data["resolution"] = (
                "Removed implied latency feasibility; allocated explicit verification task and retained mission risk. This resolves the evidence representation defect, not mission feasibility."
            )
            m.phase = "Resolution proposed"
        elif phase == "Resolution proposed":
            if (
                "verify-latency" not in m.entities
                or m.entities["mission-risk"].data["residual_risk"] != "open"
            ):
                raise ValueError("Independent review resolution checks failed")
            m.entities["review-latency"].state = "verified"
            m.entities["review-latency"].data["reviewer_verification"] = (
                "review: verification obligation and residual risk present; conceptual scope only"
            )
            m.phase = "Ready for baseline"
        else:
            raise ValueError("This phase requires a human decision")
        for e in m.entities.values():
            if e.id not in old.entities or e != old.entities.get(e.id):
                e.revision = old.revision + 1
                e.modified_at = now()
        return self.store.save(m, "orchestrator", f"Advance: {phase} → {m.phase}", old)

    def select(self, id, revision, candidate, weights, reason):
        old = self.store.get(id)
        self.guard(old, revision)
        if old.phase != "Trade study" or candidate not in ["wide", "selective"]:
            raise ValueError("Selection requires analyzed alternatives and a trade study")
        if any(
            not old.entities[f"{candidate}-{tool}"].data["compliant"]
            for tool in ["mass", "power", "data", "link"]
        ):
            raise ValueError("Candidate has a failing budget; revise it before selection")
        m = old.model_copy(deep=True)
        t = m.entities["trade"]
        result = self.analysis(
            m,
            "trade",
            {"weights": weights, "scores": t.data["scores"]},
            ["wide-link", "selective-link"],
            "selection",
        )
        t.data.update(weights=weights, recommendation=result["recommendation"])
        t.relations.append(
            __import__("app.domain.models", fromlist=["Relation"]).Relation(
                type="evidenced_by", target="selection-trade-analysis"
            )
        )
        m.selected = candidate
        m.phase = "Selected concept"
        for e in m.entities.values():
            if e.kind == "ReviewFinding" and e.id.endswith("-conflict"):
                e.state = "resolved"
                e.data["resolution"] = (
                    f"Selected {candidate}; rejected candidate and payload dissent preserved in trade"
                )
        d = entity(
            "selection",
            "Decision",
            f"Mission owner selected {candidate}",
            "human",
            refs=["trade", f"{candidate}-link"],
            classification="Human decision",
            rationale=reason,
            alternatives=["wide", "selective"],
            consequences="Proceed to independent concept review; feasibility remains preliminary",
        )
        m.entities[d.id] = d
        return self.store.save(m, "human", reason, old)

    def baseline(self, id, revision, name, confirm):
        old = self.store.get(id)
        self.guard(old, revision)
        if not confirm or old.phase != "Ready for baseline":
            raise ValueError("Explicit human confirmation after independent review is required")
        if any(
            e.state == "stale"
            or (
                e.kind == "ReviewFinding"
                and e.data["severity"] == "critical"
                and e.state not in ["verified", "resolved", "closed", "waived"]
            )
            for e in old.entities.values()
        ):
            raise ValueError("Stale objects or unresolved critical findings block baseline")
        if any(p.status in ["submitted", "challenged"] for p in old.proposals.values()):
            raise ValueError("Pending proposals block baseline")
        m = old.model_copy(deep=True)
        m.baseline = str(uuid4())
        m.phase = "Baselined"
        d = entity(
            "baseline-approval",
            "Decision",
            name,
            "human",
            refs=["selection", "review-latency", "mission-risk"],
            classification="Human decision",
            rationale="Approve conceptual study with explicitly unverified latency, coverage, lifetime and programme estimates",
            alternatives=["approve conceptual baseline", "continue engineering"],
            consequences="Immutable concept snapshot; not flight feasibility approval",
        )
        m.entities[d.id] = d
        b = entity(
            m.baseline,
            "Baseline",
            name,
            "human",
            refs=["baseline-approval"],
            classification="Human decision",
            source_revision=old.revision + 1,
        )
        m.entities[b.id] = b
        return self.store.save(m, "human", d.data["rationale"], old, baseline=True)
