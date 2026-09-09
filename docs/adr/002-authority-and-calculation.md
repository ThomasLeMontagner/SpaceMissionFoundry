# ADR 002: Separate proposal authority from deterministic calculations

Accepted. Pydantic validates proposals before acceptance; a code-level authority matrix constrains entity changes. Independent review cannot submit a model proposal. Human-only commands approve requirements, select a concept and approve the baseline. Tools use Pint and versioned pure functions. Agents may propose estimates but cannot manufacture deterministic calculation provenance.

Consequences: reproducible budgets and enforceable least privilege; the mock workflow is intentionally narrow. No generated code or arbitrary tool execution. Future providers must preserve this boundary.
