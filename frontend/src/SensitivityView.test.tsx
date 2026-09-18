import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { beforeEach, expect, test, vi } from "vitest";
import { request } from "./api";
import SensitivityView from "./SensitivityView";
import type { Model } from "./types";

vi.mock("./api", () => ({ request: vi.fn() }));
beforeEach(() => vi.clearAllMocks());
const model = {
  id: "mission-a",
  revision: 5,
  baseline: "baseline",
  selected: "selective",
  entities: {
    "selective-delivery-analysis": {
      state: "accepted",
      data: { status: "valid" },
    },
  },
} as unknown as Model;
function response() {
  const row = {
    value: { value: 2, unit: "minute" },
    status: "valid",
    reference: true,
    delivery_analysis: {
      outputs: {
        delivered_count: 0,
        observation_count: 1,
        pending_count: 1,
        dropped_count: 0,
        maximum_latency: null,
        delivered_only_maximum_latency: null,
        peak_queue: { value: 100 },
        limitations: [],
      },
    },
    link_analysis: { outputs: { link_margin_db: { value: -1 } } },
    deadline_check: {
      status: "unverified",
      missed_deadlines: 0,
      unresolved_deadlines: 1,
    },
    requirement_checks: [],
  };
  return {
    parameter: "ground_delay",
    candidate: "selective",
    source_revision: 5,
    reference: row,
    trials: [],
    limitations: [],
  };
}

test("study runs on a baseline, labels incomplete evidence and clears results on edits", async () => {
  vi.mocked(request).mockResolvedValue(response());
  render(<SensitivityView model={model} busy={false} />);
  fireEvent.click(
    screen.getByRole("button", { name: "Run sensitivity study" }),
  );
  await screen.findByRole("table");
  expect(request).toHaveBeenCalledWith(
    "/missions/mission-a/sensitivity",
    expect.objectContaining({ revision: 5, parameter: "ground_delay" }),
  );
  expect(
    screen.getByText(/unverified · 0 missed · 1 unresolved/),
  ).toBeInTheDocument();
  fireEvent.change(screen.getByLabelText("Trial values"), {
    target: { value: "0, 5" },
  });
  expect(screen.queryByRole("table")).not.toBeInTheDocument();
});

test("invalid inputs and stale evidence cannot launch a study", async () => {
  const view = render(<SensitivityView model={model} busy={false} />);
  fireEvent.change(screen.getByLabelText("Trial values"), {
    target: { value: "1,,2" },
  });
  fireEvent.click(
    screen.getByRole("button", { name: "Run sensitivity study" }),
  );
  expect(await screen.findByRole("alert")).toHaveTextContent("2–15");
  expect(request).not.toHaveBeenCalled();
  view.rerender(
    <SensitivityView model={{ ...model, entities: {} }} busy={false} />,
  );
  expect(
    screen.getByRole("button", { name: "Run sensitivity study" }),
  ).toBeDisabled();
});

test("keyed mission revisions discard delayed results and request failures are visible", async () => {
  let resolve!: (value: unknown) => void;
  vi.mocked(request).mockReturnValueOnce(
    new Promise((r) => {
      resolve = r;
    }),
  );
  const view = render(
    <SensitivityView key="mission-a:5" model={model} busy={false} />,
  );
  fireEvent.click(
    screen.getByRole("button", { name: "Run sensitivity study" }),
  );
  const next = { ...model, id: "mission-b", revision: 6 };
  view.rerender(
    <SensitivityView key="mission-b:6" model={next} busy={false} />,
  );
  await act(async () => resolve(response()));
  expect(screen.queryByRole("table")).not.toBeInTheDocument();
  vi.mocked(request).mockRejectedValueOnce(
    new Error("Mission changed; reload"),
  );
  fireEvent.click(
    screen.getByRole("button", { name: "Run sensitivity study" }),
  );
  await waitFor(() =>
    expect(screen.getByRole("alert")).toHaveTextContent("Mission changed"),
  );
});
