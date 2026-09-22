#!/usr/bin/env bash
# Read-only environment check. Never installs or changes anything — it only reports.
set -uo pipefail
# shellcheck source=env.sh
source "$(dirname "$0")/env.sh"

fail=0
row() { printf '  %-10s %-8s %s\n' "$1" "$2" "$3"; }

# name | min version | version command | install hint
check() {
  local name=$1 min=$2 cmd=$3 hint=$4
  if ! command -v "$name" >/dev/null 2>&1; then
    row "$name" "MISSING" "install: $hint"; fail=1; return
  fi
  local v; v=$(eval "$cmd" 2>/dev/null | grep -oE '[0-9]+\.[0-9]+(\.[0-9]+)?' | head -1)
  if [ -n "$min" ] && [ "$(printf '%s\n%s\n' "$min" "$v" | sort -V | head -1)" != "$min" ]; then
    row "$name" "OLD" "found $v, need >= $min — $hint"; fail=1
  else
    row "$name" "ok" "$v"
  fi
}

echo "Tools"
check docker  "24.0"  "docker version --format '{{.Client.Version}}'"   "https://docs.docker.com/engine/install/"
check kind    "0.27"  "kind version"                                    "https://kind.sigs.k8s.io/docs/user/quick-start/#installation"
check kubectl "1.31"  "kubectl version --client"                        "https://kubernetes.io/docs/tasks/tools/"
check helm    "3.16"  "helm version --short"                            "https://helm.sh/docs/intro/install/"
check ctlptl  "0.8"   "ctlptl version"                                  "https://github.com/tilt-dev/ctlptl#how-do-i-install-it"
check tilt    "0.33"  "tilt version"                                    "https://docs.tilt.dev/install.html"
check uv      "0.5"   "uv --version"                                    "https://docs.astral.sh/uv/getting-started/installation/"
check node    "20.9"  "node --version"                                  "https://nodejs.org/"
check pnpm    "9.0"   "pnpm --version"                                  "https://pnpm.io/installation"
check k6      "0.50"  "k6 version"                                      "https://grafana.com/docs/k6/latest/set-up/install-k6/"
check python3 "3.10"  "python3 --version"                               "https://www.python.org/downloads/"

echo "Docker"
if docker info >/dev/null 2>&1; then
  cpus=$(docker info --format '{{.NCPU}}'); mem=$(docker info --format '{{.MemTotal}}')
  memg=$((mem / 1024 / 1024 / 1024))
  row daemon ok "$(docker info --format '{{.OperatingSystem}}') — ${cpus} CPUs, ${memg} GiB"
  if [ "$memg" -lt 12 ]; then row memory LOW "kind with 5 nodes + components wants >= 12 GiB for Docker"; fail=1; fi
else
  row daemon DOWN "docker daemon not reachable (is Docker Desktop / dockerd running? current context: $(docker context show 2>/dev/null))"; fail=1
fi

# kind nodes share the kernel Docker runs on: the host's on Docker Engine, the VM's on Docker Desktop.
if docker info --format '{{.OperatingSystem}}' 2>/dev/null | grep -q "Docker Desktop"; then
  echo "Kernel limits inside the Docker Desktop VM (kind nodes run there)"
  vm_sysctls=$(docker run --rm busybox:1.37 sysctl fs.inotify.max_user_watches fs.inotify.max_user_instances vm.max_map_count 2>/dev/null)
  sysval() { echo "$vm_sysctls" | awk -v k="$1" '$1==k{print $3}' | grep . || echo 0; }
else
  echo "Kernel limits (kind multi-node needs these; set via sysctl yourself if flagged)"
  sysval() { sysctl -n "$1" 2>/dev/null || echo 0; }
fi
lim() {
  local key=$1 min=$2 why=$3 v; v=$(sysval "$key")
  if [ "$v" -ge "$min" ]; then row "$key" ok "$v"; else row "$key" LOW "$v < $min ($why)"; fail=1; fi
}
lim fs.inotify.max_user_watches   524288 "kind nodes run out of watches"
lim fs.inotify.max_user_instances 512    "kind nodes fail with 'too many open files'"
# Only needed by Elasticsearch; reported but not fatal
v=$(sysval vm.max_map_count)
if [ "$v" -ge 262144 ]; then row vm.max_map_count ok "$v"; else row vm.max_map_count note "$v (< 262144 — only matters for Elasticsearch)"; fi

echo "Lab"
if [ -f "$KUBECONFIG" ] && kubectl --context "$SDL_CLUSTER" get nodes >/dev/null 2>&1; then
  row cluster up "$SDL_CLUSTER ($(kubectl --context "$SDL_CLUSTER" get nodes --no-headers | wc -l) nodes)"
else
  row cluster down "run: make up"
fi

echo
if [ $fail -eq 0 ]; then echo "doctor: all good"; else echo "doctor: fix the items above (nothing was changed on your system)"; fi
exit $fail
