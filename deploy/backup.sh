#!/usr/bin/env bash
# Nightly Postgres backup for TestPilot (installed as a cron job by deploy/deploy.sh).
#
#   Output : /var/backups/testpilot/testpilot-<UTC timestamp>.sql.gz   (root-only, mode 600)
#   Retain : KEEP_DAYS days (default 14)
#   Restore: see deploy/README-backup.md or the one-liner printed with --help
#
# A backup only counts if it is a valid gzip stream that contains the schema; a failed run
# never replaces or deletes good backups.
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/testpilot}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/testpilot}"
KEEP_DAYS="${KEEP_DAYS:-14}"

if [ "${1:-}" = "--help" ]; then
  cat <<HELP
Restore (replaces the current database contents):
  gunzip -c /var/backups/testpilot/<file>.sql.gz | \
    docker compose --env-file $APP_DIR/.env.production -f $APP_DIR/docker-compose.prod.yml \
    exec -T db sh -c 'psql -U "\$POSTGRES_USER" -d "\$POSTGRES_DB"'
HELP
  exit 0
fi

cd "$APP_DIR"
umask 077
mkdir -p "$BACKUP_DIR"

stamp="$(date -u +%Y%m%dT%H%M%SZ)"
out="$BACKUP_DIR/testpilot-$stamp.sql.gz"
tmp="$out.partial"
trap 'rm -f "$tmp"' EXIT

compose=(docker compose --env-file .env.production -f docker-compose.prod.yml)
"${compose[@]}" exec -T db sh -c \
  'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner --clean --if-exists' \
  | gzip -9 > "$tmp"

gzip -t "$tmp"                                             # valid gzip stream
gunzip -c "$tmp" | grep -q "CREATE TABLE public.users"      # actually contains the schema
mv "$tmp" "$out"
trap - EXIT

# Retention: only after a good backup exists.
find "$BACKUP_DIR" -name 'testpilot-*.sql.gz' -type f -mtime "+$KEEP_DAYS" -delete

echo "$(date -u +%FT%TZ) backup ok: $out ($(du -h "$out" | cut -f1)), kept $(find "$BACKUP_DIR" -name 'testpilot-*.sql.gz' | wc -l) file(s)"
