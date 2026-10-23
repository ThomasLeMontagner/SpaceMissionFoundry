import { fireEvent, render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";
import RequirementLinks from "./RequirementLinks";
import type { Model } from "./types";

test("parent selection is a separate proposal and baseline edits are disabled", () => {
  const model = {
    entities: {
      req: {
        id: "req",
        title: "Requirement",
        kind: "Requirement",
        state: "accepted",
        relations: [{ type: "derives_from", target: "objective" }],
      },
      objective: {
        id: "objective",
        title: "Objective",
        kind: "Objective",
        state: "accepted",
      },
      parent: {
        id: "parent",
        title: "Parent",
        kind: "Requirement",
        state: "accepted",
      },
    },
  } as unknown as Model;
  const act = vi.fn().mockResolvedValue(undefined);
  const { rerender } = render(
    <RequirementLinks
      model={model}
      requirementId="req"
      busy={false}
      act={act}
    />,
  );
  expect(screen.getByRole("button")).toBeDisabled();
  fireEvent.click(screen.getByLabelText("objective — Objective"));
  expect(screen.getByRole("button")).toBeDisabled();
  fireEvent.click(screen.getByLabelText("parent — Parent"));
  fireEvent.change(screen.getByLabelText("Parent-link change rationale"), {
    target: { value: "Correct originating need" },
  });
  expect(act).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button"));
  expect(act).toHaveBeenCalledWith("/objects/req/edit", {
    changes: { parent_ids: ["parent"] },
    reason: "Correct originating need",
  });
  expect(model.entities.req.relations[0].target).toBe("objective");
  rerender(
    <RequirementLinks
      model={{ ...model, baseline: "approved" } as Model}
      requirementId="req"
      busy={false}
      act={act}
    />,
  );
  expect(screen.getByLabelText("parent — Parent")).toBeDisabled();
});
