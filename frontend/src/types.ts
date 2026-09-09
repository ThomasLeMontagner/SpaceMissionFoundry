export type Entity = {
  id: string;
  kind: string;
  title: string;
  state: string;
  owner: string;
  revision: number;
  classification: string;
  relations: { type: string; target: string }[];
  data: Record<string, any>;
};
export type Proposal = {
  id: string;
  proposal_type: string;
  agent: string;
  target_revision: number;
  status: string;
  rationale: string;
  expected_consequences: string;
  confidence: number;
  operations: { action: string; entity: Entity }[];
};
export type Model = {
  id: string;
  name: string;
  brief: string;
  revision: number;
  phase: string;
  entities: Record<string, Entity>;
  proposals: Record<string, Proposal>;
  selected: string | null;
  baseline: string | null;
  paused: boolean;
  steps: number;
};
