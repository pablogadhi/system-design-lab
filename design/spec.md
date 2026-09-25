# Sample — spec

> The template's built-in sample design. It exercises the whole toolchain (component → service →
> gateway → client → e2e → load → chaos) with the smallest possible system. `new-design.sh` removes it.

## 1. Problem

Store and list named items. Writes must be durable; reads may be served from replicas.

## 2. Requirements

**Functional**

1. Create an item with a name.
2. Fetch an item by id; list the newest items.

**Non-functional**

- Survive the loss of the database primary (automatic failover).
- Replica reads may lag; primary reads are read-your-writes.
- Survive the loss of one app replica / one zone's network path to the data tier.

## 3. Laptop scale-down

| Diagram says | Lab target                           | Why                                 |
| ------------ | ------------------------------------ | ----------------------------------- |
| n/a          | 100 writes/s + 200 reads/s for 1 min | enough to see failover impact in k6 |

## 4. Components

| Component | Profile | Status | Connection contract                                     | Design-specific setup       |
| --------- | ------- | ------ | ------------------------------------------------------- | --------------------------- |
| postgres  | ha      | exists | `POSTGRES_URL`, `POSTGRES_READ_URL`, `POSTGRES_HOST`, … | `contracts/db/postgres.sql` |

## 5. Services

| Service    | Kind            | Responsibilities | API                                                      | Consumes | Produces | Stores                                                         |
| ---------- | --------------- | ---------------- | -------------------------------------------------------- | -------- | -------- | -------------------------------------------------------------- |
| sample-api | FastAPI, public | items CRUD       | `contracts/openapi/sample-api.yaml` at `/api/sample-api` | —        | —        | postgres (primary writes, replica reads with `source=replica`) |

## 6. Data & events

- `contracts/db/postgres.sql`: table `items`.
- No events.

## 7. Configuration matrix

| Service    | connections | env |
| ---------- | ----------- | --- |
| sample-api | postgres    | —   |

## 8. Acceptance flows (`tests/e2e/test_sample.py`)

1. Given nothing, when I create an item, then I can fetch it by id.
2. When I create an item, then it eventually appears when listing from a replica.
3. Requests are load-balanced across several replicas (`X-Served-By`).
4. Fetching an unknown id returns 404.
5. The client home page is served at `/`.

## 9. Client

One page: add item, list items, toggle primary/replica reads, show `X-Served-By`.

## 10. Load (`loadtest/sample.js`)

100 writes/s + 200 reads/s for 1 minute; thresholds: <1% errors, p95 writes <150ms, reads <100ms.

## 11. Chaos experiments

| Hypothesis                          | Fault                              | Verification (observed)                                                       |
| ----------------------------------- | ---------------------------------- | ----------------------------------------------------------------------------- |
| DB primary loss is survivable       | `postgres-primary-kill` under load | failover ~20s; ~3.5% writes failed; replica reads unaffected; e2e green after |
| a slow zone only slows its own pods | `zone-a-latency`                   | only zone-a pod slows (~320ms)                                                |
| a partitioned pod leaves rotation   | `partition-apps-data`              | zone-b pod unready; 100% success via other zones                              |

## 12. Open questions

None — this is the reference sample.
