# Mission Foundry

A local, model-centered conceptual mission engineering workbench. Six versioned discipline roles propose a wildfire-monitoring CubeSat concept, deterministic tools analyze approved inputs, and a human approves an immutable concept baseline.

The reference workflow supports resource budgets, preliminary coverage and ground access, conditional data delivery, quantitative requirement checks, declared data-interface checks, saved sensitivity studies, baseline comparison and reversible mission archiving. See [setup](#run-without-docker), the [workflow walkthrough](#demonstrate-the-vertical-workflow), and [scope and limitations](#scope-and-limitations).

## Delivery sensitivity studies

Open **Sensitivity analysis** after calculating delivery results to compare storage, downlink rate or processing-delay choices. Choose a candidate, vary one input, enter 2–15 distinct comma-separated values with compatible units, and run the study. An optional exploratory deadline highlights missed or unresolved deliveries without changing requirements. Studies work directly on saved baselines. Enter a **Study name** and click **Save study** to retain the evidence; use **Saved studies** below to reopen or compare two saved runs, or export JSON. Saving leaves your mission and baseline unchanged. Unsaved results are discarded when leaving the view or changing settings. See [sensitivity scope and limits](docs/architecture/sensitivity-analysis.md).

To use a saved study result, open it under **Sensitivity analysis → Saved studies**, then choose **Propose trial** beside the desired value. Reopen a baseline first if necessary. Review the current/proposed quantities, enter a rationale, and submit the proposal; the normal **Approve design change** step applies it and triggers recalculation. If the source assumptions have changed, run and save a new study before proposing its result. Saved evidence and old baselines remain unchanged.

## Data interface checks

Open **Interfaces** to inspect declared sender/receiver compatibility. Select **Inspect or edit interface contract → Edit interface data contract**, declare each endpoint's protocol and peak-rate/capacity limits, then submit and approve the change. Recalculation runs automatically while the workflow is running; if paused, resume to refresh the checks. Blank values remain unverified. Failed or stale checks block concept selection and baseline approval; unknown checks remain outstanding in a conceptual baseline. Reopen a baseline before editing. Existing missions may initially show “Checks have not been recorded”; define and approve a contract to record checks, leaving unknown specifications blank. These checks cover declared data compatibility, not physical hardware verification; [scope and evidence](docs/architecture/interface-checks.md).

## Archive and restore saved missions

Use **Archive** beside a saved mission, or **Archive mission** inside its workspace, and confirm the action. It disappears from the active list. Select **Show archived missions** and **Restore** to bring it back. Archiving keeps the mission's workflow, pending proposals, history and immutable baseline exports; it does not permanently delete any data. Archived missions cannot be edited until restored. Both actions are recorded in history.

## Preliminary coverage and ground access

Open **Coverage & access** to view a sampled ground track, target observation windows, revisit observations, and ground-station visibility. New missions propose explicit coverage assumptions with their architectures. For an older mission without coverage inputs, reopen its baseline if necessary and select **Propose coverage inputs**, review the illustrative point targets and hypothetical station, and approve the proposal. The setup button is absent when those inputs already exist. The calculation uses altitude from the accepted orbit input group.

Use **Inspect or edit coverage inputs** to change inclination, orbit/relative-epoch angles, analysis horizon, sample step, footprint diameter, station elevation mask, or add/remove named targets and stations. Latitude and longitude accept negative values and degrees/radians. Approval invalidates dependent results; stale ground tracks stay hidden until recalculation. Three finite-horizon metrics are available in quantitative requirement checks: network contact, observed target fraction, and largest target gap.

This is a bounded circular-orbit, spherical-Earth geometry model. It assesses configured points, not full regional area coverage. Sampling can miss short passes; run a finer step to assess sensitivity. Daily contact is a horizon-average; it does not replace approved link-budget contact assumptions. Geometry alone does not verify delivery latency. The [method and limitations](docs/architecture/access-analysis.md) explain the assumptions and reference equations.

## Conditional data delivery

Open **Data delivery** for each candidate's onboard queue, contact-limited transmissions, processing delays and per-product delivery outcomes. New missions include delivery inputs in their architecture proposal. Older missions without those inputs show **Propose delivery inputs** after coverage inputs exist (reopen a baseline first). The button is absent when delivery inputs are already configured. Review and approve the illustrative delays, then recalculate. **Configure latency requirement** opens the requirement: explicitly set the maximum acquisition-to-delivery metric, `<=`, and a threshold such as `30 minute` if that is the intended requirement. Review affected design content when prompted. Prose alone does not set the deadline. Dropped or overdue products fail; pending, truncated or absent observations cannot produce a full-workload pass. See the [delivery model and limits](docs/architecture/delivery-analysis.md).

## Compare saved baselines

Open **Baselines & replay → Compare saved baselines**, choose the **From** and **To** snapshots, then select **Compare baselines**. Expand a changed object to see stored field values side by side. Filter by object type or search for a requirement, input, result or decision. Added and removed objects are included; comparison direction follows your selections.

Audit timestamps and revision provenance are hidden by default and can be included with the checkbox. Values retain their recorded units: comparison reports stored differences, not recalculated margins or physical equivalence. Comparing a baseline with itself shows no differences. This view reads immutable exports and does not restore or modify the working design.

## Quantitative requirement checks

Open a requirement and choose **Edit requirement**. Under **Quantitative verification**, select a measured output, an upper/lower comparison, and a threshold with units. Update the statement and rationale to match the criterion, then propose and approve the change. Complete any requested impact review; recalculation refreshes the per-candidate pass/fail/stale/unverified results. Open a result to inspect its recorded calculation evidence.

Supported outputs cover mass, power/energy margins, daily data and downlink capacity, orbit period/eclipse duration, geometric network contact, observed target fraction, largest sampled target gap, and maximum modeled acquisition-to-delivery latency. Compatible units such as grams and kilograms are converted. Missing or failed evidence remains unverified. Failed or stale must-priority criteria block selection and baseline approval; conceptual baselines explicitly retain outstanding obligations. Criteria do not replace resource-budget checks or infer meaning from prose. Mission requirements are not automatically assigned quantitative criteria, and earlier baseline exports remain unchanged.

## Run with Docker Compose

```bash
cp .env.example .env
docker compose up --build
```

Open [the workbench](http://localhost:5173). Compose runs PostgreSQL 16, applies Alembic migrations, and starts the API and React workbench. Only the frontend port is published, bound to localhost. The default mock workflow requires no API key. The development database password in Compose is public and local-only; do not deploy this configuration publicly. Compose configuration has been validated, but the full container build/start path has not been exercised; see the [validation record](docs/validation.md).

## Run without Docker

From this directory, Python 3.12+ and Node 22+:

```bash
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.lock
.venv/bin/pip install --no-deps -e backend
npm ci --prefix frontend
cd backend
../.venv/bin/alembic upgrade head
../.venv/bin/uvicorn app.api.main:app --host 127.0.0.1 --port 8000
```

In a second terminal from the repository root:

```bash
npm run dev --prefix frontend
```

After installing dependencies, `./scripts/dev.sh` is a single-command alternative that applies migrations and starts both services. Stop any existing local servers before using it. Restart the backend after pulling backend changes; this command does not enable automatic backend reload.

Open [the local workbench](http://127.0.0.1:5173). This path uses SQLite in `backend/mission-foundry.db`; export `DATABASE_URL` before migration and startup to use PostgreSQL. [API documentation](http://127.0.0.1:8000/docs) is available on the backend. Schema creation is performed by migrations, never implicitly at production startup. Existing installations must apply `alembic upgrade head` from `backend` with the project virtual environment before starting the API; the commands above and `scripts/dev.sh` include this step. Native startup reads process environment variables, not the Compose `.env` file automatically.

## Demonstrate the vertical workflow

1. Create the prefilled reference mission. Review the scope and other assumptions, enter a decision rationale, and approve them.
2. Advance, inspect and approve the requirement proposal. Advance, inspect and approve the architecture proposal.
3. Advance to run orbit, mass, power/energy, data and RF/downlink tools, shared coverage/access analysis, per-candidate delivery simulation, and requirement/interface checks. Candidate A produces 43.2 Gbit/day but can downlink only 1.68 Gbit/day. Candidate B produces 8.64 Gbit/day and has 16.8 Gbit/day capacity under the reference assumptions. Undeclared numeric criteria and interface contracts remain unverified.
4. Open Trades. Inspect estimated scores and adjust weights (nonnegative, sum to one). Resolve any pending proposals before selecting candidate B. A is not selectable because it violates the downlink constraint; its dissent and failed analysis remain in the model.
5. Return to Overview. Run independent review. Propose the evidence-defect resolution, then verify it independently.
6. Open Baselines & replay. Acknowledge residual risks and explicitly approve the immutable conceptual baseline.
7. Export Markdown, JSON and CSV. Load the replay timeline, inspect an earlier snapshot, compare changed objects, or restore as a **new** revision.

Click any model object to inspect attributes, classification and both directions of traceability. Budget details link to their analysis execution, units, inputs, tool version and source revision. Proposal content has a separate pending presentation. Rejected proposals remain in history and can be regenerated by advancing. Challenges remain pending until explicitly reviewed.

## Iterate on an approved design

1. In **Baselines & replay**, choose **Reopen baseline for design changes**. This creates a new working revision; the original baseline stays immutable.
2. Open **Design inputs**, select **selective · data inputs**, and choose **Edit calculation inputs**. Change the observation duty cycle from `0.02` to `0.10`, provide a rationale, and propose the change.
3. Inspect the before/after comparison and approve **design change**. The workbench automatically recalculates accepted inputs when running. The saved intermediate revision retains stale flags and the audit trail. While paused, results remain stale until you resume or explicitly recalculate.
4. The new 43.2 Gbit/day demand exceeds candidate B's 16.8 Gbit/day capacity. The conflict reopens and selection is blocked.
5. Propose `120 minute` daily contact in **selective · link inputs**. After approval, capacity recalculates to 50.4 Gbit/day. This is still an explicit ground-network assumption, not verified access or latency evidence.
6. Select the compliant concept again, run independent review and verification, and explicitly approve a newly named baseline. **Load baseline history** to export either baseline.

Assumptions and requirements have editors in their detail panels. Their changes can invalidate narrative design objects or other inputs. **Review affected design content** requires explicit human reaffirmation before recalculation. Editing requirement text does not silently translate it into numerical limits: review the linked input groups and propose quantity changes separately.

Editable inputs cover both candidates' mass entries/allocations, power loads/mode fractions/solar/battery assumptions, data rate/duty/compression/storage, RF/link/contact inputs, delivery delays, common orbit altitude and coverage/access settings. Interface data contracts and numeric requirement criteria use the same reviewed change process. Period, eclipse and downlink demand are derived by tools and cannot be overridden. Original compatible units (including percent) are retained. Missing or unreviewed required input groups block recalculation; failed resource-budget calculations block selection, while missing or failed verification evidence remains unverified.

For missions created before editable input groups existed, reopen the baseline and use **Initialize editable inputs**. Review and approve the proposal reconstructed from recorded analysis inputs; no historical snapshots are rewritten and missing historical inputs are never replaced with defaults.

## Validation

```bash
.venv/bin/ruff check backend
.venv/bin/ruff format --check backend
.venv/bin/pytest backend/tests -q
npm run build --prefix frontend
npm test --prefix frontend
npm run format:check --prefix frontend
npm run e2e --prefix frontend
```

Playwright uses `CHROME_PATH` when set, otherwise `/usr/bin/google-chrome` if present, otherwise Playwright's Chromium. If neither browser is installed, run `cd frontend && npx playwright install --with-deps chromium` before the browser suite, then return to the repository root. Its configuration starts isolated servers on ports 5174/8011 and migrates `/tmp/mission-foundry-iteration-e2e.db`, leaving the normal app on ports 5173/8000 untouched. Backend tests use isolated SQLite databases by default; browser workflows create uniquely named missions in their separate database. The suite covers the core workflow, design iteration and baseline comparison, requirement criteria, coverage/delivery, archiving, saved sensitivity studies/trial proposals, and interface checks.

The latest local validation recorded 95 backend tests passed (one PostgreSQL-only skip), 22 frontend tests passed and seven browser workflows passed. These are recorded results, not a claim of a fresh run on every checkout. The parallel browser run logged transient SQLite lock errors despite passing; see the validation record. To exercise PostgreSQL locally, migrate a dedicated test database using `DATABASE_URL`, then set `TEST_DATABASE_URL` to the same connection URL when running pytest, as shown in [.github/workflows/ci.yml](.github/workflows/ci.yml). Tests create persistent test records and exercise database immutability protections. See [validation history and limits](docs/validation.md).

`scenarios/run_reference.py` creates a complete reproducible acceptance run and writes sample model/report artifacts to `scenarios/output/`. Its human actions are explicitly simulated test inputs, not autonomous production approvals:

```bash
.venv/bin/python scenarios/run_reference.py
```

## Security and model-provider configuration

The default is a **single-owner, public local demo**. For non-public data set `DEMO_MODE=false` and provide `MISSION_OWNER_TOKEN` through the process environment. Enter that token in the workbench access panel. It is held only in browser memory; requests use an Authorization header, including event streams and exports. This is not multi-user identity or tenant authorization.

The provider-neutral `Provider` interface has a deterministic mock and an optional OpenAI-compatible adapter. To opt in, set `LLM_PROVIDER=openai-compatible`, `LLM_BASE_URL`, `LLM_MODEL`, `LLM_API_KEY`, `LLM_MAX_PRICE_PER_MILLION`, and a positive `MAX_RUN_COST_EUR`. The real adapter can refine proposal rationale only; it cannot change scenario operations. It has a 30-second HTTP timeout, an output-token cap of 512 (reducible with `MAX_LLM_TOKENS`, minimum 64), and a conservative per-call cost preflight. The optional adapter is not a general autonomous mission designer; its HTTP contract is mock-tested but has not been exercised against a paid provider. Aggregate billing/token accounting is deferred. Compose defaults to the mock; to use the real adapter, add its required variables to the backend service's environment mapping in `docker-compose.yml`. Setting them only in the host environment or `.env` does not pass unmapped variables into the container.

No generated code is executed. Tools are an allowlisted collection of pure functions with Pint dimensional validation. Imported mission text is stored as data, never used to redefine agent instructions. Agent proposals cannot become calculated conclusions or impersonate human decisions. The API has no arbitrary SQL, shell, code execution, or evidence-fetching endpoint.

## Scope and limitations

This is a working **reference-scenario vertical MVP**, not completion of every Must in the long-term specification. See [requirement traceability](docs/requirements-traceability.md) for per-ID status and [architecture](docs/architecture/overview.md).

- Natural-language text is retained, but deterministic patterns identify reference constraints and missing information; the mock proposes a fixed reference sizing basis and explicitly requests approval of that scope. General extraction and arbitrary mission templates remain deferred; reference sizing inputs, assumptions and requirements can be revised explicitly.
- All hardware, contacts, detection performance, scores and costs are labelled assumptions/estimates. Circular-orbit eclipse is a worst-case geometric estimate, not a propagated mission-access solution.
- Daily capacity does **not** establish 30-minute delivery. Independent review retains a verification obligation for the reference claim. Conditional delivery simulation can check an explicitly configured numeric deadline for the modeled workload; it does not certify operational latency or station availability.
- Preliminary coverage and revisit results apply to configured points within a sampled finite horizon, not complete regional coverage. Declared interface protocol/rate checks do not verify electrical, timing, packet-format, power, thermal or mechanical compatibility.
- The user approves a conceptual study, not flight readiness. Operational coverage/revisit and delivery validation, lifetime, cost closure, thermal and pointing analyses remain open.
- Common entity metadata is typed and selected entity payloads require key fields. A fully discriminated schema for every engineering payload is deferred.
- No graph database, arbitrary import, branch merging, multi-user editing, supplier retrieval, high-fidelity orbit simulation or autonomous baseline approval.
- Revision snapshots prioritize auditable correctness over storage efficiency. No 10,000-object performance claim is made.
- Workflow steps are short synchronous transactions run in FastAPI's worker pool. SSE reports committed progress. Pause controls future steps, not interruption of a calculation already running. Durable distributed jobs and full elapsed/token/cost accounting are deferred.

[mission-foundry-requirements.md](mission-foundry-requirements.md) is the evolving requirements specification, updated as features are developed. Earlier versions remain available in Git history; [requirement traceability](docs/requirements-traceability.md) records implementation status.

See [the validation record](docs/validation.md) for executed checks and explicit limits, and [the JSON schema](docs/architecture/mission-model.schema.json) for the versioned export format.

GitHub Actions is configured to run lint/format checks, SQLite and migrated PostgreSQL regression suites, the frontend build/tests, and the full Playwright suite on pushes and pull requests. The workflow has read-only repository permissions and uses no paid model credentials. Local validation does not establish the status of a hosted Actions run.
