import { render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";
import InterfaceChecks from "./InterfaceChecks";
import type { Model } from "./types";

test("stale interface checks hide prior pass evidence and baseline editing is explained", () => {
  const model = {
    baseline: "baseline",
    entities: {
      interface: {
        id: "interface",
        kind: "Interface",
        title: "Payload data",
        state: "accepted",
        data: {},
      },
      "interface-check-interface": {
        id: "interface-check-interface",
        state: "stale",
        data: {
          status: "pass",
          checks: [{ check: "rate", status: "pass", reason: "Old result" }],
        },
      },
    },
  } as unknown as Model;
  render(<InterfaceChecks model={model} busy={true} onInspect={vi.fn()} />);
  expect(screen.getByText(/Stale — review changes/)).toBeInTheDocument();
  expect(screen.queryByText(/Old result/)).not.toBeInTheDocument();
  expect(screen.getByText(/Reopen the baseline/)).toBeInTheDocument();
  expect(
    screen.getByRole("button", { name: "Inspect or edit interface contract" }),
  ).toBeDisabled();
});
