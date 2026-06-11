from __future__ import annotations

import argparse
import json
import os
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
for line in (ROOT / ".env.local").read_text(encoding="utf-8").splitlines() if (ROOT / ".env.local").exists() else []:
    if line and not line.startswith("#") and "=" in line:
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())

from party_quest.billing import BillingConfigurationError, create_checkout, verify_entitlement
from party_quest.generator import QuestRequest, generate_quest


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT / "web"), **kwargs)

    def _json(self, payload, status=200):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            return self._json({"status": "ok", "product": "party-quest-maker"})
        if parsed.path == "/api/entitlement":
            try:
                query = parse_qs(parsed.query)
                return self._json(verify_entitlement(query.get("session_id", [""])[0], query.get("install_id", [""])[0]))
            except Exception:
                return self._json({"active": False}, 502)
        if parsed.path.startswith("/assets/"):
            self.path = parsed.path.removeprefix("/assets/")
        return super().do_GET()

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length) or b"{}")
            if self.path == "/api/generate":
                return self._json(generate_quest(QuestRequest.validate(payload)))
            if self.path == "/api/checkout":
                return self._json({"url": create_checkout(f"http://{self.headers.get('Host')}", str(payload.get("install_id", "")))})
        except (ValueError, BillingConfigurationError) as exc:
            return self._json({"error": str(exc)}, 422)
        except Exception:
            return self._json({"error": "Request failed."}, 500)
        self.send_error(404)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8802)
    args = parser.parse_args()
    print(f"Party Quest Maker running at http://127.0.0.1:{args.port}")
    ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()
