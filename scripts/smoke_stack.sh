#!/usr/bin/env bash
# One-line health story for a running stack: healthz, readyz, one REST call, one chat run.
set -euo pipefail
API=${KPI_API_URL:-http://localhost:8080}
ok() { printf '  %-12s ok  %s\n' "$1" "$2"; }
fail() { printf '  %-12s FAIL %s\n' "$1" "$2"; exit 1; }
curl -fsS "$API/healthz" >/dev/null && ok healthz "$API/healthz" || fail healthz "$API/healthz"
READY=$(curl -fsS "$API/readyz") && ok readyz "$READY" || fail readyz "$API/readyz"
T=$(curl -fsS "$API/v1/companies?q=orbitly" | python3 -c 'import json,sys; print(json.load(sys.stdin)["items"][0]["ticker"])') && ok companies "q=orbitly -> $T" || fail companies "search"
N=$(bash "$(dirname "$0")/demo_chat.sh" "What is ORBY total revenue QTD?" | grep -c "^event: tool_call_finished" || true)
[ "$N" -ge 1 ] && ok chat "$N tool call(s) streamed" || fail chat "no tool calls streamed"
echo "stack ok"
