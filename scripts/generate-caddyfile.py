#!/usr/bin/env python3
"""Generate a Caddyfile from container environment variables."""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from typing import cast
from urllib.parse import urlparse


@dataclass(frozen=True)
class Route:
    path: str
    upstream_origin: str
    upstream_host: str
    upstream_base_path: str


def fail(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None or value == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def parse_route_map() -> dict[str, str]:
    raw = os.environ.get("ROUTE_MAP", "").strip()
    if not raw:
        fail("ROUTE_MAP is required")

    try:
        parsed: object = json.loads(raw)
    except json.JSONDecodeError as exc:
        fail(f"ROUTE_MAP must be valid JSON: {exc}")
        raise AssertionError("unreachable") from exc

    if not isinstance(parsed, dict) or not parsed:
        fail("ROUTE_MAP must be a non-empty JSON object")
    parsed_dict = cast(dict[object, object], parsed)

    for key, value in parsed_dict.items():
        if not isinstance(key, str) or not isinstance(value, str):
            fail("ROUTE_MAP keys and values must be strings")
    return cast(dict[str, str], parsed_dict)


def normalize_route_path(path: str) -> str:
    path = path.strip()
    if not path.startswith("/"):
        fail(f"route path must start with /: {path}")
    if len(path) > 1 and path.endswith("/"):
        path = path.rstrip("/")
    if "?" in path or "#" in path:
        fail(f"route path must not contain query strings or fragments: {path}")
    return path


def parse_upstream(url: str) -> tuple[str, str, str]:
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"}:
        fail(f"upstream must use http or https: {url}")
    if not parsed.netloc:
        fail(f"upstream must include a host: {url}")
    if parsed.query or parsed.fragment:
        fail(f"upstream must not include query strings or fragments: {url}")

    origin = f"{parsed.scheme}://{parsed.netloc}"
    base_path = parsed.path or ""
    if len(base_path) > 1 and base_path.endswith("/"):
        base_path = base_path.rstrip("/")
    return origin, parsed.netloc, base_path


def build_routes(route_map: dict[str, str]) -> list[Route]:
    routes = []
    for route_path, upstream in route_map.items():
        normalized_path = normalize_route_path(route_path)
        origin, host, base_path = parse_upstream(upstream)
        routes.append(Route(normalized_path, origin, host, base_path))

    # More-specific paths first prevents /foo from shadowing /foo/bar.
    return sorted(routes, key=lambda route: len(route.path), reverse=True)


def generate_caddyfile(routes: list[Route]) -> str:
    enable_https = env_bool("ENABLE_HTTPS", False)
    http_port = os.environ.get("HTTP_PORT", "80").strip() or "80"
    proxy_domain = os.environ.get("PROXY_DOMAIN", "").strip()

    if enable_https:
        if not proxy_domain:
            fail("PROXY_DOMAIN is required when ENABLE_HTTPS=true")
        if not os.environ.get("CLOUDFLARE_API_TOKEN"):
            fail("CLOUDFLARE_API_TOKEN is required when ENABLE_HTTPS=true")
        site_address = proxy_domain
    else:
        site_address = f":{http_port}"

    lines: list[str] = [f"{site_address} {{"]
    if enable_https:
        lines.extend(
            [
                "    tls {",
                "        dns cloudflare {env.CLOUDFLARE_API_TOKEN}",
                "    }",
                "",
            ]
        )

    lines.extend(
        [
            "    respond /healthz 200",
            "",
        ]
    )

    for index, route in enumerate(routes):
        route_patterns = f"{route.path} {route.path}/*" if route.path != "/" else "/*"
        rewrite_target = f"{route.upstream_base_path}{{uri}}" if route.upstream_base_path else "{uri}"
        lines.extend(
            [
                f"    @route_{index} path {route_patterns}",
                f"    handle @route_{index} {{",
                "        route {",
            ]
        )
        if route.path != "/":
            lines.append(f"            uri strip_prefix {route.path}")
        lines.extend(
            [
                f"            rewrite * {rewrite_target}",
                f"            reverse_proxy {route.upstream_origin} {{",
                f"                header_up Host {route.upstream_host}",
                "            }",
                "        }",
                "    }",
                "",
            ]
        )

    lines.extend(
        [
            "    respond \"No route configured for {path}\" 404",
            "}",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    route_map = parse_route_map()
    routes = build_routes(route_map)
    print(generate_caddyfile(routes), end="")


if __name__ == "__main__":
    main()
