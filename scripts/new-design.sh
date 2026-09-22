#!/usr/bin/env bash
# Start a new design from this template ("fork" = local git clone).
#
#   scripts/new-design.sh <name> [--dir <path>] [--diagram <file.excalidraw>] [--png <file.png>]
#
# - clones the template to ../designs/<name> (or --dir); `origin` points back at the template, so
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
dest=${dir:-"$(dirname "$SDL_ROOT")/designs/$name"}
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

python3 - "$name" <<'EOF'
import re, sys, pathlib
name = sys.argv[1]
p = pathlib.Path("services/pyproject.toml")
p.write_text(re.sub(r'members = \[.*?\]', 'members = ["libs/*"]', p.read_text(), flags=re.S))
pathlib.Path("stack.yaml").write_text(f"""# What this design runs — written by the architect step of /build-design (see design/spec.md).
#   make up      -> creates the cluster, installs the platform, then each component below (in order)
#   make dev/ci  -> Tilt builds + deploys the services, pipelines and client below
name: {name}

components: []         # - name: kafka / profile: ha      (infra/components/<name>/)

services: []           # services/<name>/

pipelines: []          # pipelines/<name>/

client: true           # client/
""")
pathlib.Path("design/contracts/config.md").write_text("""# Configuration matrix

Which connection contracts and env vars each workload gets (written by the architect).
`connections:` entries become env vars with a prefix: `postgres` -> `POSTGRES_URL`, ...
(keys per component: infra/components/AUTHORING.md).

| Workload | connections | extra env | route |
|---|---|---|---|
| client | — | — | `/` |
""")
pathlib.Path("client/src/app/page.tsx").write_text(f'''// Placeholder — the client-builder agent replaces this with the flows in design/spec.md.
export default function Home() {{
  return (
    <>
      <h1>{name}</h1>
      <p className="muted">Nothing here yet. Run /build-design in Claude Code.</p>
    </>
  );
}}
''')
EOF
cp design/SPEC_TEMPLATE.md design/spec.md
mkdir -p tests/e2e loadtest design/contracts/openapi design/contracts/db design/contracts/events
touch tests/e2e/.gitkeep loadtest/.gitkeep design/contracts/openapi/.gitkeep design/contracts/db/.gitkeep design/contracts/events/.gitkeep

if [ -n "$diagram" ]; then
  cp "$diagram" design/diagram.excalidraw
  python3 scripts/excalidraw_to_graph.py design/diagram.excalidraw -o design/diagram.graph.md
fi
[ -n "$png" ] && cp "$png" design/diagram.png

(cd services && uv lock --quiet) || warn "uv lock failed — run 'cd services && uv lock' later"

git add -A
git commit -qm "Start design '$name' from template $(git -C "$SDL_ROOT" rev-parse --short HEAD)"
ok "design '$name' ready at $dest"
echo "   next: cd \"$dest\" && claude    then run: /build-design"
[ -z "$diagram" ] && echo "   (no diagram yet: put diagram.excalidraw + diagram.png in design/)"
