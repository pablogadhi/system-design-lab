# System Design Lab

Build system designs end to end on a local multi-node Kubernetes cluster, then break them on purpose.
Draw a design in Excalidraw, hand it to Claude Code, and get working infra + services + a demo client,
verified by e2e tests, load tests and chaos experiments.

```
                    http://localhost:8080
                           │
                ┌──────────▼──────────┐   kind cluster "sdl": 1 control plane + 4 workers
                │ Envoy Gateway (API  │   zone-a: worker, worker4 · zone-b: worker2 · zone-c: worker3
                │ gateway, NodePort)  │
                └───┬────────────┬────┘
        /api/<svc>/…│            │ /
            ┌───────▼───┐   ┌────▼────┐     ns apps: services + client (generic chart, spread over zones)
            │ services  │   │ client  │
            └───────┬───┘   └─────────┘
                    │ <component>-conn secrets
            ┌───────▼─────────────────────┐   ns data: components (postgres, kafka, redis, …)
            │ components (operators)      │
            └─────────────────────────────┘
  platform: cert-manager · metrics-server · Prometheus + Grafana · Chaos Mesh · local registry :5005
```

## Quick start

```bash
make doctor          # read-only check: tools, Docker, kernel limits (installs nothing)
make up              # cluster + platform + components from stack.yaml   (~5 min first time)
make smoke           # components really work (writes/reads, replication)
make ci              # build + deploy services and client with Tilt, then run the e2e tests
open http://localhost:8080          # the demo client
make load            # k6 against the gateway
make chaos E=postgres-primary-kill  # break something (see chaos/README.md)
make down
```

Tools you need (the lab never installs them): docker, kind, kubectl, helm, ctlptl, tilt, uv, node,
pnpm, k6, python3. To use kubectl/helm against the lab from your shell: `source scripts/env.sh`
(kubeconfig and helm state live in the repo, your `~/.kube/config` is untouched).

## Building a design

```bash
# 1. In Excalidraw: File → Save to… (.excalidraw) and Export image (.png)
make new-design N=ad-aggregator ARGS="--diagram ~/Downloads/ad.excalidraw --png ~/Downloads/ad.png"
cd ../ad-aggregator && claude
> /build-design
```

`/build-design` runs this flow (details in `.claude/skills/build-design/SKILL.md`):

1. **Architect** (main session, with you): parses the diagram, writes `design/spec.md` + contracts
   (OpenAPI, event schemas, DB schemas, config matrix) and `stack.yaml`. **You approve the spec.**
2. **Builders in parallel** (subagents, each owning its folders):
   `infra-builder` (components + design infra), `services-builder` (FastAPI services, pipelines),
   `client-builder` (Next.js flows).
3. **Integrator** brings everything up, runs smoke/e2e/load/chaos, fixes wiring or reports defects
   back to the owning builder until green.
4. **Results** in `design/RESULTS.md`; new components are proposed for harvesting back into the template.

## Components: built on demand, harvested back

The template only ships Postgres (CloudNativePG). Everything else (Kafka, Redis, Elasticsearch,
Cassandra, Flink, Temporal, AWS emulation) is built the first time a design needs it, following
`infra/components/AUTHORING.md` and the researched approaches in `infra/components/PLAYBOOK.md`.
Then `make harvest C=kafka` pushes it to the template as branch `component/kafka`; merge it there and
every later design reuses it.

## The sample stack

`stack.yaml` ships a tiny sample (Postgres ha + `services/sample-api` + a client page) that proves the
whole toolchain works; `new-design.sh` removes it. Sample files: `services/sample-api/`,
`design/spec.md`, `design/contracts/{openapi/sample-api.yaml,db/postgres.sql}`,
`client/src/api/sample-api.ts`, `tests/e2e/test_sample.py`, `loadtest/sample.js`.

## Layout

See `CLAUDE.md` for the full ownership map and conventions.

```
design/      input diagram + spec + contracts        infra/cluster/     kind + registry (ctlptl)
services/    FastAPI uv workspace (+ sdl_common)     infra/platform/    gateway, monitoring, chaos
pipelines/   stream jobs (Flink)                     infra/components/  reusable backing infra
client/      Next.js demo                            infra/design/      design-specific infra
tests/e2e/   acceptance flows                        infra/charts/app/  generic workload chart
loadtest/    k6 scripts          chaos/  experiments  scripts/          lab tooling
```
