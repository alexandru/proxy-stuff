# QNAP OpenAI-Compatible API Proxy

Docker image project for a LAN reverse proxy that routes path prefixes to OpenAI-compatible API upstreams.

Example:

```text
http://192.168.0.121/claude/v1/responses
-> https://api.anthropic.com/v1/responses
```

## Configuration

All runtime configuration is supplied through environment variables, so the image can be deployed from QNAP Container Station using only `docker-compose.yaml`.

### Required

- `ROUTE_MAP`: JSON object mapping local path prefixes to upstream base URLs.

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

Provider notes:

- Claude: `https://api.anthropic.com/v1` uses Anthropic's API shape, not OpenAI's API shape.
- Codex/OpenAI: `https://api.openai.com/v1`.
- OpenCode Go: OpenCode documents this as an OpenCode-managed provider, not a generic public OpenAI-compatible URL. The sample uses `http://opencode-go:1235/v1` as a placeholder for a same-network OpenAI-compatible OpenCode Go/local endpoint; adjust it to your actual endpoint if different.
- DeepSeek: `https://api.deepseek.com`.
- Kimi/Moonshot: `https://api.moonshot.ai/v1`.

### Optional

- `ENABLE_HTTPS`: `true` or `false`; defaults to `false`.
- `HTTP_PORT`: internal HTTP listen port; defaults to `80`.
- `PROXY_DOMAIN`: required when `ENABLE_HTTPS=true`.
- `CLOUDFLARE_API_TOKEN`: required when `ENABLE_HTTPS=true`.

## HTTP deployment

Use `docs/docker-compose.example.yaml` or the full QNAP static-IP example in `docs/docker-compose.qnap-static-ip.example.yaml`, then deploy it in QNAP Container Station.

```yaml
services:
  api-proxy:
    image: ghcr.io/alexandru/proxy-stuff:latest
    restart: unless-stopped
    ports:
      - "80:80"
    environment:
      ENABLE_HTTPS: "false"
      ROUTE_MAP: >
        {
          "/claude/v1": "https://api.anthropic.com/v1",
          "/codex/v1": "https://api.openai.com/v1",
          "/opencode-go/v1": "http://opencode-go:1235/v1",
          "/deepseek/v1": "https://api.deepseek.com",
          "/kimi/v1": "https://api.moonshot.ai/v1"
        }
```

## QNAP static LAN IP deployment

Use `docs/docker-compose.qnap-static-ip.example.yaml` for a QNAP `qnet` deployment that assigns this container its own LAN IP:

```text
192.168.0.121
```

The sample uses:

- `qnet-static` network on `qvs0`
- static MAC `02:42:53:7B:12:BE`
- persistent Caddy `/data` and `/config` volumes
- `read_only: true` with the generated Caddyfile written to `/tmp/Caddyfile`

If you enable HTTPS, point local DNS for your `PROXY_DOMAIN` to `192.168.0.121`.

## HTTPS with Cloudflare DNS

Trusted HTTPS for an internal LAN service requires a real domain. Configure local DNS so your chosen hostname points to the QNAP IP, for example:

```text
api-proxy.example.com -> 192.168.0.121
```

The container uses Caddy with the Cloudflare DNS plugin. Caddy obtains and renews certificates automatically by creating temporary `_acme-challenge` TXT records through the Cloudflare API.

Create a Cloudflare API token scoped to the zone with DNS edit permission, then pass it as `CLOUDFLARE_API_TOKEN`.

```yaml
services:
  api-proxy:
    image: ghcr.io/alexandru/proxy-stuff:latest
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    environment:
      ENABLE_HTTPS: "true"
      PROXY_DOMAIN: "api-proxy.example.com"
      CLOUDFLARE_API_TOKEN: "${CLOUDFLARE_API_TOKEN}"
      ROUTE_MAP: >
        {
          "/claude/v1": "https://api.anthropic.com/v1",
          "/codex/v1": "https://api.openai.com/v1",
          "/opencode-go/v1": "http://opencode-go:1235/v1",
          "/deepseek/v1": "https://api.deepseek.com",
          "/kimi/v1": "https://api.moonshot.ai/v1"
        }
    volumes:
      - caddy_data:/data
      - caddy_config:/config
```

Keep `/data` mounted so Caddy can retain account and certificate state across restarts.

Compose samples are in `docs/`:

- `docs/docker-compose.example.yaml`
- `docs/docker-compose.https-cloudflare.example.yaml`
- `docs/docker-compose.qnap-static-ip.example.yaml`

## Publishing the image

The workflow in `.github/workflows/publish-image.yaml` is manually dispatched.

1. Push this repository to GitHub.
2. Open **Actions**.
3. Run **Publish Docker image**.
4. Choose a tag, for example `latest`.

The image will be published to:

```text
ghcr.io/alexandru/proxy-stuff:<tag>
```

## Local tests

```sh
python3 -m unittest discover -s tests
```

Generate a Caddyfile manually:

```sh
ROUTE_MAP='{ "/claude/v1": "https://api.anthropic.com/v1" }' \
  python3 scripts/generate-caddyfile.py
```

Build locally:

```sh
docker build -t api-proxy:local .
```

Build the QNAP x64 target locally:

```sh
make build-qnap
```

By default this targets `linux/amd64`, which is the expected architecture for x64 QNAP systems.

Run locally:

```sh
docker run --rm -p 8080:80 \
  -e ENABLE_HTTPS=false \
  -e 'ROUTE_MAP={"/claude/v1":"https://api.anthropic.com/v1"}' \
  api-proxy:local
```

Health check:

```sh
curl http://localhost:8080/healthz
```

Optional Docker smoke test with a mock upstream:

```sh
./scripts/local-smoke-test.sh
```

or:

```sh
make smoke-test
```

## Publishing from local Docker

Log in to GitHub Container Registry first:

```sh
docker login ghcr.io
```

Then publish a multi-arch image for x64 QNAP plus arm64:

```sh
make publish TAG=latest
```

Defaults:

- `PLATFORMS=linux/amd64,linux/arm64`
- `TAG=latest`

To publish only the x64 QNAP image:

```sh
make publish PLATFORMS=linux/amd64
```

## Notes

- The proxy passes client request headers and bodies through to upstreams.
- API keys should be supplied by clients in normal provider-specific headers.
- If HTTPS is enabled, do not use a broad Cloudflare API token; use the narrowest zone-scoped token possible.
- For QNAP x64 systems, use an image that includes `linux/amd64`. The GitHub workflow and `make publish` include `linux/amd64` by default and also publish `linux/arm64` for broader compatibility.
