#!/usr/bin/env bash
# Load a CSV of test cases into a user's project on this server.
#
#   bash deploy/load-testcases.sh <user-email> <project-name-or-key> <csv-file>
#
# Example:
#   bash deploy/load-testcases.sh kalainathan11@gmail.com Pim deploy/seed/pharmacy-inventory-testcases.csv
set -euo pipefail

[ "$#" -eq 3 ] || { sed -n '2,9p' "$0"; exit 2; }
EMAIL="$1"; PROJECT="$2"; CSV="$3"
cd "${APP_DIR:-/opt/testpilot}"
[ -f "$CSV" ] || { echo "CSV not found: $CSV" >&2; exit 1; }

compose=(docker compose --env-file .env.production -f docker-compose.prod.yml)
"${compose[@]}" cp deploy/load_testcases.py backend:/tmp/load_testcases.py
"${compose[@]}" cp "$CSV" backend:/tmp/cases.csv
trap '"${compose[@]}" exec -T backend rm -f /tmp/load_testcases.py /tmp/cases.csv >/dev/null 2>&1 || true' EXIT
"${compose[@]}" exec -T backend python /tmp/load_testcases.py "$EMAIL" "$PROJECT" /tmp/cases.csv
