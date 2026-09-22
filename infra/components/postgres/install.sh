#!/usr/bin/env bash
# usage: install.sh [small|ha]
source "$(dirname "$0")/../../../scripts/lib.sh"
HERE="$(cd "$(dirname "$0")" && pwd)"
PROFILE=${1:-small}
CNPG_CHART_VERSION=0.29.0   # operator 1.30.0

[ -d "$HERE/profiles/$PROFILE" ] || die "postgres: unknown profile '$PROFILE'"

helm_repo cnpg https://cloudnative-pg.io/charts
helm repo update cnpg >/dev/null
helm_install cnpg cnpg/cloudnative-pg "$CNPG_CHART_VERSION" cnpg-system

log "postgres: applying profile '$PROFILE'"
kc apply -k "$HERE/profiles/$PROFILE" >/dev/null
wait_for "postgres cluster to be created" 60 kc -n data get cluster.postgresql.cnpg.io/postgres
kc -n data wait --for=condition=Ready cluster.postgresql.cnpg.io/postgres --timeout=600s >/dev/null

# Connection contract: Secret postgres-conn in namespace apps (see README.md)
wait_for "postgres-app secret" 60 kc -n data get secret postgres-app
user=$(kc -n data get secret postgres-app -o jsonpath='{.data.username}' | base64 -d)
pass=$(kc -n data get secret postgres-app -o jsonpath='{.data.password}' | base64 -d)
host=postgres-rw.data.svc.cluster.local
read_host=postgres-ro.data.svc.cluster.local
enc_pass=$(python3 -c 'import sys,urllib.parse; print(urllib.parse.quote(sys.argv[1], safe=""))' "$pass")
kc -n apps create secret generic postgres-conn \
  --from-literal=HOST="$host" \
  --from-literal=READ_HOST="$read_host" \
  --from-literal=PORT=5432 \
  --from-literal=USER="$user" \
  --from-literal=PASSWORD="$pass" \
  --from-literal=DATABASE=app \
  --from-literal=URL="postgresql://$user:$enc_pass@$host:5432/app" \
  --from-literal=READ_URL="postgresql://$user:$enc_pass@$read_host:5432/app" \
  --dry-run=client -o yaml | kc label --local -f - sdl.dev/conn=true -o yaml | kc apply -f - >/dev/null

ok "postgres ($PROFILE) ready — secret apps/postgres-conn"
