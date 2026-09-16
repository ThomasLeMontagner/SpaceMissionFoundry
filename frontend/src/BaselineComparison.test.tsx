import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, expect, test, vi } from "vitest";
import BaselineComparison from "./BaselineComparison";
import { request } from "./api";
vi.mock("./api", () => ({ request: vi.fn() }));
beforeEach(() => vi.resetAllMocks());

const rows = [
  { id: "b1", name: "Original", revision: 1 },
  { id: "b2", name: "Revised", revision: 2 },
];
const snapshot = (baseline: string) => ({
  id: "mission",
  baseline,
  revision: baseline === "b1" ? 1 : 2,
  entities: {},
  proposals: {},
});

test("loads immutable snapshots, clears old results when selection changes and reports errors", async () => {
  vi.mocked(request).mockImplementation(async (path) =>
    path.endsWith("/baselines")
      ? rows
      : snapshot(path.includes("b1") ? "b1" : "b2"),
  );
  render(<BaselineComparison missionId="mission" revision={2} />);
  const compare = await screen.findByRole("button", {
    name: "Compare baselines",
  });
  fireEvent.click(compare);
  expect(await screen.findByRole("status")).toHaveTextContent("1 changed");
  expect(request).toHaveBeenCalledWith(
    "/missions/mission/export/json?baseline_id=b1",
  );
  expect(request).toHaveBeenCalledWith(
    "/missions/mission/export/json?baseline_id=b2",
  );
  fireEvent.change(screen.getByLabelText("From baseline"), {
    target: { value: "b2" },
  });
  expect(screen.queryByRole("status")).not.toBeInTheDocument();
  fireEvent.click(compare);
  expect(
    await screen.findByText(/No differences between these snapshots/),
  ).toBeInTheDocument();
  vi.mocked(request).mockRejectedValueOnce(Error("Snapshot unavailable"));
  fireEvent.click(compare);
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "Snapshot unavailable",
  );
  expect(screen.queryByRole("status")).not.toBeInTheDocument();
});

test("late responses cannot display a comparison from another mission", async () => {
  let release!: (value: any) => void;
  const pending = new Promise((resolve) => {
    release = resolve;
  });
  vi.mocked(request).mockImplementation(async (path) =>
    path.endsWith("/baselines") ? rows : pending,
  );
  const view = render(<BaselineComparison missionId="mission" revision={2} />);
  fireEvent.click(
    await screen.findByRole("button", { name: "Compare baselines" }),
  );
  view.rerender(<BaselineComparison missionId="other" revision={1} />);
  await waitFor(() =>
    expect(request).toHaveBeenCalledWith("/missions/other/baselines"),
  );
  release(snapshot("b1"));
  await waitFor(() =>
    expect(
      screen.getByRole("button", { name: "Compare baselines" }),
    ).toBeEnabled(),
  );
  expect(screen.queryByRole("status")).not.toBeInTheDocument();
  expect(screen.queryByRole("alert")).not.toBeInTheDocument();
});
