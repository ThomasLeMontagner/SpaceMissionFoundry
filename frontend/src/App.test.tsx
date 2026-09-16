import {
  render,
  screen,
  fireEvent,
  waitFor,
  act,
} from "@testing-library/react";
import { vi, test, expect, beforeEach } from "vitest";
import App, { Badge } from "./App";
import { request, subscribe } from "./api";
vi.mock("./api", () => ({
  request: vi.fn(),
  subscribe: vi.fn(() => () => {}),
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

test("a delayed mission refresh cannot reopen a mission after switching away", async () => {
  const mission = {
    id: "m",
    name: "Saved test",
    brief: "Mission brief",
    revision: 1,
    phase: "Brief",
    entities: {},
    proposals: {},
    selected: null,
    baseline: null,
    paused: false,
    steps: 0,
  };
  let refresh!: () => void;
  vi.mocked(subscribe).mockImplementation((_id, callback) => {
    refresh = callback;
    return () => {};
  });
  vi.mocked(request).mockImplementation(async (path) =>
    path === "/missions"
      ? [{ id: "m", name: "Saved test" }]
      : path === "/missions/m"
        ? mission
        : { name: "New mission", brief: "A sufficiently long mission brief." },
  );
  render(<App />);
  fireEvent.click(await screen.findByRole("button", { name: "Saved test →" }));
  const switchButton = await screen.findByRole("button", {
    name: "Switch mission",
  });
  await waitFor(() => expect(switchButton).toBeEnabled());
  let resolve!: (value: unknown) => void;
  vi.mocked(request).mockImplementationOnce(
    () =>
      new Promise((r) => {
        resolve = r;
      }),
  );
  act(() => refresh());
  fireEvent.click(switchButton);
  await act(async () => {
    resolve({ ...mission, revision: 2 });
  });
  expect(
    screen.getByRole("heading", { name: "Saved missions" }),
  ).toBeInTheDocument();
  expect(
    screen.queryByRole("button", { name: "Switch mission" }),
  ).not.toBeInTheDocument();
});
