#!/usr/bin/env sh
set -eu

CADDYFILE_PATH="${CADDYFILE_PATH:-/etc/caddy/Caddyfile}"

python3 /usr/local/bin/generate-caddyfile.py > "$CADDYFILE_PATH"

echo "Generated Caddyfile:"
cat "$CADDYFILE_PATH"

exec caddy run --config "$CADDYFILE_PATH" --adapter caddyfile
