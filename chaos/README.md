# Chaos experiments

Failure injection for the running design. Chaos Mesh (dashboard: http://chaos.localhost:8080) handles
pod/network/IO/time faults; `node-down.sh` stops whole kind nodes (servers / zones).

```bash
make chaos E=<file-without-.yaml>     # apply one experiment
make chaos-clear                      # remove all of them
chaos/node-down.sh zone-a             # stop every node in zone-a; --restore to bring them back
```

Run experiments **under load** so you can see the effect: `make load &` then apply the experiment ~15s in.

| Experiment | What it does | Verified behaviour on the sample stack |
|---|---|---|
| `postgres-primary-kill` | kills the CNPG primary | failover in ~20s to another zone; ~3.5% of writes failed, write p95 rose to 2s (max = 15s route timeout); replica reads unaffected; `make e2e` green afterwards |
| `zone-a-latency` | +100ms between zone-a app pods and the data tier (5 min) | zone-a pod ~320ms/request (several DB round trips), other zones unaffected |
| `partition-apps-data` | zone-b app pods cannot reach the data tier (2 min) | zone-b pod fails `/readyz` → gateway stops routing to it, 100% of requests still succeed via zones a/c |

## Writing new experiments (for designs)

Derive them from the spec's non-functional requirements. For each one write down the hypothesis,
e.g. *"no clicks lost when a Kafka broker dies"* → kill a broker under load, then reconcile the counts.

Gotchas:
- **NetworkChaos + Services:** apps reach components through Service (ClusterIP) addresses, which kube-proxy
  translates *after* the packet leaves the pod. With `direction: to`, Chaos Mesh filters on the target
  *pod* IPs inside the source pod and matches nothing — the experiment reports "Injected" but has no
  effect. Use `direction: both` (the fault is also applied on the target side, where return traffic
  carries real pod IPs), or select the component pods as the source.
- Put experiments in namespace `chaos-mesh`; select targets with `selector.namespaces` + labels.
- `nodeSelectors: {topology.kubernetes.io/zone: zone-x}` scopes an experiment to one simulated AZ.
- `node-down.sh`: pods on a stopped node stay "Running" in the API for ~40s (until the node is NotReady)
  and are only evicted after the default 300s toleration. Stateful pods on local-path volumes cannot
  move — they come back with the node. This is real Kubernetes behaviour, worth observing.
