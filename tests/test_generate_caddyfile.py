import os
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "scripts" / "generate-caddyfile.py"


def run_generator(env):
    merged_env = os.environ.copy()
    merged_env.update(env)
    return subprocess.run(
        [sys.executable, str(GENERATOR)],
        check=False,
        capture_output=True,
        text=True,
        env=merged_env,
    )


class GenerateCaddyfileTest(unittest.TestCase):
    def test_http_mode_generates_health_and_route_rewrite(self):
        result = run_generator(
            {
                "ROUTE_MAP": '{"/claude/v1":"https://api.anthropic.com/v1"}',
                "ENABLE_HTTPS": "false",
                "HTTP_PORT": "8080",
            }
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(":8080 {", result.stdout)
        self.assertIn("respond /healthz 200", result.stdout)
        self.assertIn("@route_0 path /claude/v1 /claude/v1/*", result.stdout)
        self.assertIn("route {", result.stdout)
        strip_prefix_pos = result.stdout.index("uri strip_prefix /claude/v1")
        rewrite_pos = result.stdout.index("rewrite * /v1{uri}")
        self.assertLess(strip_prefix_pos, rewrite_pos)
        self.assertIn("reverse_proxy https://api.anthropic.com", result.stdout)
        self.assertIn("header_up Host api.anthropic.com", result.stdout)

    def test_route_blocks_preserve_prefix_strip_before_rewrite(self):
        result = run_generator(
            {
                "ROUTE_MAP": '{"/mock/v1":"http://upstream:8080/v1"}',
                "ENABLE_HTTPS": "false",
                "HTTP_PORT": "8080",
            }
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("handle @route_0 {", result.stdout)
        self.assertIn("route {", result.stdout)
        self.assertLess(
            result.stdout.index("uri strip_prefix /mock/v1"),
            result.stdout.index("rewrite * /v1{uri}"),
        )
        self.assertIn("reverse_proxy http://upstream:8080", result.stdout)

    def test_https_mode_requires_domain_and_cloudflare_token(self):
        result = run_generator(
            {
                "ROUTE_MAP": '{"/codex/v1":"https://api.openai.com/v1"}',
                "ENABLE_HTTPS": "true",
                "PROXY_DOMAIN": "api-proxy.example.com",
                "CLOUDFLARE_API_TOKEN": "test-token",
            }
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("api-proxy.example.com {", result.stdout)
        self.assertIn("tls {", result.stdout)
        self.assertIn("dns cloudflare {env.CLOUDFLARE_API_TOKEN}", result.stdout)

    def test_invalid_route_map_fails(self):
        result = run_generator({"ROUTE_MAP": "not-json"})

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("ROUTE_MAP must be valid JSON", result.stderr)

    def test_route_paths_must_start_with_slash(self):
        result = run_generator({"ROUTE_MAP": '{"claude/v1":"https://api.anthropic.com/v1"}'})

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("route path must start with /", result.stderr)

    def test_upstreams_must_be_http_urls(self):
        result = run_generator({"ROUTE_MAP": '{"/claude/v1":"file:///tmp/test"}'})

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("upstream must use http or https", result.stderr)


if __name__ == "__main__":
    unittest.main()
