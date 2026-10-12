import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";
import RecoveryControls from "./RecoveryControls";
import { request } from "./api";

vi.mock("./api", () => ({ request: vi.fn() }));
afterEach(() => {
  vi.useRealTimers();
  vi.resetAllMocks();
});
const recovered = {
  available: true,
  interrupted: true,
  requires_confirmation: false,
  reason: "Execution interrupted",
  revision: 12,
  completed: ["payload", "evaluate_payload"],
  stage: "bus",
};

test("unknown live outcomes need explicit acknowledgement before recovery", async () => {
  vi.mocked(request).mockResolvedValue({
    ...recovered,
    requires_confirmation: true,
  });
  const command = vi.fn();
  render(
    <RecoveryControls
      missionId="m"
      runId="r"
      revision={12}
      busy={false}
      act={command}
    />,
  );
  const resume = await screen.findByRole("button", {
    name: "Resume from checkpoint",
  });
  expect(resume).toBeDisabled();
  expect(screen.getByText(/2 completed tasks will be preserved/)).toBeVisible();
  fireEvent.click(screen.getByRole("checkbox"));
  fireEvent.click(resume);
  expect(command).toHaveBeenCalledExactlyOnceWith("/collaboration/r/recover", {
    retry_uncertain: true,
  });
  expect(request).toHaveBeenCalledExactlyOnceWith(
    "/missions/m/collaboration/r/recovery",
  );
});

test("polling reveals an expired lease without a revision event and stops on unmount", async () => {
  vi.useFakeTimers();
  vi.mocked(request)
    .mockResolvedValueOnce({
      ...recovered,
      available: false,
      interrupted: false,
      reason: "Lease active",
    })
    .mockResolvedValue(recovered);
  const command = vi.fn();
  const view = render(
    <RecoveryControls
      missionId="m"
      runId="r"
      revision={12}
      busy={false}
      act={command}
    />,
  );
  await act(async () => {});
  expect(screen.getByText("Lease active")).toBeVisible();
  expect(screen.queryByRole("button")).not.toBeInTheDocument();
  await act(async () => {
    await vi.advanceTimersByTimeAsync(5000);
  });
  fireEvent.click(
    screen.getByRole("button", { name: "Resume from checkpoint" }),
  );
  expect(command).toHaveBeenCalledWith("/collaboration/r/recover", {
    retry_uncertain: false,
  });
  view.unmount();
  await act(async () => {
    await vi.advanceTimersByTimeAsync(10000);
  });
  expect(request).toHaveBeenCalledTimes(2);
});

test.each(["stale", "blocked", "busy"])(
  "%s state cannot recover",
  async (condition) => {
    vi.mocked(request).mockResolvedValue({
      ...recovered,
      revision: condition === "stale" ? 13 : 12,
      available: condition !== "blocked",
    });
    render(
      <RecoveryControls
        missionId="m"
        runId="r"
        revision={12}
        busy={condition === "busy"}
        act={vi.fn()}
      />,
    );
    expect(
      await screen.findByRole("button", { name: "Resume from checkpoint" }),
    ).toBeDisabled();
  },
);
