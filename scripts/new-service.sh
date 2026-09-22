#!/usr/bin/env bash
# usage: new-service.sh <name>    (kebab-case, e.g. click-receiver)
# Copies services/_template to services/<name>, registers it in the uv workspace and relocks.
# Add it to stack.yaml `services:` yourself (or let the architect do it).
source "$(dirname "$0")/lib.sh"

name=${1:-}; [[ "$name" =~ ^[a-z][a-z0-9-]*[a-z0-9]$ ]] || die "usage: new-service.sh <kebab-case-name>"
module=${name//-/_}
dest="$SDL_ROOT/services/$name"
[ -e "$dest" ] && die "services/$name already exists"

cp -r "$SDL_ROOT/services/_template" "$dest"
mv "$dest/src/__MODULE__" "$dest/src/$module"
grep -rl -e '__SERVICE__' -e '__MODULE__' "$dest" | while read -r f; do
  sed -i -e "s/__SERVICE__/$name/g" -e "s/__MODULE__/$module/g" "$f"
done

python3 - "$SDL_ROOT/services/pyproject.toml" "$name" <<'EOF'
import re, sys
path, name = sys.argv[1], sys.argv[2]
text = open(path).read()
members = re.search(r'members = \[(.*?)\]', text, re.S)
items = [m.strip().strip('"') for m in members.group(1).split(",") if m.strip()]
if name not in items:
    items.append(name)
    text = text[:members.start(1)] + ", ".join(f'"{i}"' for i in items) + text[members.end(1):]
    open(path, "w").write(text)
EOF

(cd "$SDL_ROOT/services" && uv lock --quiet)
ok "services/$name created (module $module). Next: add '$name' to stack.yaml services, write its contract."
