# Preliminary coverage and access model

The `access` tool is deterministic, bounded and offline. The workbench presents its recorded outputs and provenance; it does not obtain live ephemerides or station schedules. Both candidate architectures share the explicit geometry. Default target coordinates are illustrative points near Portugal, Italy and Greece; the Madrid station is hypothetical. They are approved assumptions, not verified service locations or area-coverage evidence.

## Geometry

Earth is a sphere with radius 6,371,000 m. The circular-orbit radius is Earth radius plus accepted orbit altitude, with gravitational parameter 3.986004418e14 m³/s². Orbital argument increases at `sqrt(mu / radius³)`. The orbital plane is rotated by inclination and ascending node; the Earth-fixed node angle subtracts the user-supplied initial Earth angle and constant Earth rotation `7.292115e-5 rad/s × elapsed time`. This is a relative-epoch two-body model, not SGP4, an absolute-time ephemeris, or a sun-synchronous propagation model.

The circular element-to-position rotations and Earth-rotation subtraction are a simplification of the coordinate formulation documented in [ESA Navipedia: GPS and Galileo satellite coordinates](https://gssc.esa.int/navipedia/index.php/GPS_and_Galileo_Satellite_Coordinates_Computation). We omit eccentricity, broadcast corrections and perturbations and do not claim the accuracy quoted for broadcast GNSS ephemerides.

Point targets and stations are represented by unit surface normals from latitude/longitude. Station elevation is the arcsine of the normalized station-to-satellite line dotted with the station's outward normal. This follows the common-frame/topocentric observer geometry described in [CelesTrak: Orbital Coordinate Systems, Part II](https://www.celestrak.org/columns/v02n02/). Stations are assumed at sea level; Earth oblateness, terrain and refraction are omitted.

A target is inside a circular, nadir-centred surface footprint when its central angular distance from the sub-satellite point is at most half the declared footprint diameter divided by Earth radius. That cap is clipped at the geometric horizon. This footprint is not a calibrated payload field of view, swath or pointing model.

## Sampling and interpretation

The horizon is divided into equal cells no larger than the requested step and geometry is tested at each midpoint. Contiguous visible cells become windows; their boundaries are cell boundaries with sample-scale uncertainty. Very short passes may be missed entirely. Windows touching the horizon edges are marked truncated. Ground-track display is downsampled to approximately 2,000 points, independently of the calculation resolution.

For each target, the largest gap includes horizon-edge intervals. Zero observed windows yields the horizon length; fewer than two windows yields unknown revisit. Observed revisit is start-to-start between windows, not a long-term or guaranteed revisit. Observed fraction is the fraction of configured target points visited at least once, not regional area coverage. Network contact is the union of station visibility cells; overlapping stations are never double-counted. Normalized daily contact is an average over the analysis horizon, not a minimum guaranteed every day.

The optional opportunity-wait result takes observation-window starts and the next network contact interval. It is unknown if no observations exist or any observation lacks later contact within the horizon. It is an optimistic scheduling opportunity, not acquisition-to-user delivery latency. Transmission duration, data queueing, concurrent traffic, onboard/ground processing and dissemination are not modelled. The existing latency requirement remains unverified. Link-budget contact assumptions are not automatically replaced.

## Inputs, limits and evidence

`mission-access-inputs` contains typed geometry/site inputs; altitude is supplied from `mission-orbit-inputs` at calculation time. The [access schema](access-inputs.schema.json) documents structure; runtime validation additionally enforces compatible units, angular ranges, unique names, horizon/work limits and footprint bounds. Runs support 100–2000 km altitude, 1 minute–7 days, 1–60 second steps, at most 100,000 samples, 12 targets and 8 stations.

The tool records input values, effective step, constants in code version 1.0, outputs, warnings and source revision. Analysis, claims, criteria and downstream decisions use typed dependencies for staleness. Invalid executions have no fabricated outputs. Optional access criteria use the shared mission analysis and remain conditional on sampling and finite-horizon limits. Existing baselines are not migrated; adding this capability to a legacy mission requires an approved input proposal and fresh calculation.

## Verification

Analytic tests cover overhead elevation, the horizon angle `acos(Earth radius / orbit radius)`, Earth rotation over one orbital period, polar latitude, and equatorial repeat time `2*pi / (orbital rate - Earth rotation rate)`. Sampling-refinement tests bound contact-time changes by the coarse step in the controlled case. Additional tests cover disjoint/no access, co-located station union, stricter elevation masks, signed coordinates, compatible units, resource bounds, failure-to-unverified propagation, stale state, explicit legacy initialization and unchanged historical baselines.
