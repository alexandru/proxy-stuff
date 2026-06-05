# API Proxy

Docker image for a small LAN reverse proxy. It maps local path prefixes to upstream API base URLs.

```text
http://192.168.0.121/claude/v1/messages
-> https://api.anthropic.com/v1/messages
```

## Image

```text
ghcr.io/alexandru/proxy-stuff:latest
```

## Compose samples

- `docs/docker-compose.example.yaml` — simple HTTP deployment
- `docs/docker-compose.https-cloudflare.example.yaml` — HTTPS with Cloudflare DNS-01
- `docs/docker-compose.static-ip.example.yaml` — static-IP `qnet` sample using `192.168.0.121`

## Configuration

Required:

- `ROUTE_MAP`: JSON object mapping local prefixes to upstream base URLs.

Optional:

- `ENABLE_HTTPS`: defaults to `false`
- `HTTP_PORT`: defaults to `80`
- `PROXY_DOMAIN`: required when `ENABLE_HTTPS=true`
- `CLOUDFLARE_API_TOKEN`: required when `ENABLE_HTTPS=true`

Example:

```yaml
ROUTE_MAP: >
  {
    "/claude/v1": "https://api.anthropic.com/v1",
    "/codex/v1": "https://api.openai.com/v1",
    "/opencode-go/v1": "http://opencode-go:1235/v1",
    "/deepseek/v1": "https://api.deepseek.com",
    "/kimi/v1": "https://api.moonshot.ai/v1"
  }
```

Note: Claude uses Anthropic's API format. OpenCode Go's URL is a placeholder for a same-network endpoint; adjust it if needed.

## HTTPS

HTTPS uses Caddy with the Cloudflare DNS plugin. For LAN HTTPS:

1. Own a real domain.
2. Point local DNS for `PROXY_DOMAIN` to the LAN IP, e.g. `192.168.0.121`.
3. Provide a zone-scoped Cloudflare API token with DNS edit permission.
4. Keep `/data` mounted so Caddy can retain certificate state.

## Build and test

```sh
make test
make build-amd64
make smoke-test
```

`make build-amd64` targets `linux/amd64`.

## Publish

GitHub Actions: run **Publish Docker image** manually. It builds `linux/amd64` and `linux/arm64` separately, then publishes a multi-arch manifest.

Local publish:

```sh
docker login ghcr.io
make publish TAG=latest
```

Publish x64 only:

```sh
make publish PLATFORMS=linux/amd64 TAG=latest
```
