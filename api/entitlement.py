from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from party_quest.billing import BillingConfigurationError, verify_entitlement  # noqa: E402


class handler(BaseHTTPRequestHandler):
    def _respond(self, payload: object, status: int) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        session_id = parse_qs(urlparse(self.path).query).get("session_id", [""])[0]
        install_id = parse_qs(urlparse(self.path).query).get("install_id", [""])[0]
        try:
            self._respond(verify_entitlement(session_id, install_id), 200)
        except BillingConfigurationError as exc:
            self._respond({"error": str(exc)}, 503)
        except Exception:
            self._respond({"active": False, "reason": "verification_failed"}, 502)
