#!/usr/bin/env sh
set -eu

docker compose -f docker-compose.local-test.yaml up --build -d

cleanup() {
  docker compose -f docker-compose.local-test.yaml down --remove-orphans
}
trap cleanup EXIT

for _ in $(seq 1 30); do
  if curl -fsS http://localhost:8080/healthz >/dev/null; then
    break
  fi
  sleep 1
done

curl -fsS http://localhost:8080/healthz >/dev/null
curl -fsS 'http://localhost:8080/mock/v1/responses?example=1' | grep '"path"' | grep '/v1/responses'

echo "Smoke test passed"
