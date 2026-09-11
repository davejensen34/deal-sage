#!/bin/sh
set -eu

if [ "$#" -ne 1 ]; then
  echo "usage: $0 BACKUP_DIRECTORY" >&2
  exit 2
fi

backup_dir=$(cd "$(dirname "$1")" && pwd)/$(basename "$1")
mkdir -p "$backup_dir"
case "$backup_dir" in
  */.git|*/.git/*) echo "refusing to write a backup inside .git" >&2; exit 2 ;;
esac
if [ -e "$backup_dir/manifest.json" ] || [ -e "$backup_dir/database.dump" ] || [ -e "$backup_dir/evidence.tar.gz" ]; then
  echo "refusing to overwrite an existing backup bundle" >&2
  exit 2
fi

restart_api=false
cleanup() {
  if [ "$restart_api" = true ]; then
    docker compose start api >/dev/null
    attempts=0
    until docker compose exec -T api python -c 'import socket; socket.create_connection(("127.0.0.1", 8000), 2).close()' >/dev/null 2>&1; do
      attempts=$((attempts + 1))
      if [ "$attempts" -ge 30 ]; then
        echo "API did not become reachable after backup" >&2
        return 1
      fi
      sleep 1
    done
    # Nginx resolves the Compose service address at startup; refresh it after
    # the maintenance window so it cannot retain a stale upstream address.
    docker compose restart web >/dev/null
  fi
}
trap cleanup EXIT INT TERM

# Stopping the sole writer creates one consistency boundary across PostgreSQL
# and the separately mounted evidence volume.
docker compose stop api >/dev/null
restart_api=true
docker compose exec -T postgres pg_dump -U dealsage -d dealsage -Fc >"$backup_dir/database.dump"
docker compose run --rm --no-deps -v "$backup_dir:/backup" api \
  tar -C /app/data/evidence -czf /backup/evidence.tar.gz .

schema_revision=$(docker compose exec -T postgres psql -U dealsage -d dealsage -Atc 'select version_num from alembic_version')
hash_file() {
  if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1"; else shasum -a 256 "$1"; fi | awk '{print $1}'
}
database_sha=$(hash_file "$backup_dir/database.dump")
evidence_sha=$(hash_file "$backup_dir/evidence.tar.gz")
created_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)
cat >"$backup_dir/manifest.json" <<EOF
{"format":"dealsage-pilot-backup-v1","created_at":"$created_at","schema_revision":"$schema_revision","files":{"database.dump":{"sha256":"$database_sha"},"evidence.tar.gz":{"sha256":"$evidence_sha"}},"secrets_included":false,"validated_restore":false}
EOF

echo "$backup_dir"
