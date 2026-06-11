from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from party_quest.billing import BillingConfigurationError, create_checkout  # noqa: E402


class handler(BaseHTTPRequestHandler):
    def _respond(self, payload: object, status: int) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:  # noqa: N802
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length > 2_000:
                return self._respond({"error": "Request is too large."}, 413)
            payload = json.loads(self.rfile.read(length) or b"{}")
            install_id = str(payload.get("install_id", "")) if isinstance(payload, dict) else ""
            proto = self.headers.get("x-forwarded-proto", "https")
            host = self.headers.get("host", "")
            self._respond({"url": create_checkout(f"{proto}://{host}", install_id)}, 200)
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            self._respond({"error": str(exc) or "Check the checkout request."}, 422)
        except BillingConfigurationError as exc:
            self._respond({"error": str(exc)}, 503)
        except Exception:
            self._respond({"error": "Checkout could not be started."}, 502)
