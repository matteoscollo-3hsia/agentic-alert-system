#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$ROOT_DIR/logs"
LOG_FILE="$LOG_DIR/daily_run_$(date +%Y%m%d).log"
CACHE_DIR="$ROOT_DIR/.cache/uv"

export PATH="/opt/homebrew/bin:/usr/local/bin:$HOME/.local/bin:$HOME/.cargo/bin:$PATH"

mkdir -p "$LOG_DIR"
mkdir -p "$CACHE_DIR"

export UV_CACHE_DIR="$CACHE_DIR"

{
  echo "--- Run started: $(date -u +%Y-%m-%dT%H:%M:%SZ) ---"
  cd "$ROOT_DIR"
  if [[ -z "${PROVIDERS_CSV:-}" && -f "$ROOT_DIR/data_private/providers.csv" ]]; then
    export PROVIDERS_CSV="$ROOT_DIR/data_private/providers.csv"
  fi
  echo "Using providers_csv: ${PROVIDERS_CSV:-data/providers.csv}"

  if ! command -v uv >/dev/null 2>&1; then
    echo "ERROR: uv not found in PATH. Install uv and run 'uv sync' once before enabling launchd/cron."
    exit 1
  fi

  if [[ ! -d "$ROOT_DIR/.venv" ]]; then
    echo "Missing venv. Run 'uv sync' manually once before enabling cron."
    exit 1
  fi

  if [[ "${RUN_UV_SYNC:-false}" == "true" ]]; then
    uv sync
  fi

  hostname
  whoami
  pwd
  scutil --dns | head -n 50

  DNS_HOST_GOOGLE="news.google.com"
  DNS_HOST_PUBLISHER="www.ansa.it"
  DNS_DEADLINE=$((SECONDS + 30))
  DNS_OK=false

  while true; do
    GOOGLE_IP=""
    PUBLISHER_IP=""

    if GOOGLE_IP=$(python - <<'PY' "$DNS_HOST_GOOGLE" 2>/dev/null
import socket
import sys

host = sys.argv[1]
infos = socket.getaddrinfo(host, 443)
print(infos[0][4][0])
PY
    ); then
      GOOGLE_STATUS="ok"
    else
      GOOGLE_STATUS="fail"
      GOOGLE_IP=""
    fi

    if PUBLISHER_IP=$(python - <<'PY' "$DNS_HOST_PUBLISHER" 2>/dev/null
import socket
import sys

host = sys.argv[1]
infos = socket.getaddrinfo(host, 443)
print(infos[0][4][0])
PY
    ); then
      PUBLISHER_STATUS="ok"
    else
      PUBLISHER_STATUS="fail"
      PUBLISHER_IP=""
    fi

    echo "NET_PREFLIGHT google=${GOOGLE_STATUS} ip=${GOOGLE_IP} publisher=${PUBLISHER_STATUS} ip=${PUBLISHER_IP}"

    if [[ "$GOOGLE_STATUS" == "ok" && "$PUBLISHER_STATUS" == "ok" ]]; then
      DNS_OK=true
      break
    fi

    if [[ $SECONDS -ge $DNS_DEADLINE ]]; then
      echo "DNS resolution failed; check launchd network/DNS context"
      exit 2
    fi

    sleep 5
  done

  uv run python -m agentic_alert.pipeline
  echo "--- Run completed: $(date -u +%Y-%m-%dT%H:%M:%SZ) ---"
} >>"$LOG_FILE" 2>&1

printf "Log written to %s\n" "$LOG_FILE"
