import json
import tempfile
import threading
import unittest
from http.client import HTTPConnection
from pathlib import Path

from redblue_arena.control import ControlPlane
from redblue_arena.runner import Runner
from redblue_arena.web import LabServer

CONFIG = {
    "authorized": True,
    "allowed_targets": ["lab://training"],
    "target": "lab://training",
    "scenario": "failed-logins",
}


class WebTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.control = ControlPlane(Path(self.tmp.name) / "test.sqlite", Runner("trusted-local"))
        self.token = self.control.provision("a", "alice", "admin", ["lab://training"])
        self.viewer = self.control.provision("a", "viewer", "viewer", ["lab://training"])
        self.server = LabServer(0, self.control)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(2)
        self.control.close()
        self.tmp.cleanup()

    def request(self, path, method="GET", body=None, headers=None, token=None):
        conn = HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        values = {"Authorization": "Bearer " + (token or self.token)}
        if body is not None:
            values["Content-Type"] = "application/json"
        values.update(headers or {})
        conn.request(method, path, json.dumps(body) if body is not None else None, values)
        response = conn.getresponse()
        status, response_headers, raw = (
            response.status,
            dict(response.getheaders()),
            response.read(),
        )
        conn.close()
        return status, response_headers, raw

    def test_health_and_dashboard_security_headers(self):
        status, headers, body = self.request("/")
        self.assertEqual(status, 200)
        self.assertIn(b"RedBlue Arena", body)
        self.assertIn("frame-ancestors 'none'", headers["Content-Security-Policy"])
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertEqual(self.request("/app.js")[0], 200)

    def test_auth_and_browser_boundaries(self):
        self.assertEqual(self.request("/api/jobs", headers={"Authorization": ""})[0], 403)
        self.assertEqual(
            self.request("/api/jobs", headers={"Origin": "http://untrusted.invalid"})[0], 403
        )
        self.assertEqual(self.request("/api/jobs", headers={"Host": "untrusted.invalid"})[0], 403)
        self.assertEqual(self.request("/api/me")[0], 200)

    def test_submit_read_cancel_and_roles(self):
        status, _, raw = self.request(
            "/api/jobs", "POST", {"config": CONFIG, "scope_confirmed": True}
        )
        self.assertEqual(status, 202)
        job_id = json.loads(raw)["job_id"]
        self.assertEqual(self.request("/api/jobs/" + job_id)[0], 200)
        self.assertEqual(self.request("/api/jobs/" + job_id + "/cancel", "POST", {})[0], 200)
        self.assertEqual(
            self.request(
                "/api/jobs", "POST", {"config": CONFIG, "scope_confirmed": True}, token=self.viewer
            )[0],
            403,
        )
        self.assertEqual(self.request("/api/audit", token=self.viewer)[0], 403)
        self.assertEqual(self.request("/api/audit")[0], 200)

    def test_invalid_payloads_and_scope(self):
        for body in [
            [],
            {},
            {"config": CONFIG, "scope_confirmed": False},
            {"config": CONFIG, "scope_confirmed": True, "extra": 1},
        ]:
            with self.subTest(body=body):
                self.assertIn(self.request("/api/jobs", "POST", body)[0], {400, 403})
        self.assertEqual(
            self.request("/api/jobs", "POST", {}, {"Content-Type": "text/plain"})[0], 400
        )
        self.assertEqual(self.request("/api/jobs/missing")[0], 403)
        self.assertEqual(self.request("/api/jobs", "POST", {}, {"Content-Length": "65537"})[0], 400)

    def test_request_rate_cap(self):
        for _ in range(120):
            self.server.rate_allowed()
        self.assertEqual(self.request("/health")[0], 429)
