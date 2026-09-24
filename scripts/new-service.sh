#!/usr/bin/env bash
# usage: new-service.sh <name>    (kebab-case, e.g. click-receiver)
# Copies services/_template to services/<name> and relocks the uv workspace (which globs services/*).
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

# the workspace picks up services/* by glob (services/pyproject.toml), so relocking registers it
(cd "$SDL_ROOT/services" && uv lock --quiet)
ok "services/$name created (module $module). Next: add '$name' to stack.yaml services, write its contract."
