export const emptyImpact = {
  storage_kg_per_gbit: "",
  storage_w_per_gbit: "",
  observation_w: "",
  processing_w_per_ratio: "",
  basis: "",
};
export type ImpactDraft = typeof emptyImpact;
export function impactPayload(value: ImpactDraft) {
  return {
    ...value,
    storage_kg_per_gbit: Number(value.storage_kg_per_gbit),
    storage_w_per_gbit: Number(value.storage_w_per_gbit),
    observation_w: Number(value.observation_w),
    processing_w_per_ratio: Number(value.processing_w_per_ratio),
  };
}
export default function ImpactAssumptions({
  value,
  onChange,
}: {
  value: ImpactDraft;
  onChange: (value: ImpactDraft) => void;
}) {
  return (
    <fieldset>
      <legend>Incremental mass and power assumptions</legend>
      <p>
        Enter estimates and their basis. No hardware defaults are supplied.
        Increases add costs relative to accepted inputs; reductions receive no
        savings credit. Processing workload depends on duty × (compression − 1).
        Added active loads are assumed to coincide with eclipse for its full
        duration. Coefficients stay fixed for this study; zero explicitly
        assumes no incremental cost.
      </p>
      {(
        [
          ["storage_kg_per_gbit", "Storage mass (kg/Gbit)", 1000],
          ["storage_w_per_gbit", "Storage power (W/Gbit)", 1000],
          ["observation_w", "Additional observation active power (W)", 1000000],
          [
            "processing_w_per_ratio",
            "Processing active power per compression-ratio increment (W)",
            1000000,
          ],
        ] as const
      ).map(([key, label, max]) => (
        <label key={key}>
          {label}
          <input
            type="number"
            required
            min="0"
            max={max}
            step="any"
            value={value[key]}
            onChange={(e) => onChange({ ...value, [key]: e.target.value })}
          />
        </label>
      ))}
      <label>
        Assumption basis and applicability
        <textarea
          required
          minLength={3}
          maxLength={1000}
          value={value.basis}
          onChange={(e) => onChange({ ...value, basis: e.target.value })}
        />
      </label>
    </fieldset>
  );
}
