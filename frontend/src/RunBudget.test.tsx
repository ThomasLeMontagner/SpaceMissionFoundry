import { act, render, screen } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";
import RunBudget from "./RunBudget";

afterEach(() => vi.useRealTimers());

function fixture() {
  return {
    limits: { cost_eur: 1, tokens: 30000, elapsed_seconds: 60 },
    price_per_million: 1,
    deadline: new Date(Date.now() + 60000).toISOString(),
    attempts: [
      {
        agent: "payload",
        live: true,
        accounted_tokens: 29120,
        reported_tokens: null,
        elapsed_seconds: null,
      },
      {
        agent: "payload",
        live: true,
        accounted_tokens: 50,
        reported_tokens: 50,
        elapsed_seconds: 0.5,
      },
    ],
  };
}

test("usage includes unknown reservations and displays per-agent totals honestly", () => {
  render(<RunBudget budget={fixture()} />);
  expect(screen.getByText(/Accounted tokens: 29,170/)).toHaveTextContent(
    "€0.029170 / €1",
  );
  expect(
    screen.getByText(/1 live attempt\(s\) have unknown usage/),
  ).toBeVisible();
  expect(screen.getByText("50 + unknown")).toBeVisible();
  expect(screen.getByText("0.50 + unknown")).toBeVisible();
  expect(screen.getByText(/At least 80%/)).toBeVisible();
});

test("elapsed window expires without a revision notification", async () => {
  vi.useFakeTimers();
  render(<RunBudget budget={fixture()} />);
  await act(async () => {
    await vi.advanceTimersByTimeAsync(61000);
  });
  expect(screen.getByText(/Execution window expired/)).toBeVisible();
});

test("legacy usage is unavailable, not zero", () => {
  render(<RunBudget budget={undefined} />);
  expect(
    screen.getByText(/complete usage accounting is unavailable/),
  ).toBeVisible();
  expect(screen.queryByText(/Accounted tokens/)).not.toBeInTheDocument();
});
