import { fireEvent, render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";
import CreateRequirement from "./CreateRequirement";
import type { Model } from "./types";

test("creation requires parents and source and only submits a proposal", () => {
  const model = {
    entities: {
      objective: {
        id: "objective",
        kind: "Objective",
        title: "Mission objective",
        state: "accepted",
      },
    },
  } as unknown as Model;
  const act = vi.fn().mockResolvedValue(undefined);
  const { rerender } = render(
    <CreateRequirement model={model} busy={false} act={act} />,
  );
  fireEvent.click(screen.getByText("Add a requirement"));
  fireEvent.change(screen.getByLabelText("New requirement statement"), {
    target: { value: "Provide observation reports" },
  });
  fireEvent.change(screen.getByLabelText("Requirement rationale"), {
    target: { value: "Enable planning" },
  });
  fireEvent.change(screen.getByLabelText("Requirement source"), {
    target: { value: "Owner need" },
  });
  expect(screen.getByRole("button")).toBeDisabled();
  fireEvent.click(screen.getByLabelText("objective — Mission objective"));
  expect(act).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button"));
  expect(act).toHaveBeenCalledWith(
    "/requirements",
    expect.objectContaining({
      statement: "Provide observation reports",
      source: "Owner need",
      parent_ids: ["objective"],
      verification_method: "review",
    }),
  );
  expect(Object.keys(model.entities)).toEqual(["objective"]);
  rerender(
    <CreateRequirement
      model={{ ...model, baseline: "approved" } as Model}
      busy={false}
      act={act}
    />,
  );
  expect(screen.getByLabelText("New requirement statement")).toBeDisabled();
});
