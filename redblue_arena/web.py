"""Loopback-only HTTP API. Not a public Internet server."""

import argparse
import json
import os
import threading
import time
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .control import AccessDenied, ControlPlane, QuotaExceeded
from .dashboard import HTML, JAVASCRIPT
from .runner import Runner


class LabServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, port: int, control: ControlPlane):
        self.control = control
        self._slots = threading.BoundedSemaphore(16)
        self._rate_lock = threading.Lock()
        self._requests = deque()
        super().__init__(("127.0.0.1", port), Handler)

    def process_request(self, request, client_address):
        if not self._slots.acquire(blocking=False):
            request.close()
            return
        try:
            super().process_request(request, client_address)
        except Exception:
            self._slots.release()
            raise

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            self._slots.release()

    def rate_allowed(self):
        with self._rate_lock:
            now = time.monotonic()
            while self._requests and now - self._requests[0] > 60:
                self._requests.popleft()
            if len(self._requests) >= 120:
                return False
            self._requests.append(now)
            return True


class Handler(BaseHTTPRequestHandler):
    server_version = "RedBlueLab"

    def setup(self):
        super().setup()
        self.connection.settimeout(5)

    def log_message(self, format, *args):
        pass  # No tokens, URLs, request bodies, or client details in access logs.

    def send(self, code: int, value, content_type: str = "application/json"):
        raw = json.dumps(value).encode() if content_type == "application/json" else value.encode()
        self.send_response(code)
        self.send_header("Content-Type", content_type + "; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; style-src 'self' 'unsafe-inline'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'",
        )
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        self.dispatch("GET")

    def do_POST(self):
        self.dispatch("POST")

    def dispatch(self, method: str):
        expected = f"127.0.0.1:{self.server.server_port}"
        if self.headers.get("Host") != expected:
            self.send(403, {"error": "Invalid host"})
            return
        origin = self.headers.get("Origin")
        if origin and origin != "http://" + expected:
            self.send(403, {"error": "Invalid origin"})
            return
        if not self.server.rate_allowed():
            self.send(429, {"error": "Request rate exceeded"})
            return
        if method == "GET" and self.path in {"/", "/app.js", "/health"}:
            if self.path == "/":
                self.send(200, HTML, "text/html")
            elif self.path == "/app.js":
                self.send(200, JAVASCRIPT, "application/javascript")
            else:
                self.send(200, {"status": "ok", "runner": self.server.control.runner.mode})
            return
        try:
            auth = self.headers.get("Authorization", "")
            if not auth.startswith("Bearer "):
                raise AccessDenied("Authentication required")
            principal = self.server.control.authenticate(auth[7:])
            body = None
            if method == "POST":
                if self.headers.get("Transfer-Encoding"):
                    raise ValueError("Chunked bodies are not accepted")
                if self.headers.get("Content-Type") != "application/json":
                    raise ValueError("JSON required")
                length = int(self.headers.get("Content-Length", "-1"))
                if not 0 <= length <= 65536:
                    raise ValueError("Body exceeds limit or has no length")
                body = json.loads(self.rfile.read(length))
                if not isinstance(body, dict):
                    raise ValueError("JSON object required")
            control = self.server.control
            if method == "GET" and self.path == "/api/me":
                self.send(
                    200,
                    {
                        "tenant": principal.tenant,
                        "subject": principal.subject,
                        "role": principal.role,
                        "runner": control.runner.mode,
                    },
                )
            elif method == "GET" and self.path == "/api/jobs":
                self.send(200, {"jobs": control.jobs(principal)})
            elif method == "GET" and self.path == "/api/audit":
                self.send(200, control.audit(principal))
            elif method == "GET" and self.path.startswith("/api/jobs/"):
                self.send(200, control.job(principal, self.path.removeprefix("/api/jobs/")))
            elif method == "POST" and self.path == "/api/jobs":
                if set(body) != {"config", "scope_confirmed"}:
                    raise ValueError("Expected config and scope_confirmed")
                job_id = control.submit(principal, body["config"], body["scope_confirmed"])
                self.send(202, {"job_id": job_id})
            elif (
                method == "POST"
                and self.path.startswith("/api/jobs/")
                and self.path.endswith("/cancel")
            ):
                if body:
                    raise ValueError("Cancel body must be empty")
                control.cancel(principal, self.path[len("/api/jobs/") : -len("/cancel")])
                self.send(200, {"status": "cancel_requested"})
            elif method == "POST" and self.path == "/api/retention/prune":
                if body:
                    raise ValueError("Prune body must be empty")
                self.send(200, {"reports_pruned": control.prune(principal)})
            else:
                self.send(404, {"error": "Unknown endpoint"})
        except AccessDenied:
            self.send(403, {"error": "Access denied"})
        except QuotaExceeded:
            self.send(429, {"error": "Job quota exceeded"})
        except (ValueError, TypeError):
            self.send(400, {"error": "Invalid request"})
        except Exception:
            self.send(500, {"error": "Internal error"})


def main():
    parser = argparse.ArgumentParser(description="RedBlue local laboratory control plane")
    parser.add_argument("--db", type=Path, required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    provision = commands.add_parser("provision", help="Trusted host identity provisioning")
    provision.add_argument("--tenant", required=True)
    provision.add_argument("--subject", required=True)
    provision.add_argument("--role", choices=["admin", "analyst", "viewer"], required=True)
    provision.add_argument("--target", action="append", required=True)
    commands.add_parser("revoke", help="Revoke token from REDBLUE_TOKEN environment variable")
    serve = commands.add_parser("serve")
    serve.add_argument("--port", type=int, default=8765)
    serve.add_argument("--runner", choices=["docker", "trusted-local"], default="docker")
    serve.add_argument("--retention-days", type=int, default=7)
    args = parser.parse_args()
    os.umask(0o077)
    control = ControlPlane(
        args.db,
        Runner(getattr(args, "runner", "docker")),
        retention_days=getattr(args, "retention_days", 7),
    )
    try:
        if args.command == "provision":
            print(control.provision(args.tenant, args.subject, args.role, args.target))
        elif args.command == "revoke":
            control.revoke(os.environ.get("REDBLUE_TOKEN", ""))
            print("Token revoked")
        else:
            server = LabServer(args.port, control)
            print(
                f"Local lab: http://127.0.0.1:{server.server_port}; runner={control.runner.mode}",
                flush=True,
            )
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                pass
            finally:
                server.server_close()
    finally:
        control.close()


if __name__ == "__main__":
    main()
