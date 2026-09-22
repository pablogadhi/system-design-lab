#!/usr/bin/env bash
# Whole-server failures: stop (or restore) kind node containers.
#
#   chaos/node-down.sh zone-a            # stop every node in zone-a  (AZ outage)
#   chaos/node-down.sh sdl-worker2       # stop one node              (server crash)
#   chaos/node-down.sh zone-a --restore  # start them again
#
# What to expect (real Kubernetes behaviour, worth observing):
#   - the node goes NotReady after ~40s; its pods keep "Running" in the API until then
#   - pods are evicted only after the default 300s toleration -> Deployments reschedule them
#   - StatefulSet/CNPG pods on local-path volumes cannot move: they come back when the node does
source "$(dirname "$0")/../scripts/lib.sh"

target=${1:-}; action=${2:-stop}
[ -n "$target" ] || die "usage: node-down.sh <zone-x|node-name> [--restore]"
[ "$action" = "--restore" ] && action=start

if [[ "$target" == zone-* ]]; then
  nodes=$(kc get nodes -l "topology.kubernetes.io/zone=$target" -o name | sed 's|node/||')
else
  nodes=$target
fi
[ -n "$nodes" ] || die "no nodes match '$target'"

for n in $nodes; do
  log "docker $action $n"
  docker "$action" "$n" >/dev/null
done
ok "done — watch: kubectl get nodes -L topology.kubernetes.io/zone -w"
