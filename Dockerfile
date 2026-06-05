FROM caddy:2-builder-alpine AS builder

RUN xcaddy build \
    --with github.com/caddy-dns/cloudflare

FROM caddy:2-alpine

RUN apk add --no-cache python3

COPY --from=builder /usr/bin/caddy /usr/bin/caddy
COPY scripts/generate-caddyfile.py /usr/local/bin/generate-caddyfile.py
COPY scripts/entrypoint.sh /usr/local/bin/entrypoint.sh

RUN chmod +x /usr/local/bin/generate-caddyfile.py /usr/local/bin/entrypoint.sh

EXPOSE 80 443

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
