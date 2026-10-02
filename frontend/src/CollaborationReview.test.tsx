import { fireEvent, render, screen, within } from "@testing-library/react";
import { expect, test, vi } from "vitest";
import CollaborationView from "./CollaborationView";
import type { Model } from "./types";

function fixture(recommendation: string) {
  const review = {
    recommendation,
    rationale: "Consider the science trade-off",
    findings: [
      {
        severity: recommendation === "submit" ? "advisory" : "blocking",
        summary: "Science adequacy remains unverified",
        evidence: ["mission_goal"],
      },
    ],
    follow_up:
      recommendation === "submit"
        ? ""
        : "Provide a minimum useful observation duty.",
  };
  return {
    id: "mission",
    phase: "Trade study",
    proposals: {},
    entities: {
      run: {
        id: "run",
        kind: "AgentRun",
        title: "Duty study",
        data: {
          workflow: "duty-collaboration",
          mode: "simulation",
          status: recommendation === "submit" ? "awaiting_approval" : "blocked",
          stage: "systems",
          completed: ["payload", "evaluate_payload", "bus", "evaluate_bus"],
          attempts: 5,
          source_revision: 6,
          systems_review: review,
          events: [
            {
              id: "assessment",
              type: "systems_review",
              sender: "systems",
              recipient: "human",
              task: "systems",
              summary: review.rationale,
              objects: ["selective-data-inputs"],
              evidence: {
                context: { mission_goal: { goal: "Observe wildfires" } },
              },
            },
          ],
        },
      },
    },
  } as unknown as Model;
}

test.each(["submit", "revise", "clarify"])(
  "review displays %s and recorded evidence without accepting changes",
  (recommendation) => {
    const act = vi.fn();
    render(
      <CollaborationView
        model={fixture(recommendation)}
        busy={false}
        act={act}
        onInspect={vi.fn()}
      />,
    );
    const panel = screen.getByRole("region", {
      name: "Systems review",
    });
    expect(within(panel).getByText(/SIMULATED REVIEW/)).toBeInTheDocument();
    expect(
      within(panel).getByText(/Science adequacy remains unverified/),
    ).toBeInTheDocument();
    fireEvent.click(within(panel).getByText(/Review evidence:/));
    expect(within(panel).getByText(/Observe wildfires/)).toBeVisible();
    expect(act).not.toHaveBeenCalled();
    if (recommendation !== "submit") {
      const form = screen.getByRole("form", { name: "Clarify and revise" });
      expect(
        within(form).getByRole("button", { name: "Request revised proposal" }),
      ).toBeDisabled();
      fireEvent.click(
        within(form).getByRole("button", { name: "Use Systems feedback" }),
      );
      expect(within(form).getByLabelText("Revision feedback")).toHaveValue(
        "Provide a minimum useful observation duty.",
      );
      fireEvent.submit(form);
      expect(act).toHaveBeenCalledWith("/collaboration/run/clarify", {
        feedback: "Provide a minimum useful observation duty.",
        minimum_duty: null,
      });
    }
  },
);

test("legacy completed runs do not claim a new independent review", () => {
  const model = fixture("submit");
  delete model.entities.run.data.systems_review;
  model.entities.run.data.completed.push("systems");
  render(
    <CollaborationView
      model={model}
      busy={false}
      act={vi.fn()}
      onInspect={vi.fn()}
    />,
  );
  expect(
    screen.getByText(/Legacy run: no independent Systems assessment/),
  ).toBeInTheDocument();
  expect(
    screen.queryByRole("region", { name: "Systems review" }),
  ).not.toBeInTheDocument();
});
