# Delivery sensitivity studies

`POST /api/missions/{id}/sensitivity` is a read-only calculation endpoint protected by the normal mission-owner authorization. Its request identifies the current revision, candidate, a supported parameter, 2–15 distinct unit-bearing values and an optional exploratory deadline. The source must be an accepted, valid delivery AnalysisRun. Saved baselines can be studied without reopening or changing them.

Supported fields: payload storage, link rate, onboard delay, ground-processing delay and dissemination delay. Values use the existing engineering validation; equivalent values such as 60 seconds and 1 minute are duplicates. A study is bounded to 50,000 product cases across reference plus trials. This is a one-parameter sweep, not a coupled optimization or uncertainty model.

The source run's recorded input bundle is copied for each calculation. The selected field changes; geometry and other assumptions stay fixed. Both the reference and every trial rerun daily data generation, RF link and delivery. Changing link rate therefore changes Eb/N0 and can disable downlink when RF margin becomes negative. Failures remain invalid records. Conditional deadline logic is shared with delivery verification, so incomplete/no-observation cases cannot falsely pass.

The response records schema/tool versions, timestamp, mission and baseline identity, source revision and analysis revision, each trial quantity, full calculator input/output/error evidence, exploratory deadline outcomes, and separate comparisons against accepted numeric delivery criteria. The optional study deadline is never written into a requirement. Existing verification items, input groups, history, selection and baseline exports remain unchanged.

The UI holds one unsaved study and exports the response as JSON. Changing settings clears unsaved results; changing mission/revision remounts the view so a delayed response cannot populate a different source. Navigating away discards the unsaved result. To retain a study, save it by name or export it; to adopt a value, use the normal reviewed Design inputs edit flow, reopening a baseline if necessary.

All delivery workload, station-availability and sampling limitations remain applicable. Results are conditional comparisons, not operational verification. Multi-parameter grids, Pareto optimization and automatic recommendation/adoption are outside this slice.

## Saved evidence

`POST /api/missions/{id}/sensitivity-studies` accepts a name and typed study request, never a supplied result. It reruns the study from current evidence and writes the complete response to a separate immutable `sensitivity_studies` table. Source revision is checked before calculation and again at insertion; archived missions reject new saves. Saving does not increment the mission revision or modify approved inputs or baselines. Every save receives a unique ID and creation timestamp; names need not be unique. Saved records cannot be edited or deleted through the API.

Mission-scoped list/detail endpoints retrieve saved evidence without recalculation. They remain readable for archived missions. ORM hooks reject update/delete; Alembic migration 0002 adds PostgreSQL/SQLite database triggers as well. Run `alembic upgrade head` before serving the new endpoints on an existing installation; `scripts/dev.sh` does this automatically. The table is additive and destructive downgrades are intentionally unsupported.

The saved-study library loads one or two records with source revision, candidate, varied parameter, horizon and exploratory deadline. Different source revisions/candidates/parameters/deadlines are called out; the comparison does not assert causal improvement across changed designs. Historical records are explicitly labeled and remain exportable, including full RF/per-product evidence and accepted-criterion comparisons. Selected records clear while loading; abandoned requests cannot overwrite a newer selection or another mission.

## Reviewed trial proposals

`POST /api/missions/{id}/sensitivity-studies/{study_id}/propose` accepts the current mission revision, a zero-based trial index and a rationale. The server resolves candidate, field and value from the immutable mission-scoped study. It accepts only valid trial calculations, rejects semantically unchanged quantities, and requires an accepted valid current delivery run whose input bundle matches the recorded study reference, as well as matching accepted payload/link/delay input groups. Exact recorded-unit/input equality is conservative: even physically equivalent reformatted input groups may require a fresh study.

Archived missions, active baselines and pending proposals use the existing workflow guards. Reopen a baseline before proposing a trial; its unchanged calculation evidence remains eligible despite the new mission revision. A changed design must be recalculated and studied again. The proposal updates only the varied input and preserves every other current quantity. Exploratory pass/fail does not authorize the change and is never copied into verification evidence.

The UI displays current/proposed quantities and collects a rationale, then submits a normal design-change proposal. `Proposal.source_study` records study ID/name, source revision, trial index, candidate, parameter and previous/proposed values. Generic agent submission cannot supply study provenance. No accepted input changes until human approval; rejection leaves the design intact. Approval uses the existing dependency invalidation, recalculation and independent review workflow. Saved study records and approved historical snapshots remain unchanged. The optional proposal field is backward-compatible and requires no additional database migration.
