# infra/design/ — design-specific infrastructure

Things that belong to *this design*, not to a reusable component: Kafka topics (`KafkaTopic` CRs),
S3 buckets / SQS queues (a Job using the aws component), extra databases (CNPG `Database` CRs),
Envoy Gateway policies (rate limits, JWT auth, retries) for the design's routes.

`make up` applies it after all components are installed:
- `install.sh` if present (full control), otherwise
- `kustomization.yaml` via `kubectl apply -k infra/design`

Owned by the infra-builder agent. Empty in the template.
