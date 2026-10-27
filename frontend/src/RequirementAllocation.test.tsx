import { fireEvent, render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";
import RequirementAllocation from "./RequirementAllocation";
import type { Model } from "./types";

test("allocations are reviewed separately and expose incoming requirements", () => {
  const model = {
    entities: {
      req: {
        id: "req",
        title: "Observe target",
        kind: "Requirement",
        state: "accepted",
        relations: [{ type: "allocated_to", target: "imager" }],
      },
      imager: {
        id: "imager",
        title: "Payload",
        kind: "Component",
        state: "accepted",
        owner: "systems",
        revision: 3,
      },
      detect: {
        id: "detect",
        title: "Detect events",
        kind: "Function",
        state: "accepted",
      },
    },
  } as unknown as Model;
  const act = vi.fn().mockResolvedValue(undefined),
    onSelect = vi.fn();
  const { rerender } = render(
    <RequirementAllocation
      model={model}
      requirementId="req"
      busy={false}
      act={act}
      onSelect={onSelect}
    />,
  );
  fireEvent.click(screen.getByText("Allocate responsibility"));
  fireEvent.click(screen.getByRole("button", { name: "Observe target" }));
  expect(onSelect).toHaveBeenCalledWith("req");
  fireEvent.click(screen.getByLabelText("imager — Payload"));
  fireEvent.change(screen.getByLabelText("Allocation change rationale"), {
    target: { value: "Remove unsupported assignment" },
  });
  expect(act).not.toHaveBeenCalled();
  fireEvent.click(
    screen.getByRole("button", { name: "Propose allocations for approval" }),
  );
  expect(act).toHaveBeenCalledWith("/objects/req/edit", {
    changes: { allocation_ids: [] },
    reason: "Remove unsupported assignment",
  });
  expect(model.entities.req.relations[0].target).toBe("imager");
  rerender(
    <RequirementAllocation
      model={{ ...model, baseline: "approved" } as Model}
      requirementId="req"
      busy={false}
      act={act}
      onSelect={onSelect}
    />,
  );
  expect(screen.getByLabelText("detect — Detect events")).toBeDisabled();
});
