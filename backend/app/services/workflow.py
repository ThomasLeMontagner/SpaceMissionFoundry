import os
from uuid import uuid4

from app.agents.definitions import AGENTS
from app.agents.providers import provider
from app.domain.models import Model, Operation, Proposal, Relation, now
from app.domain.protocol import accept, validate
from app.engineering_tools.calculations import execute
from app.orchestration.scenario import architectures, assumptions, entity, requirements
from app.services.brief import extract
from app.services.design_inputs import (
    BUDGET_TOOLS,
    CANDIDATES,
    IMPACT_KINDS,
    access_parameter,
    delivery_parameters,
    edited_entity,
    input_entities,
    parameter_id,
    read_inputs,
)
from app.services.interface_checks import guard_interfaces, refresh_interfaces
from app.services.requirement_checks import guard_candidate, refresh


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
            if any(
                op.action == "replace"
                and op.entity.kind in ["Assumption", "Requirement", "Parameter", "Interface"]
                for op in p.operations
            ):
                self.after_change(m)
            elif p.proposal_type == "assumptions":
                m.phase = "Needs defined"
            elif p.proposal_type == "requirements":
                m.phase = "Requirements approved"
            elif p.proposal_type == "architectures":
                m.phase = "Candidate concepts"
            elif p.proposal_type == "calculation inputs":
                self.require_recalculation(m)
            elif p.proposal_type == "design change":
                self.after_change(m)
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
        if p.source_study is not None:
            raise ValueError("Study provenance must come from the saved-trial proposal endpoint")
        old = self.store.get(id)
        self.guard(old, p.target_revision)
        if p.id in old.proposals or p.status != "submitted":
            raise ValueError("Proposal must be a new submitted proposal")
        if p.agent == "human":
            raise ValueError("Use the mission owner edit endpoint for human changes")
        validate(old, p)
        m = old.model_copy(deep=True)
        p.target_revision += 1
        m.proposals[p.id] = p
        return self.store.save(m, p.agent, p.rationale, old)

    def guard(self, m, revision):
        if m.archived:
            raise ValueError("Mission is archived; restore it to the active list before editing")
        if m.revision != revision:
            raise ValueError("Stale revision; reload and retry")
        if m.baseline:
            raise ValueError("Baseline is immutable; restore a revision to continue")

    def archive(self, id, revision, archived):
        old = self.store.get(id)
        if old.revision != revision:
            raise ValueError("Stale revision; reload before changing archive status")
        if old.archived == archived:
            return old
        m = old.model_copy(deep=True)
        m.archived = archived
        for p in m.proposals.values():
            if p.status in ["submitted", "challenged"]:
                p.target_revision = old.revision + 1
        return self.store.save(
            m,
            "human",
            "Archived mission; history retained" if archived else "Restored mission to active list",
            old,
        )

    def analysis(self, m, tool, values, refs, prefix):
        record = execute(
            tool,
            values,
            m.revision,
            ["Concept estimates; approved resources and operations assumptions"],
        )
        if tool == "trade" and record["status"] != "valid":
            raise ValueError("Invalid trade inputs: " + "; ".join(record["errors"]))
        id = f"{prefix}-{tool}-analysis"
        e = entity(
            id,
            "AnalysisRun",
            f"{prefix} · {tool} calculation",
            "tool",
            refs=refs,
            classification="Deterministic calculation"
            if record["status"] == "valid"
            else "Unknown",
            **record,
        )
        if id in m.entities:
            e.created_at = m.entities[id].created_at
        e.revision = m.revision + 1
        m.entities[id] = e
        outputs = (
            record["outputs"]
            if record["status"] == "valid"
            else {
                "status": "invalid",
                "compliant": None,
                "margin": None,
                "errors": record["errors"],
            }
        )

        if tool in ["mass", "power", "data", "link"]:
            b = entity(
                f"{prefix}-{tool}",
                "Budget",
                f"{prefix} · {tool}",
                "tool",
                refs=[id],
                classification="Deterministic calculation"
                if record["status"] == "valid"
                else "Unknown",
                candidate=prefix,
                **outputs,
            )
            m.entities[b.id] = b
        claim = entity(
            f"{prefix}-{tool}-claim",
            "Claim",
            f"{prefix}: preliminary {tool} results",
            "tool",
            refs=[id],
            classification="Deterministic calculation"
            if record["status"] == "valid"
            else "Unknown",
            outputs=outputs,
            validity="Conditional on recorded assumptions",
        )
        m.entities[claim.id] = claim
        if tool == "mass":
            for previous in m.entities.values():
                if previous.kind == "BudgetEntry" and previous.id.startswith(
                    f"{prefix}-mass-entry-"
                ):
                    previous.state = "superseded"
            for index, entry in enumerate(record["outputs"].get("entries", [])):
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
        return outputs

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
            self.propose(m, "systems", architectures() + input_entities(), "architectures")
        elif phase == "Candidate concepts":
            self.calculate_design(m)
        elif phase == "Recalculation required":
            self.calculate_design(m)
        elif phase == "Selected concept":
            f = entity(
                "review-latency",
                "ReviewFinding",
                "Daily downlink capacity does not establish delivery latency",
                "review",
                refs=["req-latency", f"{m.selected}-link"]
                + (["mission-access-analysis"] if "mission-access-analysis" in m.entities else []),
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
                refs=["req-latency", "operations"]
                + (["mission-access-analysis"] if "mission-access-analysis" in m.entities else []),
                method="Orbit access and processing simulation",
                success_criterion=m.entities["req-latency"].title,
                status="not verified",
                evidence="Operational delivery remains unverified: modeled delivery is conditional on sampled access and assumed processing and station availability"
                if "mission-access-analysis" in m.entities
                else "Unknown: no propagated access evidence",
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
        guard_candidate(old, candidate)
        guard_interfaces(old)
        if any(
            old.entities[f"{candidate}-{tool}"].state != "accepted"
            or old.entities[f"{candidate}-{tool}"].data.get("compliant") is not True
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
        t.relations = [r for r in t.relations if r.target != "selection-trade-analysis"]
        t.relations.append(Relation(type="evidenced_by", target="selection-trade-analysis"))
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
            refs=["trade", f"{candidate}-link"]
            + [e.id for e in m.entities.values() if e.kind == "Interface"]
            + (
                [f"{candidate}-delivery-analysis"]
                if f"{candidate}-delivery-analysis" in m.entities
                else []
            )
            + (["mission-access-analysis"] if "mission-access-analysis" in m.entities else []),
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
                and e.state not in ["verified", "resolved", "closed", "waived", "superseded"]
            )
            for e in old.entities.values()
        ):
            raise ValueError("Stale objects or unresolved critical findings block baseline")
        if any(p.status in ["submitted", "challenged"] for p in old.proposals.values()):
            raise ValueError("Pending proposals block baseline")
        if not old.selected or any(
            old.entities[f"{old.selected}-{tool}"].state != "accepted"
            or old.entities[f"{old.selected}-{tool}"].data.get("compliant") is not True
            for tool in BUDGET_TOOLS
        ):
            raise ValueError("A current compliant concept must be selected")
        m = old.model_copy(deep=True)
        m.baseline = str(uuid4())
        guard_candidate(old, old.selected)
        guard_interfaces(old)
        refresh(m)
        refresh_interfaces(m)
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
        d.data["outstanding_requirements"] = [
            e.data["requirement"]
            for e in m.entities.values()
            if e.kind == "VerificationItem"
            and e.data.get("candidate") == m.selected
            and e.data.get("status") in ["unverified", "fail"]
        ]
        d.data["outstanding_interfaces"] = [
            e.data["interface"]
            for e in m.entities.values()
            if e.data.get("check_type") == "interface_consistency"
            and e.data.get("status") != "pass"
        ]
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

    def propose_study_trial(self, id, study_id, revision, trial_index, reason):
        from copy import deepcopy

        from app.engineering_tools.calculations import q
        from app.services.design_inputs import EditChanges
        from app.services.sensitivity import PARAMETERS

        old = self.store.get(id)
        self.guard(old, revision)
        self.no_pending(old)
        saved = self.store.study(id, study_id)
        result = saved["result"]
        trials = result["trials"]
        if trial_index < 0 or trial_index >= len(trials):
            raise ValueError("Choose a recorded trial from this study")
        trial = trials[trial_index]
        if trial["status"] != "valid":
            raise ValueError("Invalid trial results cannot propose a design change")
        candidate = result["candidate"]
        source = old.entities.get(f"{candidate}-delivery-analysis")
        reference = result["reference"]["delivery_analysis"]["inputs"]
        if (
            not source
            or source.state != "accepted"
            or source.data.get("status") != "valid"
            or source.data["inputs"] != reference
        ):
            raise ValueError(
                "Design assumptions differ from this study; run and save a new study before proposing a trial"
            )
        for group, tool in [("payload", "data"), ("link", "link"), ("delays", "delivery")]:
            if read_inputs(old, candidate, tool) != reference[group]:
                raise ValueError("Design inputs differ from the study; run and save a new study")
        group, field, unit = PARAMETERS[result["parameter"]]
        tool = {"payload": "data", "link": "link", "delays": "delivery"}[group]
        values = deepcopy(read_inputs(old, candidate, tool))
        if q(values[field], unit) == q(trial["value"], unit):
            raise ValueError("This trial already matches the accepted input")
        prior = deepcopy(values[field])
        values[field] = trial["value"]
        return self.edit(
            id,
            parameter_id(candidate, tool),
            revision,
            EditChanges(inputs=values),
            reason,
            source_study=dict(
                id=study_id,
                name=saved["name"],
                source_revision=result["source_revision"],
                trial_index=trial_index,
                candidate=candidate,
                parameter=result["parameter"],
                previous_value=prior,
                proposed_value=trial["value"],
            ),
        )

    def edit(self, id, object_id, revision, changes, reason, source_study=None):
        old = self.store.get(id)
        self.guard(old, revision)
        self.no_pending(old)
        prior = old.entities.get(object_id)
        if not prior or prior.state not in ["accepted", "stale"]:
            raise ValueError("Only accepted or stale design objects can be edited")
        if (
            any(e.kind == "AnalysisRun" for e in old.entities.values())
            and "mission-orbit-inputs" not in old.entities
        ):
            raise ValueError("Initialize editable inputs from recorded analyses first")
        e = edited_entity(prior, changes)
        p = Proposal(
            source_study=source_study,
            proposal_type="design change",
            agent="human",
            target_revision=old.revision,
            operations=[Operation(action="replace", entity=e)],
            rationale=reason,
            expected_consequences="Dependent results and decisions become stale; review and recalculation are required.",
            confidence=1,
        )
        validate(old, p)
        m = old.model_copy(deep=True)
        p.target_revision += 1
        m.proposals[p.id] = p
        return self.store.save(m, "human", f"Proposed edit to {object_id}: {reason}", old)

    @staticmethod
    def no_pending(m):
        if any(p.status in ["submitted", "challenged"] for p in m.proposals.values()):
            raise ValueError("Resolve pending proposals before changing the design")

    def require_recalculation(self, m):
        if any(e.kind == "AnalysisRun" for e in m.entities.values()):
            m.phase = "Recalculation required"
        else:
            m.phase = m.resume_phase or m.phase
        m.resume_phase = None

    def after_change(self, m):
        if m.phase not in ["Impact review", "Recalculation required"]:
            m.resume_phase = m.phase
        if any(e.state == "stale" and e.kind in IMPACT_KINDS for e in m.entities.values()):
            m.phase = "Impact review"
        else:
            self.require_recalculation(m)

    def review_impact(self, id, revision, reason, confirm):
        old = self.store.get(id)
        self.guard(old, revision)
        self.no_pending(old)
        if old.phase != "Impact review" or not confirm:
            raise ValueError("Explicit confirmation of affected design content is required")
        m = old.model_copy(deep=True)
        reviewed = []
        for e in m.entities.values():
            if e.state == "stale" and e.kind in IMPACT_KINDS:
                if e.kind == "Parameter":
                    from app.domain.engineering_inputs import validate_inputs

                    validate_inputs(e.data["tool"], e.data["inputs"])
                e.state = "accepted"
                reviewed.append(e.id)
        self.require_recalculation(m)
        decision = entity(
            str(uuid4()),
            "Decision",
            "Mission owner reviewed change impact",
            "human",
            refs=reviewed,
            classification="Human decision",
            rationale=reason,
            alternatives=["revise affected content", "reaffirm affected content"],
            consequences="Reaffirmed design content; numerical results still require recalculation",
        )
        m.entities[decision.id] = decision
        return self.store.save(m, "human", reason, old)

    def initialize_inputs(self, id, revision):
        old = self.store.get(id)
        self.guard(old, revision)
        self.no_pending(old)
        if "selective" not in old.entities or "mission-orbit-inputs" in old.entities:
            raise ValueError(
                "Input initialization is only for existing concepts without input objects"
            )
        m = old.model_copy(deep=True)
        self.propose(m, "systems", input_entities(old), "calculation inputs")
        return self.store.save(
            m, "systems", "Proposed explicit input objects from recorded sizing basis", old
        )

    def initialize_delivery(self, id, revision):
        old = self.store.get(id)
        self.guard(old, revision)
        self.no_pending(old)
        if "mission-access-inputs" not in old.entities or any(
            parameter_id(c, "delivery") in old.entities for c in CANDIDATES
        ):
            raise ValueError(
                "Delivery initialization requires access inputs and no existing delivery inputs"
            )
        m = old.model_copy(deep=True)
        self.propose(m, "systems", delivery_parameters(), "calculation inputs")
        return self.store.save(m, "systems", "Proposed delivery delays for explicit approval", old)

    def initialize_access(self, id, revision):
        old = self.store.get(id)
        self.guard(old, revision)
        self.no_pending(old)
        if "mission-access-inputs" in old.entities or "mission-orbit-inputs" not in old.entities:
            raise ValueError(
                "Access initialization requires editable orbit inputs and no existing access inputs"
            )
        m = old.model_copy(deep=True)
        self.propose(m, "systems", [access_parameter()], "calculation inputs")
        return self.store.save(
            m,
            "systems",
            "Proposed illustrative coverage and station assumptions for explicit approval",
            old,
        )

    def reopen(self, id, revision, reason):
        old = self.store.get(id)
        if old.archived:
            raise ValueError("Restore the archived mission to the active list before reopening")
        if old.revision != revision or not old.baseline:
            raise ValueError("Reopening requires the current approved baseline revision")
        m = old.model_copy(deep=True)
        m.derived_from_baseline = old.baseline
        m.baseline = None
        m.entities = {
            k: v for k, v in m.entities.items() if v.kind != "Baseline" and k != "baseline-approval"
        }
        m.phase = "Ready for baseline"
        return self.store.save(
            m, "human", f"Reopened baseline {old.baseline} as a new revision: {reason}", old
        )

    def calculate_design(self, m):
        if any(e.state == "stale" and e.kind in IMPACT_KINDS for e in m.entities.values()):
            raise ValueError("Review affected assumptions, requirements and design inputs first")
        # A recalculation never reuses a stale selection or independent review.
        for e in m.entities.values():
            if e.state == "stale" and e.kind in ["Decision", "VerificationItem", "ReviewFinding"]:
                e.state = "superseded"
            if e.id.startswith("selection-trade-"):
                e.state = "superseded"
        m.selected = None
        reqs = [
            e.id for e in m.entities.values() if e.kind == "Requirement" and e.state == "accepted"
        ]
        orbit = self.analysis(
            m,
            "orbit",
            read_inputs(m, "mission", "orbit"),
            [parameter_id("mission", "orbit"), "orbit-assumption"],
            "mission",
        )
        if "mission-access-inputs" in m.entities:
            self.analysis(
                m,
                "access",
                {
                    **read_inputs(m, "mission", "access"),
                    "altitude": read_inputs(m, "mission", "orbit")["altitude"],
                },
                ["mission-access-inputs", "mission-orbit-inputs", *reqs],
                "mission",
            )
        for candidate in CANDIDATES:
            for tool in BUDGET_TOOLS:
                values = read_inputs(m, candidate, tool)
                refs = [parameter_id(candidate, tool), candidate, *reqs]
                if tool == "power":
                    values.update(period=orbit.get("period"), eclipse=orbit.get("eclipse"))
                    refs.append("mission-orbit-analysis")
                if tool == "link":
                    values["demand"] = m.entities[f"{candidate}-data"].data.get("daily")
                    refs.append(f"{candidate}-data")
                result = self.analysis(m, tool, values, refs, candidate)
                key = f"{candidate}-conflict" if tool == "link" else f"{candidate}-{tool}-conflict"
                if result.get("compliant") is not True or key in m.entities:
                    finding = entity(
                        key,
                        "ReviewFinding",
                        "Payload production exceeds downlink capacity or RF link fails"
                        if tool == "link"
                        else f"{candidate}: {tool} constraint violation",
                        refs=[f"{candidate}-{tool}"],
                        severity="critical",
                        resolution="",
                        candidate=candidate,
                        tool=tool,
                        disciplines=[
                            "Payload: observation demand",
                            "Bus & Ground: resource availability",
                        ],
                    )
                    if result.get("compliant") is True:
                        finding.state = "verified"
                        finding.data["resolution"] = (
                            "Deterministic recalculation verifies compliance under the revised inputs"
                        )
                    else:
                        finding.state = "open"
                        if result.get("status") == "invalid":
                            finding.title = f"{candidate}: {tool} calculation is invalid"
                    m.entities[key] = finding
            if parameter_id(candidate, "delivery") in m.entities:
                access_run = m.entities.get("mission-access-analysis")
                access_output = (
                    access_run.data.get("outputs", {})
                    if access_run
                    and access_run.state == "accepted"
                    and access_run.data.get("status") == "valid"
                    else {}
                )
                self.analysis(
                    m,
                    "delivery",
                    dict(
                        delays=read_inputs(m, candidate, "delivery"),
                        payload=read_inputs(m, candidate, "data"),
                        link=read_inputs(m, candidate, "link"),
                        link_result=m.entities[f"{candidate}-link-analysis"].data.get(
                            "outputs", {}
                        ),
                        access={
                            k: access_output[k]
                            for k in ("horizon", "targets", "network_windows", "sample_step")
                            if k in access_output
                        },
                    ),
                    [
                        parameter_id(candidate, "delivery"),
                        parameter_id(candidate, "data"),
                        parameter_id(candidate, "link"),
                        f"{candidate}-link-analysis",
                        "mission-access-analysis",
                        *reqs,
                    ],
                    candidate,
                )
        for role, tools in [
            (
                "analysis",
                ["orbit", "access"] if "mission-access-inputs" in m.entities else ["orbit"],
            ),
            ("payload", ["data"]),
            ("bus", ["mass", "power", "link"]),
        ]:
            run = entity(
                str(uuid4()),
                "AgentRun",
                AGENTS[role].role + ": deterministic analysis",
                role,
                agent_version="1.0",
                model="deterministic mock",
                input_revision=m.revision,
                context_references=list(m.entities),
                tool_calls=tools,
                result="completed",
                tokens=0,
                cost=0,
            )
            m.entities[run.id] = run
        previous_trade = m.entities.get("trade")
        weights = (
            previous_trade.data["weights"]
            if previous_trade
            else {"science": 0.35, "capacity": 0.45, "simplicity": 0.2}
        )
        scores = {
            "wide": {"science": 5, "capacity": 0, "simplicity": 4},
            "selective": {"science": 3, "capacity": 0, "simplicity": 3},
        }
        for candidate in CANDIDATES:
            scores[candidate]["capacity"] = (
                5 if m.entities[f"{candidate}-link"].data.get("compliant") is True else 0
            )
        calculated = self.analysis(
            m,
            "trade",
            {"weights": weights, "scores": scores},
            ["wide-link", "selective-link"],
            "concept",
        )
        m.entities["trade"] = entity(
            "trade",
            "TradeStudy",
            "Compare the revised engineering concepts",
            refs=["concept-trade-analysis"],
            criteria=list(weights),
            weights=weights,
            scores=scores,
            recommendation=calculated["recommendation"],
            dissent="Payload favors complete images; event filtering risks missed weak anomalies.",
            sensitivities="Science and simplicity are estimates; capacity scores follow current tool results.",
            alternatives=list(CANDIDATES),
            score_basis="Engineering estimates on a 0–5 scale; capacity scored by deterministic compliance",
        )
        refresh(m)
        refresh_interfaces(m)
        m.phase = "Trade study"
