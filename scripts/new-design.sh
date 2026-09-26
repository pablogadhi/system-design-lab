#!/usr/bin/env bash
# Start a new design from this template ("fork" = local git clone).
#
#   scripts/new-design.sh <name> [--dir <path>] [--diagram <file.excalidraw>] [--png <file.png>]
#
# - clones the template to ../<name>, next to the template (or --dir); `origin` points back at the template, so
#   components built in the design can be harvested back (scripts/harvest-component.sh)
# - removes the sample stack (sample-api, its contract/tests/load test, the sample client page)
# - copies the diagram in and generates design/diagram.graph.md
# Then: cd into it, open Claude Code and run /build-design.
source "$(dirname "$0")/lib.sh"

name=""; dir=""; diagram=""; png=""
while [ $# -gt 0 ]; do
  case $1 in
    --dir) dir=$2; shift 2 ;;
    --diagram) diagram=$2; shift 2 ;;
    --png) png=$2; shift 2 ;;
    -*) die "unknown flag $1" ;;
    *) name=$1; shift ;;
  esac
done
[[ "$name" =~ ^[a-z][a-z0-9-]*$ ]] || die "usage: new-design.sh <kebab-name> [--dir path] [--diagram f.excalidraw] [--png f.png]"
dest=${dir:-"$(dirname "$SDL_ROOT")/$name"}
[ -e "$dest" ] && die "$dest already exists"
git -C "$SDL_ROOT" rev-parse HEAD >/dev/null 2>&1 || die "the template has no commits yet"
[ -z "$(git -C "$SDL_ROOT" status --porcelain)" ] || warn "template has uncommitted changes — they are NOT included in the clone"

log "cloning template -> $dest"
mkdir -p "$(dirname "$dest")"
git clone -q "$SDL_ROOT" "$dest"
cd "$dest"

log "removing the sample stack"
# Keep in sync with the sample files in the template (README.md -> "The sample stack").
git rm -rq \
  services/sample-api \
  tests/e2e/test_sample.py \
  loadtest/sample.js \
  design/contracts/openapi/sample-api.yaml \
  design/contracts/db/postgres.sql \
  client/src/api/sample-api.ts \
  design/spec.md

# starter files (empty stack.yaml, config matrix, placeholder client page) — see the overlay's README
overlay=scripts/new-design-overlay
(cd "$overlay" && find . -type f ! -path ./README.md) | while read -r f; do
  mkdir -p "$(dirname "$f")"
  sed "s/__NAME__/$name/g" "$overlay/$f" > "$f"
done
cp design/SPEC_TEMPLATE.md design/spec.md
mkdir -p tests/e2e loadtest design/contracts/openapi design/contracts/db design/contracts/events
touch tests/e2e/.gitkeep loadtest/.gitkeep design/contracts/openapi/.gitkeep design/contracts/db/.gitkeep design/contracts/events/.gitkeep

if [ -n "$diagram" ]; then
  cp "$diagram" design/diagram.excalidraw
  python3 scripts/excalidraw_to_graph.py design/diagram.excalidraw -o design/diagram.graph.md
fi
[ -n "$png" ] && cp "$png" design/diagram.png

(cd services && uv lock --quiet) || warn "uv lock failed — run 'cd services && uv lock' later"

# point Claude Code's commands at this clone's kubeconfig/helm/tilt state (absolute paths, so not
# committed): kubectl/helm run outside the sandbox and would otherwise fall back to ~/.kube/config
mkdir -p .claude
(source scripts/env.sh && python3 -c 'import json, os, sys
print(json.dumps({"env": {k: os.environ[k] for k in sys.argv[1:]}}, indent=2))' \
  KUBECONFIG HELM_CONFIG_HOME HELM_CACHE_HOME HELM_DATA_HOME TILT_DEV_DIR) > .claude/settings.local.json

git add -A
git commit -qm "Start design '$name' from template $(git -C "$SDL_ROOT" rev-parse --short HEAD)"
ok "design '$name' ready at $dest"
echo "   next: cd \"$dest\" && claude    then run: /build-design"
[ -z "$diagram" ] && echo "   (no diagram yet: put diagram.excalidraw + diagram.png in design/)"
