import { fireEvent, render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";
import RequirementCollaboration from "./RequirementCollaboration";
import type { Model } from "./types";
vi.mock("./api", () => ({ request: vi.fn().mockResolvedValue({}) }));
function model(run?: any) {
  return {
    id: "mission",
    revision: 3,
    entities: {
      req: {
        id: "req",
        kind: "Requirement",
        title: "Deliver within 30 minutes",
        state: "accepted",
      },
      ...(run
        ? {
            run: {
              id: "run",
              kind: "AgentRun",
              data: {
                workflow: "requirement-collaboration",
                source_requirement: { title: "Deadline" },
                source_revision: 1,
                mode: "simulation",
                round: 0,
                attempts: 0,
                stage: "mission",
                events: [],
                ...run,
              },
            },
          }
        : {}),
    },
    proposals: {},
  } as unknown as Model;
}
test("starting is explicit and simulation is clearly labeled", () => {
  const act = vi.fn();
  render(<RequirementCollaboration model={model()} busy={false} act={act} />);
  expect(act).not.toHaveBeenCalled();
  fireEvent.click(screen.getByText("Start requirement collaboration"));
  expect(act).toHaveBeenCalledWith(
    "/requirement-collaboration",
    expect.objectContaining({
      mode: "simulation",
      requirement_id: "req",
      limits: { cost_eur: 1, tokens: 100000, elapsed_seconds: 3600 },
    }),
  );
});
test("questions stop task execution and require answers", () => {
  const act = vi.fn();
  render(
    <RequirementCollaboration
      model={model({
        status: "awaiting_answers",
        stage: "formalize",
        pending_questions: ["Which quality applies?"],
      })}
      busy={false}
      act={act}
    />,
  );
  expect(
    screen.queryByText("Run Systems criterion proposal"),
  ).not.toBeInTheDocument();
  expect(screen.getByLabelText("Which quality applies?")).toBeRequired();
  fireEvent.change(screen.getByLabelText("Which quality applies?"), {
    target: { value: "Quality remains outside this deadline check" },
  });
  fireEvent.click(screen.getByText("Record answers and continue"));
  expect(act).toHaveBeenCalledWith("/requirement-collaboration/run/answers", {
    answers: ["Quality remains outside this deadline check"],
    criterion: null,
  });
});
test("unknown live call requires acknowledgement before explicit retry", () => {
  const act = vi.fn();
  render(
    <RequirementCollaboration
      model={model({ status: "failed", mode: "live" })}
      busy={false}
      act={act}
    />,
  );
  const button = screen.getByText("Prepare explicit retry");
  expect(button).toBeDisabled();
  fireEvent.click(screen.getByRole("checkbox"));
  fireEvent.click(button);
  expect(act).toHaveBeenCalledWith("/requirement-collaboration/run/retry", {
    acknowledge_unknown: true,
  });
});

test("automatic progression is explicitly requested and excludes manual work", () => {
  const act = vi.fn();
  const { rerender } = render(
    <RequirementCollaboration
      model={model({ status: "ready" })}
      busy={false}
      act={act}
    />,
  );
  expect(act).not.toHaveBeenCalled();
  fireEvent.click(screen.getByText("Run until owner action"));
  expect(act).toHaveBeenCalledWith("/requirement-collaboration/run/run");
  rerender(
    <RequirementCollaboration
      model={model({
        status: "ready",
        execution: {
          status: "running",
          lease_expires_at: "2999-01-01T00:00:00Z",
        },
      })}
      busy={false}
      act={act}
    />,
  );
  expect(screen.getByText("Run until owner action")).toBeDisabled();
  expect(screen.getByText("Run Mission clarification")).toBeDisabled();
});

test("expired idle execution can recover without acknowledging a model call", () => {
  const act = vi.fn();
  render(
    <RequirementCollaboration
      model={model({
        status: "ready",
        mode: "live",
        execution: {
          status: "running",
          lease_expires_at: "2000-01-01T00:00:00Z",
        },
      })}
      busy={false}
      act={act}
    />,
  );
  expect(screen.queryByRole("checkbox")).not.toBeInTheDocument();
  fireEvent.click(screen.getByText("Prepare explicit retry"));
  expect(act).toHaveBeenCalledWith("/requirement-collaboration/run/retry", {
    acknowledge_unknown: false,
  });
});
