#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TEMPLATE_PATH="$ROOT_DIR/scripts/launchd/com.agentic-alert.daily.plist.template"
OUTPUT_PATH="$ROOT_DIR/scripts/launchd/com.agentic-alert.daily.plist"
LAUNCHD_DIR="$HOME/Library/LaunchAgents"
LAUNCHD_PLIST="$LAUNCHD_DIR/com.agentic-alert.daily.plist"

mkdir -p "$LAUNCHD_DIR"
mkdir -p "$ROOT_DIR/logs"
mkdir -p "$ROOT_DIR/.cache/uv"

sed "s|__REPO_PATH__|$ROOT_DIR|g; s|__HOME__|$HOME|g" "$TEMPLATE_PATH" > "$OUTPUT_PATH"

cp "$OUTPUT_PATH" "$LAUNCHD_PLIST"

if [[ -z "${SLACK_WEBHOOK_URL:-}" ]]; then
  if [[ -t 0 ]]; then
    read -r -s -p "Enter SLACK_WEBHOOK_URL: " SLACK_WEBHOOK_URL
    echo
  fi
fi

if [[ -z "${SLACK_WEBHOOK_URL:-}" ]]; then
  echo "ERROR: SLACK_WEBHOOK_URL not set. Export it before running install script."
  exit 1
fi

set_plist_var() {
  local key="$1"
  local value="$2"
  /usr/libexec/PlistBuddy -c "Set :EnvironmentVariables:$key \"$value\"" "$LAUNCHD_PLIST" >/dev/null 2>&1 || \
    /usr/libexec/PlistBuddy -c "Add :EnvironmentVariables:$key string \"$value\"" "$LAUNCHD_PLIST" >/dev/null 2>&1
}

set_plist_var "ALERTS_ENABLED" "true"
set_plist_var "ALERT_CHANNEL" "slack"
set_plist_var "SLACK_WEBHOOK_URL" "$SLACK_WEBHOOK_URL"

launchctl unload "$LAUNCHD_PLIST" 2>/dev/null || true
launchctl load "$LAUNCHD_PLIST"
launchctl start com.agentic-alert.daily

cat <<INFO
Installed launchd agent:
- $LAUNCHD_PLIST

Status:
- launchctl list | grep com.agentic-alert.daily

Stop:
- launchctl stop com.agentic-alert.daily

Uninstall:
- launchctl unload "$LAUNCHD_PLIST" && rm -f "$LAUNCHD_PLIST"
INFO
