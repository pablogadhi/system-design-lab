#!/usr/bin/env bash
# usage: smoke-all.sh [component]   — runs smoke.sh for one component or every component in stack.yaml
source "$(dirname "$0")/lib.sh"

log "platform: gateway reachable"
code=$(curl -s -o /dev/null -w '%{http_code}' -H 'Host: grafana.localhost' "$SDL_GATEWAY_URL/api/health" || true)
[ "$code" = "200" ] || die "gateway/grafana not reachable at $SDL_GATEWAY_URL (HTTP $code)"
ok "gateway -> grafana"

comps=${1:-$(stack components)}
for c in $comps; do
  "$SDL_ROOT/infra/components/$c/smoke.sh"
done
ok "all smoke tests passed"
