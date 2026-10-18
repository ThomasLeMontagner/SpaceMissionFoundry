import { fireEvent, render, screen, within } from "@testing-library/react";
import { expect, test, vi } from "vitest";
import DataAlternatives, {
  AlternativeBounds,
  defaultBounds,
} from "./DataAlternatives";

function fixture() {
  return {
    bounds: defaultBounds,
    inputs: {
      data: {
        duty: { value: 0.03, unit: "dimensionless" },
        compression: { value: 4, unit: "dimensionless" },
        storage: { value: 8, unit: "Gbit" },
      },
    },
    bus: {
      alternatives: [
        {
          id: "A",
          duty: 0.01,
          compression: 2,
          storage_gbit: 16,
          rationale: "Lower duty and compression",
        },
        {
          id: "B",
          duty: 0.02,
          compression: 8,
          storage_gbit: 64,
          rationale: "More storage and observation",
        },
      ],
    },
    evaluate_bus: {
      alternatives: [
        {
          id: "A",
          eligible: false,
          data: {
            outputs: { daily: { value: 20e9 }, margin: { value: -4e9 } },
          },
          link: { outputs: { capacity: { value: 18e9 } } },
        },
        {
          id: "B",
          eligible: true,
          data: {
            outputs: { daily: { value: 10e9 }, margin: { value: 54e9 } },
          },
          link: { outputs: { capacity: { value: 18e9 } } },
        },
      ],
    },
    selected_alternative: "B",
  };
}

test("comparison separates source inputs, failed checks, recommendation and evidence", () => {
  render(<DataAlternatives data={fixture()} />);
  expect(screen.getByText(/Source inputs: duty 0.03/)).toBeVisible();
  expect(screen.getByText(/Systems recommends Bus option B/)).toBeVisible();
  expect(
    screen.getByText(/Passing data\/link checks does not verify/),
  ).toBeVisible();
  const rows = screen.getAllByRole("row");
  expect(within(rows[1]).getByText("Not eligible")).toBeVisible();
  expect(within(rows[1]).getByText("-4.000")).toBeVisible();
  expect(within(rows[2]).getByText("Pass declared checks")).toBeVisible();
  fireEvent.click(screen.getByText("Bus B: rationale and evidence"));
  expect(screen.getByText("More storage and observation")).toBeVisible();
  expect(
    screen.queryByRole("button", { name: /approve/i }),
  ).not.toBeInTheDocument();
});

test("unevaluated alternatives cannot appear compliant", () => {
  const data: any = fixture();
  delete data.evaluate_bus;
  delete data.selected_alternative;
  render(<DataAlternatives data={data} />);
  expect(screen.getAllByText("Not evaluated")).toHaveLength(2);
  expect(screen.queryByText("Pass declared checks")).not.toBeInTheDocument();
});

test("bounds editor labels units and sends the changed bound", () => {
  const change = vi.fn();
  render(<AlternativeBounds bounds={defaultBounds} onChange={change} />);
  fireEvent.change(screen.getByLabelText("Maximum storage (Gbit)"), {
    target: { value: "32" },
  });
  expect(change).toHaveBeenCalledWith({
    ...defaultBounds,
    storage_max_gbit: 32,
  });
  expect(screen.getByText(/Storage uses decimal Gbit, not GB/)).toBeVisible();
});

test("cross-discipline comparison exposes missing assumptions and failed budgets", () => {
  const data: any = fixture();
  data.study = "cross-discipline";
  delete data.selected_alternative;
  data.evaluate_bus.alternatives.forEach((row: any) => {
    row.eligible = false;
    row.blockers = ["Mass budget failed or invalid"];
    row.mass = { outputs: { margin: { value: -2.5 } } };
  });
  render(<DataAlternatives data={data} />);
  expect(screen.getByRole("alert")).toHaveTextContent(
    "Missing impact assumptions",
  );
  expect(
    screen.getByRole("columnheader", { name: "Mass margin (kg)" }),
  ).toBeVisible();
  expect(screen.getAllByText("-2.500")).toHaveLength(2);
  expect(screen.getAllByText("Unverified")).toHaveLength(4);
  expect(screen.queryByText("Pass declared checks")).not.toBeInTheDocument();
});

test("mission checks distinguish passed failed and unverified proposed evidence", () => {
  const data: any = fixture();
  data.study = "cross-discipline";
  data.check_requirements = true;
  data.source_revision = 7;
  data.evaluate_bus.alternatives[0].requirement_checks = [
    {
      requirement: "mass",
      title: "Mass limit",
      priority: "must",
      status: "pass",
      reason: "Within bound",
      actual: { value: 12, unit: "kg" },
      criterion: {
        metric: "mass.total",
        operator: "<=",
        threshold: { value: 20, unit: "kg" },
      },
    },
    {
      requirement: "latency",
      title: "Delivery deadline",
      priority: "must",
      status: "fail",
      reason: "Late product",
    },
    {
      requirement: "science",
      title: "Image quality",
      priority: "must",
      status: "unverified",
      reason: "No supported quantitative criterion",
    },
  ];
  render(<DataAlternatives data={data} />);
  fireEvent.click(screen.getByText("Bus A: rationale and evidence"));
  const checks = screen.getByLabelText("bus A requirement checks");
  expect(within(checks).getByText("Mass limit (must): Passed")).toBeVisible();
  expect(
    within(checks).getByText("Delivery deadline (must): Failed"),
  ).toBeVisible();
  expect(
    within(checks).getByText("Image quality (must): Unverified"),
  ).toBeVisible();
  expect(within(checks).getByText(/Actual: 12 kg/)).toBeVisible();
  expect(
    screen.getByText(/accepted verification records remain unchanged/),
  ).toBeVisible();
});
