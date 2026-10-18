import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { expect, test, vi } from "vitest";
import RequirementFormalization from "./RequirementFormalization";
import { request } from "./api";
import type { Model } from "./types";
vi.mock("./api", () => ({ request: vi.fn() }));

test("deadline suggestion stays partial and requires a separate proposal", async () => {
  const act = vi.fn().mockResolvedValue(undefined);
  vi.mocked(request).mockResolvedValue({
    revision: 1,
    metrics: {
      "delivery.maximum_latency": { label: "Delivery latency", unit: "s" },
    },
    notes: [],
    requirements: [
      {
        id: "req",
        title: "Deliver within 2 hours of acquisition",
        status: "needs_clarification",
        suggestion: {
          source_quote: "within 2 hours of acquisition",
          explanation: "Deadline only",
          criterion: {
            metric: "delivery.maximum_latency",
            operator: "<=",
            threshold: { value: 2, unit: "hour" },
          },
        },
      },
    ],
  });
  render(
    <RequirementFormalization
      model={
        {
          id: "mission",
          revision: 1,
          entities: { req: { revision: 1 } },
        } as unknown as Model
      }
      busy={false}
      act={act}
    />,
  );
  fireEvent.click(await screen.findByText("Use suggested deadline"));
  expect(act).not.toHaveBeenCalled();
  expect(screen.getByLabelText("Threshold")).toHaveValue(2);
  expect(screen.getByLabelText("Criterion coverage")).toHaveValue("partial");
  fireEvent.change(screen.getByLabelText("Basis and applicability"), {
    target: { value: "Extracted deadline; image quality unresolved" },
  });
  fireEvent.click(screen.getByText("Propose formalization"));
  await waitFor(() =>
    expect(act).toHaveBeenCalledWith(
      "/requirements/req/formalize",
      expect.objectContaining({
        coverage: "partial",
        confirm_full_coverage: false,
        criterion: {
          metric: "delivery.maximum_latency",
          operator: "<=",
          threshold: { value: 2, unit: "hour" },
        },
      }),
    ),
  );
});
