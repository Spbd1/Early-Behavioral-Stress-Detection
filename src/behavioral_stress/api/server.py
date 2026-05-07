"""Minimal stdlib API/static server for the browser dashboard."""

from __future__ import annotations

import argparse
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from behavioral_stress.api.dashboard_data import build_dashboard_payload
from behavioral_stress.ops.health import build_health_report


class DashboardHandler(SimpleHTTPRequestHandler):
    frontend_dir = Path("frontend")
    data_dir = Path("data/synthetic")
    config_path = Path("configs/default.yaml")

    def do_GET(self) -> None:  # noqa: N802 - stdlib API
        if self.path == "/api/health":
            self._json(build_health_report(self.config_path).as_dict())
            return
        if self.path == "/api/dashboard.json":
            self._json(build_dashboard_payload(self.data_dir, self.config_path))
            return
        if self.path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def translate_path(self, path: str) -> str:
        return str((self.frontend_dir / path.lstrip("/")).resolve())

    def _json(self, payload: dict[str, object]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> int:
    parser = argparse.ArgumentParser(description="Serve experimental behavioral-stress dashboard.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--frontend-dir", type=Path, default=Path("frontend"))
    parser.add_argument("--data-dir", type=Path, default=Path("data/synthetic"))
    parser.add_argument("--config", type=Path, default=Path("configs/default.yaml"))
    args = parser.parse_args()
    DashboardHandler.frontend_dir = args.frontend_dir
    DashboardHandler.data_dir = args.data_dir
    DashboardHandler.config_path = args.config
    server = ThreadingHTTPServer((args.host, args.port), DashboardHandler)
    print(f"Serving dashboard on http://{args.host}:{args.port}")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
