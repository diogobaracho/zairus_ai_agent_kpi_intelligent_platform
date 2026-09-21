#!/usr/bin/env bash
# Toolchain check. Prints versions; exits non-zero if a required tool is missing.
set -u
ok=0
check() { # name, command, required(1/0)
  if v=$($2 2>&1 | head -1); then printf '  %-10s %s\n' "$1" "$v"; else
    if [ "$3" = 1 ]; then printf '  %-10s MISSING (required)\n' "$1"; ok=1; else printf '  %-10s missing (optional)\n' "$1"; fi; fi
}
echo "Toolchain:"
check uv "uv --version" 1
check python "python3 --version" 1
check node "node --version" 1
check pnpm "pnpm --version" 1
check docker "docker --version" 1
check compose "docker compose version" 1
check kubectl "kubectl version --client --short" 0
exit $ok
