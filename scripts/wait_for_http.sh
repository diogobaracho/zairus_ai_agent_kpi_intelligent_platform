#!/usr/bin/env bash
# wait_for_http.sh URL TIMEOUT_SECONDS — poll until HTTP 200.
set -u
url=$1; timeout=${2:-60}; start=$(date +%s)
until curl -fsS "$url" >/dev/null 2>&1; do
  if [ $(( $(date +%s) - start )) -ge "$timeout" ]; then echo "timeout waiting for $url"; exit 1; fi
  sleep 1
done
echo "ready: $url"
