import json
import tempfile
import threading
import time
import unittest
from pathlib import Path

from redblue_arena.control import AccessDenied, ControlPlane, QuotaExceeded
from redblue_arena.runner import JobCancelled, Runner

CONFIG = {
    "authorized": True,
    "allowed_targets": ["lab://training"],
    "target": "lab://training",
    "scenario": "failed-logins",
}


class BlockingRunner:
    mode = "test"

    def __init__(self):
        self.started = threading.Event()

    def execute(self, config, cancel):
        self.started.set()
        cancel.wait(5)
        raise JobCancelled()


class ControlTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "test.sqlite"
        self.control = ControlPlane(self.db, Runner("trusted-local"))
        self.token = self.control.provision("a", "alice", "admin", ["lab://training"])
        self.admin = self.control.authenticate(self.token)
        self.viewer = self.control.authenticate(
            self.control.provision("a", "viewer", "viewer", ["lab://training"])
        )
        self.other = self.control.authenticate(
            self.control.provision("b", "bob", "admin", ["lab://other"])
        )

    def tearDown(self):
        self.control.close()
        self.tmp.cleanup()

    def completed(self, job_id):
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            job = self.control.job(self.admin, job_id)
            if job["status"] not in {"queued", "running"}:
                return job
            time.sleep(0.01)
        self.fail("Worker did not finish")

    def test_end_to_end_and_tenant_isolation(self):
        job_id = self.control.submit(self.admin, CONFIG, True)
        job = self.completed(job_id)
        self.assertEqual(job["status"], "completed")
        self.assertEqual(len(job["report"]["findings"]), 1)
        self.assertEqual(self.control.jobs(self.other), [])
        with self.assertRaises(AccessDenied):
            self.control.job(self.other, job_id)
        self.assertEqual(self.control.job(self.viewer, job_id)["status"], "completed")
        self.assertTrue(self.control.audit(self.admin)["verified"])

    def test_policy_denials_audited_and_no_job_created(self):
        for principal, config, confirmed in [
            (self.viewer, CONFIG, True),
            (self.admin, CONFIG, False),
            (self.other, CONFIG, True),
            (self.admin, {**CONFIG, "authorized": False}, True),
        ]:
            with self.subTest(principal=principal), self.assertRaises(ValueError):
                self.control.submit(principal, config, confirmed)
        self.assertEqual(self.control.jobs(self.admin), [])
        self.assertEqual(
            sum(r["action"] == "job.rejected" for r in self.control.audit(self.admin)["entries"]), 3
        )

    def test_active_quota_and_cancellation(self):
        blocker = BlockingRunner()
        self.control.runner = blocker
        self.control.max_active = 1
        job_id = self.control.submit(self.admin, CONFIG, True)
        self.assertTrue(blocker.started.wait(2))
        with self.assertRaises(QuotaExceeded):
            self.control.submit(self.admin, CONFIG, True)
        with self.assertRaises(AccessDenied):
            self.control.cancel(self.other, job_id)
        with self.assertRaises(AccessDenied):
            self.control.cancel(self.viewer, job_id)
        self.control.cancel(self.admin, job_id)
        self.assertEqual(self.control.job(self.admin, job_id)["status"], "cancelled")

    def test_daily_quota_persistence_and_revocation(self):
        self.control.daily_quota = 1
        self.completed(self.control.submit(self.admin, CONFIG, True))
        with self.assertRaises(QuotaExceeded):
            self.control.submit(self.admin, CONFIG, True)
        self.control.revoke(self.token)
        with self.assertRaises(AccessDenied):
            self.control.authenticate(self.token)
        with self.control.connection() as db:
            self.assertNotIn(
                self.token, json.dumps([dict(r) for r in db.execute("SELECT * FROM users")])
            )

    def test_audit_tamper_detection_and_retention(self):
        job_id = self.control.submit(self.admin, CONFIG, True)
        self.completed(job_id)
        with self.control.connection() as db:
            db.execute("UPDATE jobs SET updated=0 WHERE id=?", (job_id,))
        self.assertEqual(self.control.prune(self.admin), 1)
        self.assertIsNone(self.control.job(self.admin, job_id)["report"])
        self.assertTrue(self.control.audit(self.admin)["verified"])
        with self.control.connection() as db:
            db.execute("UPDATE audit SET action='tampered' WHERE tenant='a' AND seq=1")
        with self.assertRaises(ValueError):
            self.control.audit(self.admin)

    def test_single_database_owner(self):
        with self.assertRaises(ValueError):
            ControlPlane(self.db)

    def test_restart_fails_interrupted_jobs_without_replaying(self):
        with self.control.connection() as db:
            db.execute(
                "INSERT INTO jobs VALUES (?,?,?,?,?,?,?,?,?)",
                ("interrupted", "a", "alice", "running", 0, 0, json.dumps(CONFIG), None, None),
            )
        self.control.close()
        self.control = ControlPlane(self.db, Runner("trusted-local"))
        self.assertEqual(self.control.job(self.admin, "interrupted")["status"], "failed")
        self.assertTrue(self.control.audit(self.admin)["verified"])
