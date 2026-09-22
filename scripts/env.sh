# shellcheck shell=bash
# Repo-local environment. Keeps kubeconfig, helm repos/cache and tilt state inside the repo
# so nothing in your home directory is modified.
#
#   source scripts/env.sh        # use kubectl/helm/tilt against this lab's cluster from your shell
#
# Every script and Makefile target sources this automatically.

SDL_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.." && pwd)"
export SDL_ROOT

export KUBECONFIG="$SDL_ROOT/.kube/config"
export HELM_CONFIG_HOME="$SDL_ROOT/.cache/helm/config"
export HELM_CACHE_HOME="$SDL_ROOT/.cache/helm/cache"
export HELM_DATA_HOME="$SDL_ROOT/.cache/helm/data"
export TILT_DEV_DIR="$SDL_ROOT/.cache/tilt"

# Cluster / registry names (must match infra/cluster/ctlptl.yaml)
export SDL_CLUSTER="kind-sdl"
export SDL_KIND_NAME="sdl"
export SDL_GATEWAY_URL="${SDL_GATEWAY_URL:-http://localhost:8080}"

# Homebrew on Linux installs outside the default PATH of non-login shells.
if [ -d /home/linuxbrew/.linuxbrew/bin ] && ! command -v kind >/dev/null 2>&1; then
  export PATH="/home/linuxbrew/.linuxbrew/bin:$PATH"
fi

export KUBECTL_CONTEXT="$SDL_CLUSTER"
