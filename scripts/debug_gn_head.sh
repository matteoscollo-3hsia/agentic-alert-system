#!/usr/bin/env bash
set -euo pipefail

URL_DEFAULT="https://news.google.com/rss/search?q=%22piano%20strategico%22%20OR%20%22piano%20industriale%22%20OR%20%22strategic%20plan%22&hl=it&gl=IT&ceid=IT:it"
URL="${1:-$URL_DEFAULT}"

curl -I -sS "$URL" | awk 'BEGIN{IGNORECASE=1} NR==1 || /^location:/ || /^content-type:/ {print}'
