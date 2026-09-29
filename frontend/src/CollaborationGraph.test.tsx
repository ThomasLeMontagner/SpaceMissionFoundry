import { fireEvent, render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";
import CollaborationGraph, {
  selectedEventIds,
  type CollaborationEvent,
} from "./CollaborationGraph";

const events: CollaborationEvent[] = [
  {
    id: "request",
    sender: "human",
    recipient: "payload",
    type: "request",
    task: "payload",
    summary: "Request duty proposal",
    objects: ["input"],
  },
  {
    id: "tool",
    sender: "orchestrator",
    recipient: "evaluate_payload",
    type: "started",
    task: "evaluate_payload",
    summary: "Execute tool",
    objects: ["input"],
  },
  {
    id: "result",
    sender: "tools",
    recipient: "bus",
    type: "tool_result",
    task: "evaluate_payload",
    summary: "Capacity failed",
    objects: ["input"],
  },
];

test("graph uses recorded exchanges and groups historical tool stage recipients", () => {
  const select = vi.fn();
  render(
    <CollaborationGraph
      events={events}
      stage="bus"
      status="ready"
      paused={false}
      mode="simulation"
      selection=""
      onSelect={select}
    />,
  );
  expect(screen.getByText(/SIMULATION · ready/)).toBeInTheDocument();
  expect(
    screen.queryByRole("button", { name: /Systems → Mission Owner/ }),
  ).not.toBeInTheDocument();
  fireEvent.click(
    screen.getByRole("button", { name: "Show Engineering tools events" }),
  );
  expect(select).toHaveBeenCalledWith("Engineering tools", ["tool", "result"]);
  fireEvent.keyDown(
    screen.getByRole("button", {
      name: "Engineering tools → Bus & Ground: 1 events",
    }),
    { key: "Enter" },
  );
  expect(select).toHaveBeenLastCalledWith("Engineering tools → Bus & Ground", [
    "result",
  ]);
});

test("graph selections include subsequent live events without leaking unrelated exchanges", () => {
  const extended = [...events, { ...events[2], id: "retry" }];
  expect(
    selectedEventIds(extended, "Engineering tools → Bus & Ground"),
  ).toEqual(["result", "retry"]);
  expect(selectedEventIds(extended, "Engineering tools")).toEqual([
    "tool",
    "result",
    "retry",
  ]);
  expect(selectedEventIds(extended, "Systems")).toEqual([]);
});

test("paused and terminal runs do not claim active execution", () => {
  const props = {
    events,
    stage: "systems",
    mode: "simulation",
    selection: "",
    onSelect: vi.fn(),
  };
  const view = render(
    <CollaborationGraph {...props} status="ready" paused={true} />,
  );
  expect(
    screen.getByText(/Paused. Next attention: Systems/),
  ).toBeInTheDocument();
  view.rerender(
    <CollaborationGraph {...props} status="cancelled" paused={true} />,
  );
  expect(
    screen.getByText(/cancelled. Recorded activity; no task is running/),
  ).toBeInTheDocument();
});
