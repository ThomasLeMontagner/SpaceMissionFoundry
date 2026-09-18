import { render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";
import DeliveryView from "./DeliveryView";
import type { Model } from "./types";

test("delivery hides stale and failed evidence and requires explicit legacy setup", () => {
  const model = {
    entities: {
      "mission-access-inputs": { data: {} },
      "selective-delivery-analysis": {
        id: "selective-delivery-analysis",
        state: "stale",
        data: { status: "valid", outputs: {} },
      },
    },
  } as unknown as Model;
  const view = render(
    <DeliveryView
      model={model}
      busy={true}
      onInitialize={vi.fn()}
      onInspect={vi.fn()}
    />,
  );
  expect(screen.getByText(/Stale — review changes/)).toBeInTheDocument();
  expect(screen.queryByRole("table")).not.toBeInTheDocument();
  expect(
    screen.getByRole("button", { name: "Propose delivery inputs" }),
  ).toBeDisabled();
  model.entities["selective-delivery-analysis"].state = "accepted";
  model.entities["selective-delivery-analysis"].data.status = "invalid";
  model.entities["selective-delivery-analysis"].data.errors = [
    "No valid RF evidence",
  ];
  view.rerender(
    <DeliveryView
      model={{ ...model, baseline: "saved" }}
      busy={false}
      onInitialize={vi.fn()}
      onInspect={vi.fn()}
    />,
  );
  expect(
    screen.getByText(/Calculation invalid: No valid RF evidence/),
  ).toBeInTheDocument();
  expect(screen.getByText(/Reopen the baseline/)).toBeInTheDocument();
  expect(screen.queryByRole("table")).not.toBeInTheDocument();
  expect(
    screen.queryByRole("button", { name: "Propose delivery inputs" }),
  ).not.toBeInTheDocument();
});
