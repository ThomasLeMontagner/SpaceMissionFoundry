import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, expect, test, vi } from "vitest";
import DesignEditor from "./DesignEditor";
import { request } from "./api";
import type { Entity } from "./types";
vi.mock("./api", () => ({ request: vi.fn() }));
const data: Entity = {
  id: "selective-data-inputs",
  kind: "Parameter",
  title: "selective · data inputs",
  owner: "systems",
  state: "accepted",
  revision: 3,
  classification: "Explicit assumption",
  relations: [],
  data: {
    tool: "data",
    candidate: "selective",
    inputs: {
      duty: { value: 0.02, unit: "" },
      compression: { value: 4, unit: "" },
    },
  },
};
beforeEach(() => vi.clearAllMocks());
test("editing submits a proposal with the displayed revision without changing accepted data", async () => {
  const done = vi.fn();
  vi.mocked(request).mockResolvedValue({ id: "mission" });
  render(
    <DesignEditor
      entity={data}
      missionId="mission"
      revision={7}
      onProposed={done}
    />,
  );
  fireEvent.click(
    screen.getByRole("button", { name: "Edit calculation inputs" }),
  );
  fireEvent.change(
    screen.getByLabelText("Observation duty cycle", { exact: true }),
    { target: { value: "0.1" } },
  );
  fireEvent.change(screen.getByLabelText("Change rationale"), {
    target: { value: "More imaging" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Propose change" }));
  await waitFor(() => expect(done).toHaveBeenCalled());
  expect(request).toHaveBeenCalledWith(
    "/missions/mission/objects/selective-data-inputs/edit",
    {
      revision: 7,
      changes: {
        inputs: {
          duty: { value: 0.1, unit: "" },
          compression: { value: 4, unit: "" },
        },
      },
      reason: "More imaging",
    },
  );
  expect(data.data.inputs.duty.value).toBe(0.02);
});
test("validation failure preserves the draft and is visible inside the editor", async () => {
  vi.mocked(request).mockRejectedValue(
    Error("Fractions must be between zero and one"),
  );
  render(
    <DesignEditor
      entity={data}
      missionId="mission"
      revision={7}
      onProposed={vi.fn()}
    />,
  );
  fireEvent.click(
    screen.getByRole("button", { name: "Edit calculation inputs" }),
  );
  fireEvent.change(
    screen.getByLabelText("Observation duty cycle", { exact: true }),
    { target: { value: "2" } },
  );
  fireEvent.change(screen.getByLabelText("Change rationale"), {
    target: { value: "Invalid input" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Propose change" }));
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "between zero and one",
  );
  expect(
    screen.getByLabelText("Observation duty cycle", { exact: true }),
  ).toHaveValue(2);
});

test("requirement text can be revised and submitted for impact review", async () => {
  const done = vi.fn();
  vi.mocked(request).mockResolvedValue({ id: "mission" });
  const requirement: Entity = {
    ...data,
    id: "req-latency",
    kind: "Requirement",
    title: "Deliver within 30 minutes",
    data: {
      rationale: "Timely imagery",
      level: "system",
      priority: "must",
      verification_method: "analysis",
    },
  };
  render(
    <DesignEditor
      entity={requirement}
      missionId="mission"
      revision={9}
      onProposed={done}
    />,
  );
  fireEvent.click(screen.getByRole("button", { name: "Edit requirement" }));
  fireEvent.change(screen.getByRole("textbox", { name: "title" }), {
    target: { value: "Deliver within 20 minutes" },
  });
  fireEvent.change(screen.getByLabelText("Change rationale"), {
    target: { value: "Explore faster delivery" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Propose change" }));
  await waitFor(() => expect(done).toHaveBeenCalled());
  expect(request).toHaveBeenCalledWith(
    "/missions/mission/objects/req-latency/edit",
    {
      revision: 9,
      changes: { title: "Deliver within 20 minutes", ...requirement.data },
      reason: "Explore faster delivery",
    },
  );
  expect(requirement.title).toBe("Deliver within 30 minutes");
});
