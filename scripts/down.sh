#!/usr/bin/env bash
# usage: down.sh [--all]   (--all also deletes the local image registry and its cached images)
source "$(dirname "$0")/lib.sh"
if [ "${1:-}" = "--all" ]; then
  ctlptl delete -f "$SDL_ROOT/infra/cluster/ctlptl.yaml" --ignore-not-found
else
  ctlptl delete cluster "$SDL_CLUSTER" --ignore-not-found
fi
ok "cluster deleted"
