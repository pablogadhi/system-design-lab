# Authoring a component

A _component_ is a piece of backing infrastructure (Kafka, Redis, Flink, …) that designs select in
`stack.yaml`. Components are built **on demand** the first time a design needs one, then harvested
back into the template (`scripts/harvest-component.sh`) so the next design reuses them.

`postgres/` is the reference implementation — copy its shape.

## Layout

```
infra/components/<name>/
├── install.sh        # usage: install.sh <profile>   — idempotent; installs operator + instance + conn secret
├── uninstall.sh      # removes the instance (and its data); operators may stay
├── smoke.sh          # proves real behaviour; exit non-zero on failure
├── README.md         # what it is, profiles, connection contract, experiments worth running
├── profiles/
│   ├── small/        # kustomize overlay (or small.yaml helm values) — minimum footprint
│   └── ha/           # replicated across zones — for failure experiments
└── base/             # shared manifests (kustomize) — or values/ for helm-only components
```

Name: lower-kebab, the technology (`kafka`, `redis`, `elasticsearch`, `flink`, `temporal`, `aws`).

## Rules

1. **Scripts** start with `source "$(dirname "$0")/../../../scripts/lib.sh"` and use its helpers:
   `kc` (kubectl on the lab context), `helm_repo`, `helm_install <release> <chart> <version> <ns>`,
   `wait_for`, `run_once <ns> <image> <cmd…>`, `log/ok/warn/die`.
2. **Pin every version** (chart + app image) as variables at the top of `install.sh`. Look up current
   versions (helm search / context7 / release pages) when creating the component — never guess.
3. **Namespaces:** operators in their own namespace (e.g. `strimzi-system`); instances in `data`.
4. **Placement:** replicated profiles spread over `topology.kubernetes.io/zone` (topologySpreadConstraints
   or the operator's rack/zone awareness). Set requests/limits on everything; keep `small` light
   (the whole lab shares ~30 GiB).
5. **No Bitnami** charts/images (moved to a legacy, unmaintained catalog in 2025). Prefer the upstream
   operator (see PLAYBOOK.md), then official images.
6. **Metrics:** if the component exposes Prometheus metrics, add a ServiceMonitor/PodMonitor (any
   namespace is scraped). Grafana dashboards: ConfigMap labelled `grafana_dashboard: "1"`.
7. **UI (optional):** expose tool UIs host-based through the gateway, e.g. `kafka-ui.localhost` —
   HTTPRoute with `parentRefs: [{name: sdl, namespace: envoy-gateway-system}]`.

## The connection contract (most important)

Every component publishes **one Secret named `<name>-conn` in namespace `apps`**, labelled
`sdl.dev/conn: "true"`, with UPPER_SNAKE keys. Services mount it by listing the component in
`connections:` of their deploy values; the chart turns it into env vars prefixed `<NAME>_`.

| Component     | Secret               | Keys (→ env)                                                                    |
| ------------- | -------------------- | ------------------------------------------------------------------------------- |
| postgres      | `postgres-conn`      | `HOST READ_HOST PORT USER PASSWORD DATABASE URL READ_URL` → `POSTGRES_URL`, …   |
| kafka         | `kafka-conn`         | `BOOTSTRAP_SERVERS` (+ `SECURITY_PROTOCOL` if not PLAINTEXT)                    |
| redis         | `redis-conn`         | `URL` (`redis://…`), `MODE` (`standalone`/`cluster`/`sentinel`), `HOST`, `PORT` |
| elasticsearch | `elasticsearch-conn` | `URL`, `USERNAME`, `PASSWORD`                                                   |
| cassandra     | `cassandra-conn`     | `CONTACT_POINTS`, `PORT`, `LOCAL_DC`, `USERNAME`, `PASSWORD`, `KEYSPACE`        |
| temporal      | `temporal-conn`      | `ADDRESS` (`host:7233`), `NAMESPACE`                                            |
| flink         | `flink-conn`         | `REST_URL` (jobs usually don't need it; pipelines deploy FlinkDeployments)      |
| aws           | `aws-conn`           | `ENDPOINT_URL`, `REGION`, `ACCESS_KEY_ID`, `SECRET_ACCESS_KEY` (dummy)          |

Because names are fixed by convention, the architect writes contracts and services code against them
_before_ the component exists. Hosts are always FQDNs (`<svc>.data.svc.cluster.local`) because the
secret is consumed from another namespace. If you need a key not listed here, add it to this table.

## Design-specific setup is NOT part of the component

Topics, buckets, keyspaces, indices, extra databases belong to the design: put them in
`infra/design/` (applied by infra-builder after components are up, e.g. Strimzi `KafkaTopic` CRs,
a Job that creates buckets). The component stays reusable across designs.

## Done means

- `infra/components/<name>/install.sh <profile>` works on a fresh `make up` and when re-run
- `make smoke C=<name>` passes for both profiles you ship
- README documents profiles, the contract keys, and 1–3 failure experiments worth running
- a PLAYBOOK.md row exists/updated with what you learned (gotchas, versions)
