import { useId } from "react";

export type CollaborationEvent = {
  id: string;
  sender: string;
  recipient: string;
  type: string;
  task: string;
  summary: string;
  objects: string[];
};

const roles = ["human", "payload", "tools", "bus", "systems", "orchestrator"];
const names: Record<string, string> = {
  human: "Mission Owner",
  payload: "Payload",
  tools: "Engineering tools",
  bus: "Bus & Ground",
  systems: "Systems",
  orchestrator: "Orchestrator",
};
// Older runs addressed tool tasks by stage name. Group them under their executor.
const executor = (role: string) =>
  role.startsWith("evaluate_") ? "tools" : role;

export function selectedEventIds(
  events: CollaborationEvent[],
  selection: string,
) {
  const label = (role: string) => names[executor(role)] || executor(role);
  return events
    .filter(
      (e) =>
        label(e.sender) === selection ||
        label(e.recipient) === selection ||
        `${label(e.sender)} → ${label(e.recipient)}` === selection,
    )
    .map((e) => e.id);
}

export default function CollaborationGraph({
  events,
  stage,
  status,
  paused,
  mode,
  selection,
  onSelect,
}: {
  events: CollaborationEvent[];
  stage: string;
  status: string;
  paused: boolean;
  mode: string;
  selection: string;
  onSelect: (label: string, ids: string[]) => void;
}) {
  const marker = useId().replace(/:/g, "");
  const nodes = [
    ...new Set([
      ...roles,
      ...events.flatMap((e) => [executor(e.sender), executor(e.recipient)]),
    ]),
  ];
  const positions = Object.fromEntries(
    nodes.map((role, i) => {
      const angle = -Math.PI / 2 + (i * 2 * Math.PI) / nodes.length;
      return [
        role,
        { x: 400 + 290 * Math.cos(angle), y: 245 + 185 * Math.sin(angle) },
      ];
    }),
  );
  const edges = new Map<string, { from: string; to: string; ids: string[] }>();
  for (const event of events) {
    const from = executor(event.sender),
      to = executor(event.recipient);
    const key = JSON.stringify([from, to]);
    if (!edges.has(key)) edges.set(key, { from, to, ids: [] });
    edges.get(key)!.ids.push(event.id);
  }
  const current = ["awaiting_approval", "blocked", "failed"].includes(status)
    ? "human"
    : executor(stage);
  const active = [
    "ready",
    "working",
    "failed",
    "blocked",
    "awaiting_approval",
  ].includes(status);
  const label = (role: string) => names[role] || role;
  const selectNode = (role: string) =>
    onSelect(
      label(role),
      events
        .filter(
          (e) => executor(e.sender) === role || executor(e.recipient) === role,
        )
        .map((e) => e.id),
    );
  const state = paused && active ? "Paused" : status.replaceAll("_", " ");
  return (
    <section
      className="collaboration-graph"
      aria-label="Agent interaction graph"
    >
      <h3>Agent interaction graph</h3>
      <p>
        {mode === "simulation" ? "SIMULATION" : "LIVE PROVIDER"} · {state}.{" "}
        {active
          ? `Next attention: ${label(current)}.`
          : "Recorded activity; no task is running."}
      </p>
      <p className="muted">
        Arrows show recorded exchanges, with event counts. Select a role or
        connection to filter the timeline. A recorded tool failure is evidence
        of a past result, not necessarily an unresolved disagreement.
      </p>
      <svg
        viewBox="0 0 800 490"
        aria-label="Recorded exchanges between mission roles"
      >
        <defs>
          <marker
            id={marker}
            markerWidth="8"
            markerHeight="8"
            refX="7"
            refY="4"
            orient="auto"
          >
            <path d="M0,0 L8,4 L0,8 Z" fill="currentColor" />
          </marker>
        </defs>
        {[...edges.entries()].map(([key, edge]) => {
          const a = positions[edge.from],
            b = positions[edge.to];
          const dx = b.x - a.x,
            dy = b.y - a.y,
            length = Math.hypot(dx, dy) || 1;
          const cx = (a.x + b.x) / 2 - (dy / length) * 45;
          const cy = (a.y + b.y) / 2 + (dx / length) * 45;
          const title = `${label(edge.from)} → ${label(edge.to)}`;
          const choose = () => onSelect(title, edge.ids);
          return (
            <g key={key}>
              <path
                className="collaboration-edge"
                d={`M${a.x},${a.y} Q${cx},${cy} ${b.x - (dx / length) * 80},${b.y - (dy / length) * 40}`}
                markerEnd={`url(#${marker})`}
              />
              <g
                role="button"
                tabIndex={0}
                aria-label={`${title}: ${edge.ids.length} events`}
                aria-pressed={selection === title}
                onClick={choose}
                onKeyDown={(e) => {
                  if (["Enter", " "].includes(e.key)) {
                    e.preventDefault();
                    choose();
                  }
                }}
                className="collaboration-connection"
              >
                <title>{title}</title>
                <circle
                  cx={(a.x + 2 * cx + b.x) / 4}
                  cy={(a.y + 2 * cy + b.y) / 4}
                  r="14"
                />
                <text
                  x={(a.x + 2 * cx + b.x) / 4}
                  y={(a.y + 2 * cy + b.y) / 4 + 5}
                  textAnchor="middle"
                >
                  {edge.ids.length}
                </text>
              </g>
            </g>
          );
        })}
        {nodes.map((role) => {
          const p = positions[role];
          const count = events.filter(
            (e) =>
              executor(e.sender) === role || executor(e.recipient) === role,
          ).length;
          return (
            <g
              key={role}
              role="button"
              tabIndex={0}
              aria-label={`Show ${label(role)} events`}
              aria-pressed={selection === label(role)}
              onClick={() => selectNode(role)}
              onKeyDown={(e) => {
                if (["Enter", " "].includes(e.key)) {
                  e.preventDefault();
                  selectNode(role);
                }
              }}
              className={`collaboration-node ${active && current === role ? "current" : ""}`}
            >
              <rect x={p.x - 78} y={p.y - 29} width="156" height="58" rx="9" />
              <text x={p.x} y={p.y - 4} textAnchor="middle">
                {label(role)}
              </text>
              <text
                x={p.x}
                y={p.y + 17}
                textAnchor="middle"
                className="graph-count"
              >
                {count} recorded events
              </text>
            </g>
          );
        })}
      </svg>
    </section>
  );
}
