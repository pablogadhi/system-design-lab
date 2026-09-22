#!/usr/bin/env bash
# Removes the postgres cluster and its data (the operator stays; it is cheap).
source "$(dirname "$0")/../../../scripts/lib.sh"
kc -n apps delete secret postgres-conn --ignore-not-found >/dev/null
kc -n data delete cluster.postgresql.cnpg.io/postgres --ignore-not-found --wait >/dev/null
kc -n data delete podmonitor postgres --ignore-not-found >/dev/null
ok "postgres removed"
