# Delivery sensitivity studies

`POST /api/missions/{id}/sensitivity` is a read-only calculation endpoint protected by the normal mission-owner authorization. Its request identifies the current revision, candidate, a supported parameter, 2–15 distinct unit-bearing values and an optional exploratory deadline. The source must be an accepted, valid delivery AnalysisRun. Saved baselines can be studied without reopening or changing them.

Supported fields: payload storage, link rate, onboard delay, ground-processing delay and dissemination delay. Values use the existing engineering validation; equivalent values such as 60 seconds and 1 minute are duplicates. A study is bounded to 50,000 product cases across reference plus trials. This is a one-parameter sweep, not a coupled optimization or uncertainty model.

The source run's recorded input bundle is copied for each calculation. The selected field changes; geometry and other assumptions stay fixed. Both the reference and every trial rerun daily data generation, RF link and delivery. Changing link rate therefore changes Eb/N0 and can disable downlink when RF margin becomes negative. Failures remain invalid records. Conditional deadline logic is shared with delivery verification, so incomplete/no-observation cases cannot falsely pass.

The response records schema/tool versions, timestamp, mission and baseline identity, source revision and analysis revision, each trial quantity, full calculator input/output/error evidence, exploratory deadline outcomes, and separate comparisons against accepted numeric delivery criteria. The optional study deadline is never written into a requirement. Existing verification items, input groups, history, selection and baseline exports remain unchanged.

The UI holds one temporary study and exports the response as JSON. Changing settings clears results; changing mission/revision remounts the view so a delayed response cannot populate a different source. Navigating away discards the temporary result. To retain a study, export it; to adopt a value, use the normal reviewed Design inputs edit flow, reopening a baseline if necessary.

All delivery workload, station-availability and sampling limitations remain applicable. Results are conditional comparisons, not operational verification. Persistent study management, multi-parameter grids, Pareto optimization and automatic recommendation/adoption are outside this slice.
