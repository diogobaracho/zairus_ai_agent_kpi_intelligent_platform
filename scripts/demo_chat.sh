#!/usr/bin/env bash
# demo_chat.sh "question" [conversation_id] — stream one chat turn over SSE and print the events.
set -euo pipefail
API=${KPI_API_URL:-http://localhost:8080}
Q=${1:-"What is ORBY total revenue QTD?"}
CONV=${2:-}
BODY=$(python3 -c 'import json,sys; b={"message": sys.argv[1]}; b.update({"conversation_id": sys.argv[2]} if len(sys.argv)>2 and sys.argv[2] else {}); print(json.dumps(b))' "$Q" "$CONV")
curl -sN -X POST "$API/v1/chat" -H 'content-type: application/json' -H 'accept: text/event-stream' -d "$BODY"
echo
