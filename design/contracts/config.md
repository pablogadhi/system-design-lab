# Configuration matrix

Which connection contracts and env vars each workload gets. `connections:` entries become env vars
via `envFrom` with a prefix: `postgres` → `POSTGRES_URL`, `POSTGRES_READ_URL`, `POSTGRES_HOST`, …
(see each component's README for its keys).

| Workload | connections | extra env | route |
|---|---|---|---|
| sample-api | postgres | — | `/api/sample-api` (prefix stripped) |
| client | — | — | `/` |
