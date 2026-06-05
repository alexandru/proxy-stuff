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
    "/opencode-go/v1": "https://opencode.ai/zen/go/v1",
    "/deepseek/v1": "https://api.deepseek.com",
    "/kimi/v1": "https://api.kimi.com/coding/v1"
  }
```

[See the samples](./samples/).

## HTTPS

For enabling HTTPS, even on local LAN:

1. Own a real domain with the DNS managed via Cloudflare, to be configured in `PROXY_DOMAIN`.
2. For local LAN you can point the DNS for `PROXY_DOMAIN` to the LAN IP, e.g. `192.168.0.121`.
3. Provide a zone-scoped Cloudflare API token with DNS edit permission.

HOW-TO create the Cloudflare token:

1. Go to [Profile / API Tokens](https://dash.cloudflare.com/profile/api-tokens)
2. Create token (you can use either "custom token" or the "Edit zone DNS" template)
3. Set permissions: `Zone` / `DNS` / `Edit`.
4. Zone Resources: include only your domain/zone.
5. Create/copy token and use it as `CLOUDFLARE_API_TOKEN`.
