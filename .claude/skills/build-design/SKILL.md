---
name: build-design
description: Build a system design end to end in the System Design Lab from design/diagram.excalidraw + diagram.png — architect the spec and contracts with the user, dispatch infra/services/client builder subagents in parallel, then run the integrator until the design works on the local cluster. Use when the user runs /build-design or asks to build/implement the design from the diagram.
---

# /build-design

You are the **orchestrator** (and the architect). Builders are subagents defined in
`.claude/agents/`. Read `CLAUDE.md` before starting. Work in phases; don't skip checkpoints.

## Phase 0 — Preflight

1. `make doctor`. If anything is missing, stop and tell the user (never install tools).
2. Need `design/diagram.excalidraw` + `design/diagram.png`. If the user only has an SVG or PNG,
   ask them to export the `.excalidraw` too (File → Save to…); a PNG alone works but wiring is guessed.
3. `make graph` → `design/diagram.graph.md`. Read it **and** look at `design/diagram.png` (Read tool).
   The graph gives exact wiring; the image gives layout and meaning the JSON lacks.

## Phase 1 — Architect (you, interactively)

Read `design/SPEC_TEMPLATE.md`, `infra/components/AUTHORING.md` (connection contract table),
`infra/components/PLAYBOOK.md`, and list `infra/components/` (what already exists).

Map the diagram to the lab's building blocks:

| Diagram box                        | Lab building block                                                                                                        |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| API gateway / load balancer        | Envoy Gateway (already there) + K8s Service — **not** a service to build; rate limits/auth go in `infra/design/` policies |
| "X service", "Y API", receivers    | FastAPI service (public or internal) — replicas instead of drawn pools                                                    |
| queue / stream / broker cluster    | component (kafka, aws SQS…) + topics in `infra/design/`                                                                   |
| stream processor / aggregator      | pipeline (Flink) or a consumer worker service if trivial                                                                  |
| DB / cache / search / object store | component + schema in `contracts/db/`                                                                                     |
| workflow engine                    | temporal component + worker service                                                                                       |
| client / user / advertiser         | Next.js pages (one per flow)                                                                                              |

Write, in this order:

1. `design/spec.md` (from `SPEC_TEMPLATE.md`): requirements from the diagram's notes; **laptop
   scale-down table**; components with profiles (`ha` where the design's point is failure behaviour);
   services table; topics/keys/partitions; acceptance flows; load targets; chaos hypotheses derived
   from every failure-related NFR; open questions/assumptions.
2. `design/contracts/`: `openapi/<service>.yaml` for every public service (paths are relative to
   `/api/<service>`), `events/<topic>.schema.json`, `db/<component>.sql`, `config.md`.
   Use the AUTHORING conventions for connection env names even for components that don't exist yet.
3. `stack.yaml`: components (with profile, in dependency order), services, pipelines, client.

Keep it buildable: prefer fewer services with clear responsibilities over one per box; state
delivery semantics (at-least-once + idempotent consumer, etc.) explicitly.

Ask the user (AskUserQuestion) about anything marked `(inferred)` in the graph that matters, and
about real ambiguities. Then show a short summary (components, services, flows, experiments) and
**wait for the user's approval of the spec.** Commit: `git add -A && git commit -m "spec: <design>"`.

## Phase 2 — Build in parallel

Dispatch in **one message** (parallel):

- `infra-builder`: all components + `infra/design/`.
- `services-builder`: all services + pipelines — or several instances, one per group of services,
  when there are more than ~3 services (give each an explicit list).
- `client-builder`: the client.

Each prompt: the design name, what exactly to build (name the services/components/sections of the
spec), "read CLAUDE.md, design/spec.md and your agent instructions", and "report back in the format
your instructions define". They share nothing but the repo — the contracts are how they agree.

When all return: read the reports, check for contract interpretations that conflict (e.g. env var
names, topic names). Resolve conflicts by fixing the **contract** (you own it) and re-dispatching the
affected builders (SendMessage to the same agent to keep its context). Commit: `build: <design>`.

## Phase 3 — Integrate until green

Dispatch `integrator` with the builders' reports. On `STATUS: FAIL`, route each defect to its owner
(SendMessage to that builder with the defect verbatim), then re-run the integrator. Stop after
3 rounds without progress and bring the remaining defects to the user with your diagnosis.
Architect-owned defects (spec/contract wrong) are yours: fix, then re-dispatch.

## Phase 4 — Results

1. Write `design/RESULTS.md`: what was built (components, services, flows), how to run it
   (`make up && make ci`, URLs), the load and chaos numbers from the integrator, which NFRs held and
   which didn't (with why), and ideas for next experiments.
2. Commit: `results: <design>`.
3. For every component created in this design (not in the template before): offer to run
   `make harvest C=<name>` so the template gains it. Only run it if the user agrees.
4. Tell the user: what works, the URLs, the headline numbers, and the harvest status.
