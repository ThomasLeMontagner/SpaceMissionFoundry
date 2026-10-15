import { fireEvent, render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";
import ImpactAssumptions, {
  emptyImpact,
  impactPayload,
} from "./ImpactAssumptions";

test("impact coefficients require explicit input and explain the incremental basis", () => {
  const onChange = vi.fn();
  render(<ImpactAssumptions value={emptyImpact} onChange={onChange} />);
  const storage = screen.getByLabelText("Storage mass (kg/Gbit)");
  expect(storage).toBeRequired();
  expect(storage).toHaveValue(null);
  expect(
    screen.getByLabelText("Assumption basis and applicability"),
  ).toBeRequired();
  expect(
    screen.getByText(/reductions receive no savings credit/),
  ).toBeVisible();
  fireEvent.change(storage, { target: { value: "0.1" } });
  expect(onChange).toHaveBeenCalledWith({
    ...emptyImpact,
    storage_kg_per_gbit: "0.1",
  });
  expect(
    impactPayload({
      storage_kg_per_gbit: ".1",
      storage_w_per_gbit: ".2",
      observation_w: "10",
      processing_w_per_ratio: "1",
      basis: "Explicit hypothetical values",
    }),
  ).toEqual({
    storage_kg_per_gbit: 0.1,
    storage_w_per_gbit: 0.2,
    observation_w: 10,
    processing_w_per_ratio: 1,
    basis: "Explicit hypothetical values",
  });
});
