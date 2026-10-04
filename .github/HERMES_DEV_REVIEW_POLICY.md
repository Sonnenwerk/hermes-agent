# Hermes Development Review Policy

Status: active policy for the Sonnenwerk Hermes development workflow.

## Normative authority

For development and review work, these are **MUST** sources:

1. Current Hermes architecture and runtime invariants.
2. `SECURITY.md` for trust boundaries, threat model, and security classification.
3. The nearest applicable `AGENTS.md`.
4. The relevant `DESIGN.md`.
5. Accepted ADRs and merged architecture decisions.
6. Explicit approved task requirements.

Active Hermes design proposals are **SHOULD** guidance. Experimental ideas and generic external best practices are **MAY** guidance.

A skill, AI reviewer, decision model, or CI check MUST NOT silently override a MUST source.

## Security interpretation

`SECURITY.md` defines what Hermes treats as an actual security boundary.

Reviews MUST distinguish:
- containment / authorization boundaries;
- defense-in-depth heuristics such as approval gates, redaction, allowlists, and skill guards;
- product-correctness bugs;
- operational hardening.

A heuristic bypass is not automatically a vulnerability unless it crosses a boundary defined by `SECURITY.md`.

## Blocking vs advisory

Blocking checks are reserved for deterministic, low-noise violations such as type/build failures, unsafe workflow permission patterns, and explicit executable supply-chain hazards.

Advisory checks cover patterns that require judgment, such as profile/scope hazards, async scope crossings, architecture drift, and public-surface changes.

## Completion

A PR is not verified or ready without fresh evidence for the exact head being discussed.

Report evidence as:
- **verified** — a current command/check ran successfully;
- **inferred/static** — inspected but not executed;
- **not tested** — no current execution evidence.

Prior-head CI does not verify a newer head.
