import { act, fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, expect, test, vi } from "vitest";
import { request } from "./api";
import SavedStudies from "./SavedStudies";
import type { Model } from "./types";

vi.mock("./api", () => ({ request: vi.fn() }));
beforeEach(() => vi.clearAllMocks());
const summaries = [
  {
    id: "one",
    name: "First study",
    source_revision: 2,
    candidate: "selective",
    parameter: "ground_delay",
    created_at: "2026-09-18",
  },
];
function record() {
  return {
    id: "one",
    name: "First study",
    created_at: "2026-09-18",
    result: {
      source_revision: 2,
      candidate: "selective",
      parameter: "ground_delay",
      deadline: null,
      limitations: [],
      trials: [],
      reference: {
        status: "valid",
        value: { value: 0, unit: "s" },
        deadline_check: null,
        delivery_analysis: {
          inputs: { access: { horizon: { value: 100, unit: "s" } } },
          outputs: {
            delivered_count: 0,
            observation_count: 1,
            pending_count: 1,
            dropped_count: 0,
            maximum_latency: null,
          },
        },
      },
    },
  };
}
test("saved evidence labels historical revisions and incomplete latency", async () => {
  vi.mocked(request)
    .mockResolvedValueOnce(summaries)
    .mockResolvedValueOnce(record());
  render(<SavedStudies missionId="a" revision={3} refresh={0} />);
  fireEvent.change(await screen.findByLabelText("View saved study"), {
    target: { value: "one" },
  });
  await screen.findByRole("table");
  expect(screen.getByText(/historical revision/)).toBeInTheDocument();
  expect(screen.getByText("Unknown")).toBeInTheDocument();
});

test("trial preview requires rationale and baseline reopening before a proposal", async () => {
  const saved = record();
  (saved.result.trials as any[]).push({
    ...saved.result.reference,
    value: { value: 5, unit: "s" },
  });
  vi.mocked(request)
    .mockResolvedValueOnce(summaries)
    .mockResolvedValueOnce(saved);
  const onPropose = vi.fn();
  const model = {
    baseline: "approved",
    entities: {
      "selective-delivery-inputs": {
        data: { inputs: { ground_delay: { value: 120, unit: "s" } } },
      },
    },
  } as unknown as Model;
  const view = render(
    <SavedStudies
      missionId="a"
      revision={3}
      refresh={0}
      model={model}
      onPropose={onPropose}
    />,
  );
  fireEvent.change(await screen.findByLabelText("View saved study"), {
    target: { value: "one" },
  });
  const button = await screen.findByRole("button", {
    name: "Propose trial 1 from First study",
  });
  expect(button).toBeDisabled();
  view.rerender(
    <SavedStudies
      missionId="a"
      revision={3}
      refresh={0}
      model={{ ...model, baseline: null }}
      onPropose={onPropose}
    />,
  );
  fireEvent.click(button);
  expect(
    screen.getByText(/Current input: 120 s → proposed: 5 s/),
  ).toBeInTheDocument();
  expect(
    screen.getByRole("button", { name: "Submit trial change proposal" }),
  ).toBeDisabled();
  fireEvent.change(screen.getByLabelText("Trial change rationale"), {
    target: { value: "Reduce delay" },
  });
  fireEvent.click(
    screen.getByRole("button", { name: "Submit trial change proposal" }),
  );
  expect(onPropose).toHaveBeenCalledWith("one", 0, "Reduce delay");
});
test("late evidence cannot populate another mission and errors offer retry", async () => {
  let resolve!: (v: unknown) => void;
  vi.mocked(request)
    .mockResolvedValueOnce(summaries)
    .mockReturnValueOnce(
      new Promise((r) => {
        resolve = r;
      }),
    );
  const view = render(
    <SavedStudies key="a" missionId="a" revision={3} refresh={0} />,
  );
  fireEvent.change(await screen.findByLabelText("View saved study"), {
    target: { value: "one" },
  });
  vi.mocked(request).mockRejectedValueOnce(new Error("Unavailable"));
  view.rerender(
    <SavedStudies key="b" missionId="b" revision={0} refresh={0} />,
  );
  await act(async () => resolve(record()));
  expect(screen.queryByRole("table")).not.toBeInTheDocument();
  expect(await screen.findByRole("alert")).toHaveTextContent("Unavailable");
  vi.mocked(request).mockResolvedValueOnce([]);
  fireEvent.click(screen.getByRole("button", { name: "Retry saved studies" }));
  expect(await screen.findByText(/No saved studies yet/)).toBeInTheDocument();
});
