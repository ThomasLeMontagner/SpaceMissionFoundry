import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { vi, test, expect, beforeEach } from "vitest";
import App, { Badge } from "./App";
import { request } from "./api";
vi.mock("./api", () => ({
  request: vi.fn(),
  subscribe: () => () => {},
  download: vi.fn(),
  setToken: vi.fn(),
}));
beforeEach(() => {
  vi.mocked(request).mockImplementation(async (path: string) =>
    path === "/scenario"
      ? { name: "Pyra", brief: "A wildfire CubeSat mission brief for Europe." }
      : [],
  );
});
test("classification badges distinguish calculations from assumptions", () => {
  render(
    <>
      <Badge value="Deterministic calculation" />
      <Badge value="Explicit assumption" />
    </>,
  );
  expect(screen.getByText("Deterministic calculation")).toHaveClass("calc");
  expect(screen.getByText("Explicit assumption")).not.toHaveClass("calc");
});
test("creation validates brief and sends real request", async () => {
  render(<App />);
  await screen.findByDisplayValue("Pyra");
  fireEvent.change(screen.getByLabelText("Natural-language mission brief"), {
    target: { value: "short" },
  });
  expect(screen.getByRole("button", { name: /Create mission/ })).toBeDisabled();
  fireEvent.change(screen.getByLabelText("Natural-language mission brief"), {
    target: { value: "A sufficiently long mission brief to test creation" },
  });
  fireEvent.click(screen.getByRole("button", { name: /Create mission/ }));
  await waitFor(() =>
    expect(request).toHaveBeenCalledWith("/missions", {
      name: "Pyra",
      brief: "A sufficiently long mission brief to test creation",
    }),
  );
});
test("server errors are actionable and dismissible", async () => {
  vi.mocked(request).mockRejectedValue(
    Error("A valid mission owner token is required"),
  );
  render(<App />);
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "mission owner token",
  );
  fireEvent.click(screen.getByRole("button", { name: "Dismiss" }));
  expect(screen.queryByRole("alert")).not.toBeInTheDocument();
});
