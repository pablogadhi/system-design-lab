# Component playbook

Recommended approach per technology, so components built on demand stay consistent. These are
starting points researched in Sept 2026 — **verify current versions and docs when building**
(context7 / official docs), and update the row with anything you learn.

| Component | Status | Approach | Notes / gotchas |
|---|---|---|---|
| **postgres** | built | CloudNativePG operator (chart `cnpg/cloudnative-pg`), `Cluster` CR | ha = 3 instances, anti-affinity on zone. `-rw`/`-ro` services = primary/replicas. Sync replication is a spec switch. |
| **kafka** | todo | Strimzi operator (KRaft only — ZooKeeper is gone), `Kafka` + `KafkaNodePool` CRs; topics as `KafkaTopic` CRs | ha = 3 brokers/controllers, `rack.topologyKey: topology.kubernetes.io/zone` for rack-aware replica placement. UI: kafbat/kafka-ui at `kafka-ui.localhost`. Plain listener on 9092 inside the cluster. |
| **redis** | todo | Official `redis` image (Redis 8, AGPL/RSAL) — or `valkey/valkey` (BSD) as drop-in. OT-Container-Kit redis-operator for `RedisCluster` / `RedisReplication`+`RedisSentinel` | Decide mode per design: cluster mode changes the client (`redis.cluster.RedisCluster`). Put `MODE` in `redis-conn`. Avoid Bitnami charts. |
| **elasticsearch** | todo | ECK operator (Elastic Cloud on Kubernetes, free Basic license), `Elasticsearch` + `Kibana` CRs | Needs `vm.max_map_count>=262144` on the Docker VM (Docker Desktop: already 262144). small = 1 node, 1Gi heap; ha = 3 nodes with zone awareness (`node.attr.zone`). Default is TLS + auth: expose `URL` with https and the elastic user in the conn secret, or disable TLS on http for the lab. |
| **cassandra** | todo | cass-operator (K8ssandra), `CassandraDatacenter` CR | Requires cert-manager (installed by the platform). One rack per zone. Cassandra is memory-hungry: small = 1 node 1Gi heap. Python driver: `cassandra-driver` (`LOCAL_DC` must match). |
| **flink** | todo | Apache Flink Kubernetes Operator (`FlinkDeployment`, `FlinkSessionJob`) | Webhook needs cert-manager (installed). Operator must watch namespace `apps` (`watchNamespaces`); pipelines deploy their `FlinkDeployment` there so they can read the `*-conn` secrets. Jobs live in `pipelines/<name>/` with their own Tiltfile: Flink SQL via the operator's SQL runner pattern, or PyFlink in a custom image `flink:<ver>` + `apache-flink`. Checkpoints to a PVC or S3 (aws component) to make failure experiments meaningful. |
| **temporal** | todo | `temporalio/helm-charts` using CNPG Postgres for persistence (create `temporal` + `temporal_visibility` DBs via CNPG `Database` CRs). `lite` profile: single `temporalio/temporal` dev-server pod (`temporal server start-dev`) | UI at `temporal.localhost`. Workers are regular services (kind: worker) using the `temporalio` Python SDK with `TEMPORAL_ADDRESS`. |
| **aws** | todo | **Floci** (MIT, no account, LocalStack-compatible port 4566) as Deployment + PVC; **MiniStack** as fallback | LocalStack needs an account + auth token since 2026.03 (free tier non-commercial); MinIO OSS is archived — avoid both. Higher fidelity single services: SeaweedFS (S3), ElasticMQ (SQS), DynamoDB Local. boto3 honours `AWS_ENDPOINT_URL`; use path-style S3 addressing. Pin the image; trust the smoke test (S3 put/get, SQS send/receive), not feature claims. |

## Real AWS (only when emulation isn't enough)
New accounts (since Jul 2025): $100 credit + up to $100 more; the *Free plan* can't be billed and closes
after 6 months / when credits run out. Always-free: Lambda 1M req, SQS 1M req, SNS 1M publishes,
DynamoDB 25 GB (S3 is paid from credits). Add a Zero-Spend budget. Components never require it.
