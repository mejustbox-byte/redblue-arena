"""Local authenticated control plane with SQLite tenant isolation and append-only audit."""

import fcntl
import hashlib
import json
import re
import secrets
import sqlite3
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from .core import validate
from .runner import JobCancelled, Runner


class AccessDenied(ValueError):
    pass


class QuotaExceeded(ValueError):
    pass


@dataclass(frozen=True)
class Principal:
    tenant: str
    subject: str
    role: str


def identifier(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[a-z0-9_-]{1,64}", value):
        raise ValueError("Invalid identifier")
    return value


class ControlPlane:
    def __init__(
        self,
        database: Path,
        runner: Runner | None = None,
        max_active: int = 2,
        daily_quota: int = 100,
        retention_days: int = 7,
    ):
        if (
            not 1 <= max_active <= 16
            or not 1 <= daily_quota <= 1000
            or not 1 <= retention_days <= 365
        ):
            raise ValueError("Invalid resource policy")
        self.database = Path(database)
        self.runner = runner or Runner()
        self.max_active, self.daily_quota, self.retention_days = (
            max_active,
            daily_quota,
            retention_days,
        )
        self._lock = threading.Lock()
        self._signals: dict[str, threading.Event] = {}
        self._pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="redblue")
        self.database.parent.mkdir(parents=True, exist_ok=True)
        if self.database.is_symlink():
            raise ValueError("Database must not be a symlink")
        lock_path = self.database.with_suffix(self.database.suffix + ".lock")
        if lock_path.is_symlink():
            raise ValueError("Lock must not be a symlink")
        self._database_lock = lock_path.open("a")
        lock_path.chmod(0o600)
        try:
            fcntl.flock(self._database_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            self._database_lock.close()
            self._pool.shutdown(wait=False)
            raise ValueError("Database is already in use") from None
        self.database.touch(mode=0o600, exist_ok=True)
        self.database.chmod(0o600)
        with self.connection() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS tenants (id TEXT PRIMARY KEY, targets TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS users (token_hash TEXT PRIMARY KEY, tenant TEXT NOT NULL
                    REFERENCES tenants(id), subject TEXT NOT NULL, role TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, tenant TEXT NOT NULL
                    REFERENCES tenants(id), subject TEXT NOT NULL, status TEXT NOT NULL,
                    created REAL NOT NULL, updated REAL NOT NULL, config TEXT NOT NULL,
                    report TEXT, error TEXT);
                CREATE TABLE IF NOT EXISTS audit (tenant TEXT NOT NULL REFERENCES tenants(id),
                    seq INTEGER NOT NULL, timestamp REAL NOT NULL, subject TEXT NOT NULL,
                    action TEXT NOT NULL, job_id TEXT, previous TEXT NOT NULL, digest TEXT NOT NULL,
                    PRIMARY KEY(tenant, seq));
                CREATE INDEX IF NOT EXISTS jobs_tenant_time ON jobs(tenant, created);
            """)
            # No job replay after an interrupted server. Single server process per database.
            for job in db.execute(
                "SELECT * FROM jobs WHERE status IN ('queued', 'running')"
            ).fetchall():
                db.execute(
                    "UPDATE jobs SET status='failed', error='Server restarted', updated=? WHERE id=?",
                    (time.time(), job["id"]),
                )
                self._audit(
                    db, Principal(job["tenant"], "system", "admin"), "job.interrupted", job["id"]
                )

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.database, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        try:
            with db:
                yield db
        finally:
            db.close()

    def provision(self, tenant: str, subject: str, role: str, targets: list[str]) -> str:
        """Trusted host CLI only; never exposed over HTTP. Returns a token once."""
        identifier(tenant)
        identifier(subject)
        if role not in {"admin", "analyst", "viewer"}:
            raise ValueError("Unknown role")
        validate(
            {
                "authorized": True,
                "allowed_targets": targets,
                "target": targets[0] if targets else "",
                "scenario": "failed-logins",
            }
        )
        token = secrets.token_urlsafe(32)
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            existing = db.execute("SELECT targets FROM tenants WHERE id=?", (tenant,)).fetchone()
            if existing and json.loads(existing[0]) != targets:
                raise ValueError("Existing tenant scope differs; explicit migration required")
            db.execute("INSERT OR IGNORE INTO tenants VALUES (?,?)", (tenant, json.dumps(targets)))
            db.execute(
                "INSERT INTO users VALUES (?,?,?,?)",
                (hashlib.sha256(token.encode()).hexdigest(), tenant, subject, role),
            )
            self._audit(db, Principal(tenant, subject, role), "identity.provisioned", None)
        return token

    def authenticate(self, token: str) -> Principal:
        if not isinstance(token, str) or not 32 <= len(token) <= 256:
            raise AccessDenied("Authentication required")
        with self.connection() as db:
            user = db.execute(
                "SELECT * FROM users WHERE token_hash=?",
                (hashlib.sha256(token.encode()).hexdigest(),),
            ).fetchone()
        if not user:
            raise AccessDenied("Authentication required")
        return Principal(user["tenant"], user["subject"], user["role"])

    def revoke(self, token: str):
        principal = self.authenticate(token)
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute(
                "DELETE FROM users WHERE token_hash=?",
                (hashlib.sha256(token.encode()).hexdigest(),),
            )
            self._audit(db, principal, "identity.revoked", None)

    def _audit(self, db, principal: Principal, action: str, job_id: str | None):
        last = db.execute(
            "SELECT seq,digest FROM audit WHERE tenant=? ORDER BY seq DESC LIMIT 1",
            (principal.tenant,),
        ).fetchone()
        seq, previous = (last[0] + 1, last[1]) if last else (1, "0" * 64)
        if seq > 100000:
            raise QuotaExceeded("Audit capacity reached; trusted host archival required")
        record = [principal.tenant, seq, time.time(), principal.subject, action, job_id, previous]
        digest = hashlib.sha256(json.dumps(record, separators=(",", ":")).encode()).hexdigest()
        db.execute("INSERT INTO audit VALUES (?,?,?,?,?,?,?,?)", (*record, digest))

    def submit(self, principal: Principal, config: dict, scope_confirmed: bool) -> str:
        reason = None
        job_id = uuid.uuid4().hex
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            tenant = db.execute(
                "SELECT targets FROM tenants WHERE id=?", (principal.tenant,)
            ).fetchone()
            if principal.role not in {"admin", "analyst"} or not tenant:
                reason = AccessDenied("Role cannot submit jobs")
            elif scope_confirmed is not True:
                reason = AccessDenied("Explicit scope confirmation required")
            else:
                try:
                    validate(config)
                    allowed = json.loads(tenant[0])
                    if any(t not in allowed for t in config["allowed_targets"]):
                        raise AccessDenied("Config is outside tenant scope")
                except ValueError as exc:
                    reason = exc
            if not reason:
                active = db.execute(
                    "SELECT COUNT(*) FROM jobs WHERE tenant=? AND status IN ('queued','running')",
                    (principal.tenant,),
                ).fetchone()[0]
                daily = db.execute(
                    "SELECT COUNT(*) FROM jobs WHERE tenant=? AND created>?",
                    (principal.tenant, time.time() - 86400),
                ).fetchone()[0]
                total = db.execute(
                    "SELECT COUNT(*) FROM jobs WHERE tenant=?", (principal.tenant,)
                ).fetchone()[0]
                global_active = db.execute(
                    "SELECT COUNT(*) FROM jobs WHERE status IN ('queued','running')"
                ).fetchone()[0]
                if (
                    active >= self.max_active
                    or daily >= self.daily_quota
                    or total >= 1000
                    or global_active >= 16
                ):
                    reason = QuotaExceeded("Tenant job quota exceeded")
            if reason:
                self._audit(db, principal, "job.rejected", None)
            else:
                now = time.time()
                db.execute(
                    "INSERT INTO jobs VALUES (?,?,?,?,?,?,?,?,?)",
                    (
                        job_id,
                        principal.tenant,
                        principal.subject,
                        "queued",
                        now,
                        now,
                        json.dumps(config),
                        None,
                        None,
                    ),
                )
                self._audit(db, principal, "job.queued", job_id)
        if reason:
            raise reason
        signal = threading.Event()
        with self._lock:
            self._signals[job_id] = signal
        self._pool.submit(self._execute, principal, job_id, config, signal)
        return job_id

    def _execute(self, principal, job_id, config, signal):
        try:
            with self.connection() as db:
                db.execute("BEGIN IMMEDIATE")
                changed = db.execute(
                    "UPDATE jobs SET status='running',updated=? WHERE id=? AND status='queued'",
                    (time.time(), job_id),
                ).rowcount
                if not changed:
                    return
                self._audit(db, principal, "job.running", job_id)
            try:
                # Policy revalidated at the worker boundary as well.
                validate(config)
                report = self.runner.execute(config, signal)
                status, error = "completed", None
            except JobCancelled:
                status, error, report = "cancelled", None, None
            except Exception:
                status, error, report = "failed", "Worker failed or timed out", None
            with self.connection() as db:
                db.execute("BEGIN IMMEDIATE")
                changed = db.execute(
                    "UPDATE jobs SET status=?,updated=?,report=?,error=? WHERE id=? AND status='running'",
                    (status, time.time(), json.dumps(report) if report else None, error, job_id),
                ).rowcount
                if changed:
                    self._audit(db, principal, "job." + status, job_id)
        finally:
            with self._lock:
                self._signals.pop(job_id, None)

    def jobs(self, principal: Principal) -> list[dict]:
        with self.connection() as db:
            rows = db.execute(
                "SELECT id,subject,status,created,updated,error FROM jobs WHERE tenant=? ORDER BY created DESC LIMIT 100",
                (principal.tenant,),
            ).fetchall()
        return [dict(row) for row in rows]

    def job(self, principal: Principal, job_id: str) -> dict:
        with self.connection() as db:
            row = db.execute(
                "SELECT * FROM jobs WHERE tenant=? AND id=?", (principal.tenant, job_id)
            ).fetchone()
        if not row:
            raise AccessDenied("Job unavailable")
        result = dict(row)
        result.pop("tenant")
        result["config"] = json.loads(result["config"])
        result["report"] = json.loads(result["report"]) if result["report"] else None
        return result

    def cancel(self, principal: Principal, job_id: str):
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            job = db.execute(
                "SELECT * FROM jobs WHERE tenant=? AND id=?", (principal.tenant, job_id)
            ).fetchone()
            if (
                not job
                or principal.role not in {"admin", "analyst"}
                or (principal.role != "admin" and job["subject"] != principal.subject)
            ):
                self._audit(db, principal, "job.cancel_rejected", None)
                denied = True
            else:
                denied = False
                if job["status"] in {"queued", "running"}:
                    db.execute(
                        "UPDATE jobs SET status='cancelled',updated=? WHERE id=?",
                        (time.time(), job_id),
                    )
                    self._audit(db, principal, "job.cancelled", job_id)
        if denied:
            raise AccessDenied("Cannot cancel job")
        with self._lock:
            signal = self._signals.get(job_id)
            if signal:
                signal.set()

    def audit(self, principal: Principal) -> dict:
        if principal.role != "admin":
            raise AccessDenied("Admin role required")
        with self.connection() as db:
            rows = db.execute(
                "SELECT * FROM audit WHERE tenant=? ORDER BY seq", (principal.tenant,)
            ).fetchall()
        previous = "0" * 64
        for seq, row in enumerate(rows, 1):
            record = [
                row[k]
                for k in ("tenant", "seq", "timestamp", "subject", "action", "job_id", "previous")
            ]
            digest = hashlib.sha256(json.dumps(record, separators=(",", ":")).encode()).hexdigest()
            if row["seq"] != seq or row["previous"] != previous or row["digest"] != digest:
                raise ValueError("Audit integrity check failed")
            previous = digest
        return {"verified": True, "entries": [dict(r) for r in rows], "head": previous}

    def prune(self, principal: Principal) -> int:
        if principal.role != "admin":
            raise AccessDenied("Admin role required")
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            count = db.execute(
                "UPDATE jobs SET report=NULL WHERE tenant=? AND updated<? AND report IS NOT NULL AND status NOT IN ('queued','running')",
                (principal.tenant, time.time() - self.retention_days * 86400),
            ).rowcount
            self._audit(db, principal, "retention.pruned", None)
        return count

    def close(self):
        with self._lock:
            for signal in self._signals.values():
                signal.set()
        self._pool.shutdown(wait=True, cancel_futures=False)
        self._database_lock.close()
