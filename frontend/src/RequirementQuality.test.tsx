import { fireEvent, render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";
import RequirementQuality from "./RequirementQuality";

test("filters advisory findings and navigates without proposing changes", () => {
  const onSelect = vi.fn();
  const report = {
    revision: 7,
    checked_requirements: 2,
    findings: [
      {
        id: "a:duplicate",
        requirement_id: "a",
        title: "Duplicate",
        code: "duplicate_statement",
        message: "Compare sources",
        action: "Review applicability",
        related_ids: ["b"],
        source_quote: null,
      },
      {
        id: "b:wording",
        requirement_id: "b",
        title: "Wording",
        code: "ambiguous_wording",
        message: "Define term",
        action: "Clarify",
        related_ids: [],
        source_quote: "useful",
      },
    ],
  };
  const { rerender } = render(
    <RequirementQuality
      report={report}
      onSelect={onSelect}
      requirementIds={["a", "b"]}
    />,
  );
  fireEvent.click(screen.getByRole("button", { name: "b" }));
  expect(onSelect).toHaveBeenCalledWith("b");
  fireEvent.change(screen.getByLabelText("Quality finding type"), {
    target: { value: "ambiguous_wording" },
  });
  expect(screen.queryByText("Compare sources")).not.toBeInTheDocument();
  expect(screen.getByText(/Flagged text/)).toHaveTextContent("useful");
  rerender(
    <RequirementQuality
      report={{ ...report, findings: [report.findings[0]] }}
      onSelect={onSelect}
      requirementIds={["a", "b"]}
    />,
  );
  expect(screen.getByLabelText("Quality finding type")).toHaveValue("all");
  expect(screen.getByText("Compare sources")).toBeInTheDocument();
});
