#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cat <<CRON
# Daily pipeline run (add SLACK_WEBHOOK_URL in modo sicuro, non qui)
SHELL=/bin/bash
PATH=/usr/local/bin:/usr/bin:/bin
ALERTS_ENABLED=true
ALERT_CHANNEL=slack
30 8 * * * /usr/bin/env bash -lc "source $ROOT_DIR/scripts/.env.local; $ROOT_DIR/scripts/run_daily_local.sh"
CRON
