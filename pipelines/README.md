# pipelines/ — stream processing jobs

One folder per job, listed under `pipelines:` in `stack.yaml`. Each has its own `Tiltfile` (included by
the root Tiltfile) that builds the job image and deploys it — for Flink, a `FlinkDeployment` in namespace
`apps` (see the flink row in `infra/components/PLAYBOOK.md`). Owned by the services-builder agent.

```
pipelines/<name>/
├── Tiltfile          # docker_build(...) + k8s_yaml('deploy/flinkdeployment.yaml')
├── Dockerfile        # FROM flink:<pinned> + job (PyFlink or SQL runner)
├── job/              # the job code (Flink SQL / PyFlink)
├── deploy/           # FlinkDeployment (parallelism, checkpointing, env from <component>-conn secrets)
└── README.md         # what it computes, delivery guarantees, how to observe it
```

Empty in the template.
