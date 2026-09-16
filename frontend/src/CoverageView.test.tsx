import { fireEvent, render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";
import CoverageView from "./CoverageView";
import type { Model } from "./types";

test("stale and failed access calculations cannot display a current ground track", () => {
  const model = {
    entities: {
      "mission-access-inputs": { id: "mission-access-inputs" },
      "mission-access-analysis": {
        id: "mission-access-analysis",
        state: "stale",
        data: {
          status: "valid",
          outputs: { ground_track: [{ latitude: 0, longitude: 0 }] },
        },
      },
    },
  } as unknown as Model;
  const view = render(
    <CoverageView
      model={model}
      busy={false}
      onInitialize={vi.fn()}
      onInspect={vi.fn()}
    />,
  );
  expect(screen.getByText(/Stale — review/)).toBeInTheDocument();
  view.rerender(
    <CoverageView
      model={model}
      busy={true}
      onInitialize={vi.fn()}
      onInspect={vi.fn()}
    />,
  );
  expect(
    screen.getByRole("button", { name: "Inspect or edit coverage inputs" }),
  ).toBeDisabled();
  expect(screen.queryByRole("img")).not.toBeInTheDocument();
  model.entities["mission-access-analysis"].state = "accepted";
  model.entities["mission-access-analysis"].data.status = "invalid";
  model.entities["mission-access-analysis"].data.errors = ["Invalid orbit"];
  view.rerender(
    <CoverageView
      model={model}
      busy={false}
      onInitialize={vi.fn()}
      onInspect={vi.fn()}
    />,
  );
  expect(
    screen.getByText(/Calculation invalid: Invalid orbit/),
  ).toBeInTheDocument();
  expect(screen.queryByRole("img")).not.toBeInTheDocument();
});

test("legacy missions offer explicit input approval and baselines require reopening", () => {
  const onInitialize = vi.fn();
  const model = {
    entities: { "mission-orbit-inputs": {} },
    baseline: null,
  } as unknown as Model;
  const view = render(
    <CoverageView
      model={model}
      busy={false}
      onInitialize={onInitialize}
      onInspect={vi.fn()}
    />,
  );
  fireEvent.click(
    screen.getByRole("button", { name: "Propose coverage inputs" }),
  );
  expect(onInitialize).toHaveBeenCalledOnce();
  view.rerender(
    <CoverageView
      model={{ ...model, baseline: "approved" }}
      busy={false}
      onInitialize={onInitialize}
      onInspect={vi.fn()}
    />,
  );
  expect(
    screen.queryByRole("button", { name: "Propose coverage inputs" }),
  ).not.toBeInTheDocument();
  expect(screen.getByText(/Reopen the baseline/)).toBeInTheDocument();
});
