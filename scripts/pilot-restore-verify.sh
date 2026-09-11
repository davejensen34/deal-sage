#!/bin/sh
set -eu

if [ "$#" -ne 1 ]; then
  echo "usage: $0 BACKUP_DIRECTORY" >&2
  exit 2
fi
backup_dir=$(cd "$1" && pwd)

schema_revision=$(python3 - "$backup_dir" <<'PY'
import hashlib, json, pathlib, sys
root = pathlib.Path(sys.argv[1])
manifest = json.loads((root / "manifest.json").read_text())
if manifest.get("format") != "dealsage-pilot-backup-v1" or manifest.get("secrets_included") is not False:
    raise SystemExit("unsupported or unsafe backup manifest")
for name, expected in manifest["files"].items():
    actual = hashlib.sha256((root / name).read_bytes()).hexdigest()
    if actual != expected["sha256"]:
        raise SystemExit(f"backup hash mismatch: {name}")
print(manifest["schema_revision"])
PY
)

project="dealsage-restore-check"
cleanup() { docker compose -p "$project" down -v >/dev/null 2>&1 || true; }
trap cleanup EXIT INT TERM
cleanup
docker compose -p "$project" up -d postgres
until docker compose -p "$project" exec -T postgres pg_isready -U dealsage >/dev/null 2>&1; do sleep 1; done
docker compose -p "$project" exec -T postgres pg_restore -U dealsage -d dealsage --clean --if-exists <"$backup_dir/database.dump"
# The verifier must come from the checkout being tested, not a stale image left
# by an earlier restore exercise.
docker compose -p "$project" build api
docker compose -p "$project" run --rm --no-deps -v "$backup_dir:/backup:ro" api \
  sh -c 'mkdir -p /app/data/evidence && tar -C /app/data/evidence -xzf /backup/evidence.tar.gz'
database_url="postgresql+psycopg://dealsage:dealsage-local@postgres:5432/dealsage"
verification=$(docker compose -p "$project" run --rm --no-deps api python -m app.ops.recovery \
  --database-url "$database_url" --evidence-root /app/data/evidence \
  --expected-schema-revision "$schema_revision")
echo "$verification"
if command -v sha256sum >/dev/null 2>&1; then
  manifest_sha=$(sha256sum "$backup_dir/manifest.json" | awk '{print $1}')
else
  manifest_sha=$(shasum -a 256 "$backup_dir/manifest.json" | awk '{print $1}')
fi
verified_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)
cat >"$backup_dir/restore-verification.json" <<EOF
{"format":"dealsage-restore-verification-v1","verified_at":"$verified_at","manifest_sha256":"$manifest_sha","result":$verification}
EOF
