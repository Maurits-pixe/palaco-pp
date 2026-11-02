"""Local PALACO Phone selection prototype. Python standard library only."""

import argparse
import getpass
from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import hashlib
from http.cookies import CookieError, SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import logging
import os
import smtplib
import ssl
import threading
from email.message import EmailMessage
from pathlib import Path
import re
from random import SystemRandom
import secrets
import sqlite3
import warnings
from uuid import uuid4
from urllib.parse import parse_qsl
from microsoft_mail import MicrosoftMailError, configured_mailer


ROOT = Path(__file__).resolve().parent
LOG = logging.getLogger("palaco")
COLORS = ("blue", "red", "green", "yellow")
SESSION_DAYS = 30
ADMIN_SESSION_HOURS = 8
PASSWORD_ITERATIONS = 600_000
LOGIN_FAILURE_LIMIT = 5
LOGIN_FAILURE_WINDOW_SECONDS = 15 * 60
MEMORY_ENTRY_LIMIT = 100
MEMORY_TITLE_MAX = 120
MEMORY_CONTENT_MAX = 5000
MEMORY_TAG_LIMIT = 8
MEMORY_TAG_MAX = 24
ADMIN_AUDIT_EVENTS = (
    "CONSUMER_CREATED", "ACCOUNT_CREATED", "ACCOUNT_LOGIN", "ACCOUNT_LOGOUT",
    "OPTIONS_OFFERED", "OPTION_OFFERED", "NUMBER_SELECTED", "NUMBER_REVOKED",
    "NUMBER_CONFLICT", "ERROR", "ADMIN_CREATED", "ADMIN_LOGIN", "ADMIN_LOGOUT",
    "ADMIN_NUMBER_REVOKED",
    "CONFIRMATION_MAIL_QUEUED", "CONFIRMATION_MAIL_SENT", "CONFIRMATION_MAIL_FAILED",
    "CONFIRMATION_MAIL_UNKNOWN",
)
USERNAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{2,31}$")
SCHEMA = """
PRAGMA journal_mode = WAL;
CREATE TABLE IF NOT EXISTS consumers (
    id TEXT PRIMARY KEY,
    token_hash TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS batches (
    id TEXT PRIMARY KEY,
    consumer_id TEXT NOT NULL UNIQUE REFERENCES consumers(id)
);
CREATE TABLE IF NOT EXISTS accounts (
    consumer_id TEXT PRIMARY KEY REFERENCES consumers(id),
    username TEXT NOT NULL UNIQUE,
    password_salt BLOB NOT NULL,
    password_hash BLOB NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS auth_sessions (
    token_hash TEXT PRIMARY KEY,
    consumer_id TEXT NOT NULL REFERENCES consumers(id),
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS auth_sessions_consumer_idx ON auth_sessions(consumer_id);
CREATE TABLE IF NOT EXISTS administrators (
    id TEXT PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password_salt BLOB NOT NULL,
    password_hash BLOB NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS admin_sessions (
    token_hash TEXT PRIMARY KEY,
    admin_id TEXT NOT NULL REFERENCES administrators(id),
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS auth_login_attempts (
    username_hash TEXT PRIMARY KEY,
    failures INTEGER NOT NULL CHECK(failures > 0),
    window_started_at TEXT NOT NULL,
    blocked_until TEXT
);
CREATE TABLE IF NOT EXISTS options (
    id TEXT PRIMARY KEY,
    batch_id TEXT NOT NULL REFERENCES batches(id),
    number TEXT NOT NULL UNIQUE
        CHECK(length(number) = 10 AND number NOT GLOB '*[^0-9]*'
              AND substr(number, 1, 1) != '0'),
    status TEXT NOT NULL CHECK(status IN ('OFFERED', 'ACTIVE', 'EXPIRED', 'REVOKED')),
    color TEXT NOT NULL CHECK(color IN ('blue', 'red', 'green', 'yellow')),
    offered_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS selections (
    consumer_id TEXT PRIMARY KEY REFERENCES consumers(id),
    option_id TEXT NOT NULL UNIQUE REFERENCES options(id),
    selected_at TEXT NOT NULL,
    revoked_at TEXT
);
CREATE TABLE IF NOT EXISTS confirmation_mail (
    consumer_id TEXT PRIMARY KEY REFERENCES selections(consumer_id),
    recipient TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('QUEUED','SENDING','SENT','FAILED','UNKNOWN')),
    attempts INTEGER NOT NULL DEFAULT 0,
    next_attempt_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    sent_at TEXT
);
CREATE TABLE IF NOT EXISTS memory_entries (
    id TEXT PRIMARY KEY,
    consumer_id TEXT NOT NULL REFERENCES consumers(id),
    title TEXT NOT NULL CHECK(length(title) BETWEEN 1 AND 120),
    content TEXT NOT NULL CHECK(length(content) BETWEEN 1 AND 5000),
    tags_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS memory_entries_consumer_updated_idx
    ON memory_entries(consumer_id,updated_at DESC,id);
CREATE TRIGGER IF NOT EXISTS memory_entries_limit BEFORE INSERT ON memory_entries
WHEN (SELECT count(*) FROM memory_entries WHERE consumer_id = NEW.consumer_id) >= 100
BEGIN SELECT RAISE(ABORT, 'MEMORY_ENTRY_LIMIT'); END;
CREATE TABLE IF NOT EXISTS audit (
    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    consumer_id TEXT,
    event TEXT NOT NULL,
    detail TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS audit_no_update BEFORE UPDATE ON audit
BEGIN SELECT RAISE(ABORT, 'AUDIT_APPEND_ONLY'); END;
CREATE TRIGGER IF NOT EXISTS audit_no_delete BEFORE DELETE ON audit
BEGIN SELECT RAISE(ABORT, 'AUDIT_APPEND_ONLY'); END;
CREATE TRIGGER IF NOT EXISTS batches_immutable_update BEFORE UPDATE ON batches
BEGIN SELECT RAISE(ABORT, 'BATCH_IMMUTABLE'); END;
CREATE TRIGGER IF NOT EXISTS batches_immutable_delete BEFORE DELETE ON batches
BEGIN SELECT RAISE(ABORT, 'BATCH_IMMUTABLE'); END;
CREATE TRIGGER IF NOT EXISTS options_immutable_identity BEFORE UPDATE ON options
WHEN NEW.id != OLD.id
  OR NEW.batch_id != OLD.batch_id
  OR NEW.number != OLD.number
  OR NEW.color != OLD.color
  OR NEW.offered_at != OLD.offered_at
BEGIN SELECT RAISE(ABORT, 'OPTION_IDENTITY_IMMUTABLE'); END;
CREATE TRIGGER IF NOT EXISTS options_valid_status_transition BEFORE UPDATE OF status ON options
WHEN NOT (
    (OLD.status = 'OFFERED' AND NEW.status IN ('ACTIVE', 'EXPIRED'))
    OR (OLD.status = 'ACTIVE' AND NEW.status = 'REVOKED')
)
BEGIN SELECT RAISE(ABORT, 'OPTION_STATUS_TRANSITION_INVALID'); END;
CREATE TRIGGER IF NOT EXISTS options_immutable_delete BEFORE DELETE ON options
BEGIN SELECT RAISE(ABORT, 'OPTION_IMMUTABLE'); END;
CREATE TRIGGER IF NOT EXISTS selections_validate_insert BEFORE INSERT ON selections
WHEN NOT EXISTS (
    SELECT 1 FROM options o
    JOIN batches b ON b.id = o.batch_id
    WHERE o.id = NEW.option_id
      AND b.consumer_id = NEW.consumer_id
      AND o.status = 'ACTIVE'
      AND NEW.revoked_at IS NULL
)
BEGIN SELECT RAISE(ABORT, 'SELECTION_OPTION_MISMATCH'); END;
CREATE TRIGGER IF NOT EXISTS selections_immutable_update BEFORE UPDATE ON selections
WHEN NEW.consumer_id != OLD.consumer_id
  OR NEW.option_id != OLD.option_id
  OR NEW.selected_at != OLD.selected_at
  OR OLD.revoked_at IS NOT NULL
  OR NEW.revoked_at IS NULL
  OR NOT EXISTS (
      SELECT 1 FROM options o
      WHERE o.id = NEW.option_id AND o.status = 'REVOKED'
  )
BEGIN SELECT RAISE(ABORT, 'SELECTION_TRANSITION_INVALID'); END;
CREATE TRIGGER IF NOT EXISTS selections_immutable_delete BEFORE DELETE ON selections
BEGIN SELECT RAISE(ABORT, 'SELECTION_IMMUTABLE'); END;
"""


def now():
    return datetime.now(timezone.utc).isoformat()


class PPError(Exception):
    def __init__(self, code, status=409):
        super().__init__(code)
        self.code = code
        self.status = status


class Store:
    def __init__(self, path):
        self.path = str(path)
        with self.connection() as db:
            db.executescript(SCHEMA)
        self.migrate_legacy_sessions()
        self.migrate_option_history()

    def migrate_legacy_sessions(self):
        expires_at = (datetime.now(timezone.utc).timestamp() + SESSION_DAYS * 86400)
        expiration = datetime.fromtimestamp(expires_at, timezone.utc).isoformat()
        with self.transaction() as db:
            db.execute(
                """INSERT OR IGNORE INTO auth_sessions(token_hash,consumer_id,created_at,expires_at)
                   SELECT token_hash,id,created_at,? FROM consumers""",
                (expiration,),
            )

    def migrate_option_history(self):
        with self.transaction() as db:
            existing_events = db.execute(
                "SELECT consumer_id,detail FROM audit WHERE event = 'OPTION_OFFERED'"
            ).fetchall()
            recorded = set()
            for event in existing_events:
                detail = json.loads(event["detail"])
                option_id = detail.get("optionId")
                if option_id:
                    recorded.add((event["consumer_id"], option_id))
            options = db.execute(
                """SELECT b.consumer_id,o.id,o.batch_id,o.number,o.color,o.offered_at
                   FROM options o JOIN batches b ON b.id = o.batch_id"""
            ).fetchall()
            for option in options:
                key = (option["consumer_id"], option["id"])
                if key in recorded:
                    continue
                detail = {
                    "batchId": option["batch_id"],
                    "optionId": option["id"],
                    "ppNumber": option["number"],
                    "color": option["color"],
                }
                db.execute(
                    """INSERT INTO audit(consumer_id,event,detail,created_at)
                       VALUES(?, 'OPTION_OFFERED', ?, ?)""",
                    (option["consumer_id"], json.dumps(detail), option["offered_at"]),
                )

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.path, timeout=15, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
        try:
            yield db
        finally:
            db.close()

    @contextmanager
    def transaction(self):
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                yield db
                db.commit()
            except Exception:
                db.rollback()
                raise

    @staticmethod
    def audit(db, consumer, event, detail=None):
        db.execute(
            "INSERT INTO audit(consumer_id,event,detail,created_at) VALUES(?,?,?,?)",
            (consumer, event, json.dumps(detail or {}), now()),
        )

    def record_error(self, consumer, code):
        with self.transaction() as db:
            self.audit(db, consumer, "ERROR", {"code": code})

    def identify(self, token):
        if not token:
            return None
        digest = hashlib.sha256(token.encode()).hexdigest()
        with self.connection() as db:
            row = db.execute(
                "SELECT consumer_id FROM auth_sessions WHERE token_hash = ? AND expires_at > ?",
                (digest, now()),
            ).fetchone()
            return row["consumer_id"] if row else None

    @staticmethod
    def hash_password(password, salt):
        try:
            encoded = password.encode("utf-8")
        except UnicodeEncodeError:
            raise PPError("PP_CREDENTIALS_INVALID", 400)
        return hashlib.pbkdf2_hmac("sha256", encoded, salt, PASSWORD_ITERATIONS)

    @staticmethod
    def normalize_username(username):
        if not isinstance(username, str):
            raise PPError("PP_REQUEST_INVALID", 400)
        normalized = username.strip().lower()
        if not USERNAME_PATTERN.fullmatch(normalized):
            raise PPError("PP_USERNAME_INVALID", 400)
        return normalized

    @staticmethod
    def validate_password(password):
        if not isinstance(password, str):
            raise PPError("PP_REQUEST_INVALID", 400)
        if not 12 <= len(password) <= 128:
            raise PPError("PP_PASSWORD_INVALID", 400)
        try:
            if len(password.encode("utf-8")) > 512:
                raise PPError("PP_PASSWORD_INVALID", 400)
        except UnicodeEncodeError:
            raise PPError("PP_PASSWORD_INVALID", 400)
        return password

    @staticmethod
    def issue_session(db, consumer, previous_token):
        token = secrets.token_urlsafe(32)
        created_at = now()
        expires_at = datetime.fromtimestamp(
            datetime.now(timezone.utc).timestamp() + SESSION_DAYS * 86400,
            timezone.utc,
        ).isoformat()
        if previous_token:
            old_hash = hashlib.sha256(previous_token.encode()).hexdigest()
            previous = db.execute(
                "SELECT consumer_id FROM auth_sessions WHERE token_hash = ?", (old_hash,)
            ).fetchone()
            db.execute("DELETE FROM auth_sessions WHERE token_hash = ?", (old_hash,))
            if previous and previous["consumer_id"] != consumer:
                db.execute(
                    "UPDATE consumers SET token_hash = ? WHERE id = ? AND token_hash = ?",
                    (
                        hashlib.sha256(secrets.token_bytes(32)).hexdigest(),
                        previous["consumer_id"],
                        old_hash,
                    ),
                )
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        db.execute("UPDATE consumers SET token_hash = ? WHERE id = ?", (token_hash, consumer))
        db.execute(
            "INSERT INTO auth_sessions VALUES(?,?,?,?)",
            (token_hash, consumer, created_at, expires_at),
        )
        return token

    def auth_state(self, consumer):
        if not consumer:
            return {"authenticated": False, "username": None}
        with self.connection() as db:
            row = db.execute(
                "SELECT username FROM accounts WHERE consumer_id = ?", (consumer,)
            ).fetchone()
        return {
            "authenticated": row is not None,
            "username": row["username"] if row else None,
        }

    def register_account(self, consumer, username, password, previous_token):
        normalized = self.normalize_username(username)
        password = self.validate_password(password)
        salt = secrets.token_bytes(16)
        password_hash = self.hash_password(password, salt)
        with self.transaction() as db:
            if db.execute(
                "SELECT 1 FROM accounts WHERE consumer_id = ?", (consumer,)
            ).fetchone():
                raise PPError("PP_ACCOUNT_EXISTS")
            if db.execute(
                "SELECT 1 FROM accounts WHERE username = ?", (normalized,)
            ).fetchone():
                raise PPError("PP_USERNAME_TAKEN")
            db.execute(
                "INSERT INTO accounts VALUES(?,?,?,?,?)",
                (consumer, normalized, salt, password_hash, now()),
            )
            session_token = self.issue_session(db, consumer, previous_token)
            self.audit(db, consumer, "ACCOUNT_CREATED", {"username": normalized})
        return normalized, session_token

    def login_account(self, username, password, previous_token, *, admin=False):
        normalized = self.normalize_username(username)
        password = self.validate_password(password)
        username_hash = hashlib.sha256(
            (f"admin:{normalized}" if admin else normalized).encode()
        ).hexdigest()
        table = "administrators" if admin else "accounts"
        identity_column = "id" if admin else "consumer_id"
        with self.connection() as db:
            attempt = db.execute(
                "SELECT blocked_until FROM auth_login_attempts WHERE username_hash = ?",
                (username_hash,),
            ).fetchone()
            if attempt and attempt["blocked_until"] and attempt["blocked_until"] > now():
                raise PPError("PP_LOGIN_RATE_LIMITED", 429)
            account = db.execute(
                f"SELECT {identity_column} AS identity,password_salt,password_hash "
                f"FROM {table} WHERE username = ?",
                (normalized,),
            ).fetchone()
        salt = account["password_salt"] if account else bytes(16)
        expected = account["password_hash"] if account else bytes(32)
        supplied = self.hash_password(password, salt)
        if not account or not secrets.compare_digest(supplied, expected):
            attempted_at = now()
            attempted_time = datetime.fromisoformat(attempted_at)
            window_start = (
                attempted_time - timedelta(seconds=LOGIN_FAILURE_WINDOW_SECONDS)
            ).isoformat()
            blocked_until = (
                attempted_time + timedelta(seconds=LOGIN_FAILURE_WINDOW_SECONDS)
            ).isoformat()
            with self.transaction() as db:
                db.execute(
                    "DELETE FROM auth_login_attempts WHERE window_started_at <= ?",
                    (window_start,),
                )
                previous = db.execute(
                    "SELECT failures,window_started_at FROM auth_login_attempts "
                    "WHERE username_hash = ?",
                    (username_hash,),
                ).fetchone()
                if previous and previous["window_started_at"] > window_start:
                    failures = previous["failures"] + 1
                    started_at = previous["window_started_at"]
                else:
                    failures = 1
                    started_at = attempted_at
                block_expiration = (
                    blocked_until if failures >= LOGIN_FAILURE_LIMIT else None
                )
                db.execute(
                    """INSERT INTO auth_login_attempts
                       (username_hash,failures,window_started_at,blocked_until)
                       VALUES(?,?,?,?)
                       ON CONFLICT(username_hash) DO UPDATE SET
                       failures=excluded.failures,
                       window_started_at=excluded.window_started_at,
                       blocked_until=excluded.blocked_until""",
                    (username_hash, failures, started_at, block_expiration),
                )
            if block_expiration:
                raise PPError("PP_LOGIN_RATE_LIMITED", 429)
            raise PPError("PP_CREDENTIALS_INVALID", 401)
        with self.transaction() as db:
            current = db.execute(
                f"SELECT {identity_column} AS identity FROM {table} WHERE username = ?",
                (normalized,),
            ).fetchone()
            if not current:
                raise PPError("PP_CREDENTIALS_INVALID", 401)
            consumer = current["identity"]
            db.execute(
                "DELETE FROM auth_login_attempts WHERE username_hash = ?",
                (username_hash,),
            )
            if admin:
                session_token = self.issue_admin_session(db, consumer, previous_token)
                self.audit(db, None, "ADMIN_LOGIN", {"adminId": consumer})
            else:
                session_token = self.issue_session(db, consumer, previous_token)
                self.audit(db, consumer, "ACCOUNT_LOGIN", {"username": normalized})
        return consumer, normalized, session_token

    def create_admin(self, username, password):
        normalized = self.normalize_username(username)
        password = self.validate_password(password)
        salt = secrets.token_bytes(16)
        password_hash = self.hash_password(password, salt)
        with self.transaction() as db:
            if db.execute(
                "SELECT 1 FROM administrators WHERE username = ?", (normalized,)
            ).fetchone():
                raise PPError("PP_USERNAME_TAKEN")
            admin_id = str(uuid4())
            db.execute(
                "INSERT INTO administrators VALUES(?,?,?,?,?)",
                (admin_id, normalized, salt, password_hash, now()),
            )
            self.audit(db, None, "ADMIN_CREATED", {"adminId": admin_id})
        return normalized

    @staticmethod
    def issue_admin_session(db, admin_id, previous_token):
        token = secrets.token_urlsafe(32)
        if previous_token:
            db.execute(
                "DELETE FROM admin_sessions WHERE token_hash = ?",
                (hashlib.sha256(previous_token.encode()).hexdigest(),),
            )
        db.execute("DELETE FROM admin_sessions WHERE expires_at <= ?", (now(),))
        db.execute(
            "INSERT INTO admin_sessions VALUES(?,?,?,?)",
            (
                hashlib.sha256(token.encode()).hexdigest(), admin_id, now(),
                (datetime.now(timezone.utc) + timedelta(hours=ADMIN_SESSION_HOURS)).isoformat(),
            ),
        )
        return token

    @staticmethod
    def require_admin(db, token):
        digest = hashlib.sha256((token or "").encode()).hexdigest()
        admin = db.execute(
            """SELECT a.id,a.username FROM administrators a JOIN admin_sessions s
               ON s.admin_id=a.id WHERE s.token_hash=? AND s.expires_at > ?""",
            (digest, now()),
        ).fetchone()
        if not admin:
            raise PPError("PP_ADMIN_REQUIRED", 401)
        return dict(admin)

    def admin_me(self, token):
        with self.connection() as db:
            return self.require_admin(db, token)

    def admin_logout(self, token):
        with self.transaction() as db:
            admin = self.require_admin(db, token)
            db.execute(
                "DELETE FROM admin_sessions WHERE token_hash=?",
                (hashlib.sha256(token.encode()).hexdigest(),),
            )
            self.audit(db, None, "ADMIN_LOGOUT", {"adminId": admin["id"]})
        return {"authenticated": False}

    def admin_overview(self, token, offset, *, search="", status=""):
        if (not isinstance(search, str) or len(search) > 120
                or status not in ("", "NEW", "OFFERED", "ACTIVE", "REVOKED", "UNKNOWN")):
            raise PPError("PP_REQUEST_INVALID", 400)
        search = search.strip().lower()
        selection = """WITH registry AS (
            SELECT c.id AS consumerId,a.username,c.created_at AS createdAt,
                   o.number AS ppNumber,
                   CASE WHEN s.revoked_at IS NOT NULL THEN 'REVOKED'
                        WHEN o.status='ACTIVE' THEN 'ACTIVE'
                        WHEN s.option_id IS NOT NULL THEN 'UNKNOWN'
                        WHEN b.id IS NOT NULL THEN 'OFFERED' ELSE 'NEW' END AS status
            FROM consumers c LEFT JOIN accounts a ON a.consumer_id=c.id
            LEFT JOIN batches b ON b.consumer_id=c.id
            LEFT JOIN selections s ON s.consumer_id=c.id
            LEFT JOIN options o ON o.id=s.option_id)
        """
        predicate = """ WHERE (? = '' OR status = ?)
            AND (? = '' OR instr(lower(coalesce(username,'')), ?) > 0
                 OR instr(lower(consumerId), ?) > 0
                 OR instr(coalesce(ppNumber,''), ?) > 0)"""
        parameters = (status, status, search, search, search, search)
        with self.connection() as db:
            db.execute("BEGIN")
            self.require_admin(db, token)
            counts = {
                "consumers": db.execute("SELECT count(*) FROM consumers").fetchone()[0],
                "accounts": db.execute("SELECT count(*) FROM accounts").fetchone()[0],
                "active": db.execute(
                    "SELECT count(*) FROM selections WHERE revoked_at IS NULL"
                ).fetchone()[0],
                "revoked": db.execute(
                    "SELECT count(*) FROM selections WHERE revoked_at IS NOT NULL"
                ).fetchone()[0],
            }
            total = db.execute(
                selection + "SELECT count(*) FROM registry" + predicate, parameters,
            ).fetchone()[0]
            rows = db.execute(
                selection + "SELECT * FROM registry" + predicate
                + " ORDER BY createdAt DESC,consumerId LIMIT 50 OFFSET ?",
                (*parameters, offset),
            ).fetchall()
            return {"counts": counts, "entries": [dict(row) for row in rows],
                    "total": total, "offset": offset, "limit": 50}

    def admin_audit(self, token, offset, *, search="", event="", status=""):
        if (not isinstance(search, str) or len(search) > 120
                or event not in ("", *ADMIN_AUDIT_EVENTS)
                or status not in ("", "OFFERED", "ACTIVE", "REVOKED")):
            raise PPError("PP_REQUEST_INVALID", 400)
        search = search.strip().lower()
        selection = """WITH projected AS (
            SELECT sequence,consumer_id AS consumerId,event,created_at AS createdAt,
                   CASE WHEN event IN ('ADMIN_CREATED','ADMIN_LOGIN','ADMIN_LOGOUT',
                                       'ADMIN_NUMBER_REVOKED')
                        THEN json_extract(detail,'$.adminId') END AS adminId,
                   CASE WHEN event='ADMIN_NUMBER_REVOKED'
                        THEN json_extract(detail,'$.reason') END AS reason,
                   CASE WHEN event IN ('OPTION_OFFERED','OPTIONS_OFFERED') THEN 'OFFERED'
                        WHEN event='NUMBER_SELECTED' THEN 'ACTIVE'
                        WHEN event IN ('NUMBER_REVOKED','ADMIN_NUMBER_REVOKED')
                             THEN 'REVOKED' ELSE '' END AS status
            FROM audit WHERE event NOT LIKE 'MEMORY_%'
        ), visible AS (
            SELECT p.*,a.username AS adminUsername,c.username AS username
            FROM projected p LEFT JOIN administrators a ON a.id=p.adminId
            LEFT JOIN accounts c ON c.consumer_id=p.consumerId
        ) """
        predicate = """ WHERE (?='' OR event=?) AND (?='' OR status=?)
            AND (?='' OR instr(lower(event),?)>0
                 OR instr(lower(coalesce(consumerId,'')),?)>0
                 OR instr(lower(coalesce(username,'')),?)>0
                 OR instr(lower(coalesce(adminId,'')),?)>0
                 OR instr(lower(coalesce(adminUsername,'')),?)>0
                 OR instr(lower(coalesce(reason,'')),?)>0
                 OR instr(cast(sequence AS TEXT),?)>0)"""
        parameters = (event, event, status, status, *([search] * 8))
        with self.connection() as db:
            db.execute("BEGIN")
            self.require_admin(db, token)
            admin_events = db.execute(
                """SELECT event,detail FROM audit WHERE event IN
                   ('ADMIN_CREATED','ADMIN_LOGIN','ADMIN_LOGOUT','ADMIN_NUMBER_REVOKED')"""
            ).fetchall()
            for row in admin_events:
                try:
                    detail = json.loads(row["detail"])
                except (ValueError, TypeError) as error:
                    raise PPError("PP_AUDIT_UNKNOWN", 503) from error
                if (not isinstance(detail, dict)
                        or not isinstance(detail.get("adminId"), str)
                        or not detail["adminId"]
                        or (row["event"] == "ADMIN_NUMBER_REVOKED" and (
                            not isinstance(detail.get("reason"), str)
                            or not 5 <= len(detail["reason"].strip()) <= 240
                        ))):
                    raise PPError("PP_AUDIT_UNKNOWN", 503)
            total = db.execute(
                selection + "SELECT count(*) FROM visible" + predicate, parameters,
            ).fetchone()[0]
            rows = db.execute(
                selection + "SELECT * FROM visible" + predicate
                + " ORDER BY sequence DESC LIMIT 50 OFFSET ?", (*parameters, offset),
            ).fetchall()
            return {"entries": [dict(row) for row in rows], "total": total,
                    "offset": offset, "limit": 50}

    def logout(self, consumer, token):
        token_hash = hashlib.sha256(token.encode()).hexdigest() if token else None
        with self.transaction() as db:
            if token_hash:
                db.execute(
                    "UPDATE consumers SET token_hash = ? WHERE id = ? AND token_hash = ?",
                    (
                        hashlib.sha256(secrets.token_bytes(32)).hexdigest(),
                        consumer,
                        token_hash,
                    ),
                )
                db.execute("DELETE FROM auth_sessions WHERE token_hash = ?", (token_hash,))
            self.audit(db, consumer, "ACCOUNT_LOGOUT")

    def create_consumer(self):
        token = secrets.token_urlsafe(32)
        consumer = str(uuid4())
        with self.transaction() as db:
            created_at = now()
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            db.execute(
                "INSERT INTO consumers VALUES(?,?,?)",
                (consumer, token_hash, created_at),
            )
            expiration = datetime.fromtimestamp(
                datetime.now(timezone.utc).timestamp() + SESSION_DAYS * 86400,
                timezone.utc,
            ).isoformat()
            db.execute(
                "INSERT INTO auth_sessions VALUES(?,?,?,?)",
                (token_hash, consumer, created_at, expiration),
            )
            self.audit(db, consumer, "CONSUMER_CREATED")
        return consumer, token

    def options(self, consumer):
        with self.transaction() as db:
            if db.execute(
                "SELECT 1 FROM selections WHERE consumer_id = ?", (consumer,)
            ).fetchone():
                raise PPError("PP_ALREADY_SELECTED")
            batch = db.execute(
                "SELECT id FROM batches WHERE consumer_id = ?", (consumer,)
            ).fetchone()
            if batch:
                batch_id = batch["id"]
            else:
                batch_id = str(uuid4())
                db.execute("INSERT INTO batches VALUES(?,?)", (batch_id, consumer))
                colors = list(COLORS) + [secrets.choice(COLORS) for _ in range(6)]
                SystemRandom().shuffle(colors)
                for color in colors:
                    # Bound retries so even a broken generator cannot hang a request.
                    for attempt in range(100):
                        number = str(1_000_000_000 + secrets.randbelow(9_000_000_000))
                        if db.execute(
                            "SELECT 1 FROM options WHERE number = ?", (number,)
                        ).fetchone():
                            self.audit(db, consumer, "NUMBER_CONFLICT")
                            continue
                        option_id = str(uuid4())
                        offered_at = now()
                        db.execute(
                            "INSERT INTO options VALUES(?,?,?,?,?,?)",
                            (option_id, batch_id, number, "OFFERED", color, offered_at),
                        )
                        self.audit(
                            db,
                            consumer,
                            "OPTION_OFFERED",
                            {
                                "batchId": batch_id,
                                "optionId": option_id,
                                "ppNumber": number,
                                "color": color,
                            },
                        )
                        break
                    else:
                        raise PPError("PP_NUMBER_CONFLICT", 503)
                self.audit(db, consumer, "OPTIONS_OFFERED", {"batchId": batch_id})
            rows = db.execute(
                "SELECT id,number,status,color FROM options WHERE batch_id = ? ORDER BY rowid",
                (batch_id,),
            ).fetchall()
            if len(rows) != 10 or any(row["status"] != "OFFERED" for row in rows):
                raise PPError("PP_SELECTION_UNKNOWN", 503)
            return {"batchId": batch_id, "options": [dict(row) for row in rows]}

    @staticmethod
    def validate_email(email):
        if not isinstance(email, str):
            raise PPError("PP_EMAIL_INVALID", 400)
        email = email.strip()
        if not email:
            return ""
        if (len(email) > 254 or not email.isascii()
                or not re.fullmatch(
                    r"[A-Za-z0-9!#$%&'*+/=?^_`{|}~.-]+@"
                    r"[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?"
                    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)+", email
                )):
            raise PPError("PP_EMAIL_INVALID", 400)
        local, domain = email.rsplit("@", 1)
        if (len(local) > 64 or local.startswith(".") or local.endswith(".")
                or ".." in local or any(len(label) > 63 for label in domain.split("."))):
            raise PPError("PP_EMAIL_INVALID", 400)
        return email

    def mail_status(self, consumer):
        with self.connection() as db:
            row = db.execute(
                "SELECT status,attempts,sent_at AS sentAt FROM confirmation_mail WHERE consumer_id=?",
                (consumer,),
            ).fetchone()
        return dict(row) if row else {"status": "NOT_REQUESTED"}

    def select(self, consumer, option_id, *, email=""):
        email = self.validate_email(email)
        with self.transaction() as db:
            if db.execute(
                "SELECT 1 FROM selections WHERE consumer_id = ?", (consumer,)
            ).fetchone():
                raise PPError("PP_ALREADY_SELECTED")
            option = db.execute(
                """SELECT o.*, b.consumer_id FROM options o
                   JOIN batches b ON b.id = o.batch_id WHERE o.id = ?""",
                (option_id,),
            ).fetchone()
            # Do not disclose whether an option belongs to another consumer.
            if not option or option["consumer_id"] != consumer:
                raise PPError("PP_OPTION_INVALID", 404)
            if option["status"] != "OFFERED":
                raise PPError("PP_OPTION_INVALID")
            selected_at = now()
            db.execute(
                """UPDATE options SET status = CASE WHEN id = ? THEN 'ACTIVE'
                   ELSE 'EXPIRED' END WHERE batch_id = ?""",
                (option_id, option["batch_id"]),
            )
            db.execute(
                "INSERT INTO selections VALUES(?,?,?,NULL)",
                (consumer, option_id, selected_at),
            )
            self.audit(
                db,
                consumer,
                "NUMBER_SELECTED",
                {
                    "batchId": option["batch_id"],
                    "optionId": option_id,
                    "ppNumber": option["number"],
                    "color": option["color"],
                },
            )
            if email:
                db.execute(
                    """INSERT INTO confirmation_mail
                       (consumer_id,recipient,status,next_attempt_at,created_at)
                       VALUES(?,?,'QUEUED',?,?)""", (consumer, email, selected_at, selected_at),
                )
                self.audit(db, consumer, "CONFIRMATION_MAIL_QUEUED")
            return {
                "consumerId": consumer,
                "ppNumberId": option_id,
                "ppNumber": option["number"],
                "status": "ACTIVE",
                "selectedAt": selected_at,
            }

    def me(self, consumer):
        with self.connection() as db:
            row = db.execute(
                """SELECT s.option_id, s.selected_at, s.revoked_at, o.number, o.status
                   FROM selections s JOIN options o ON o.id = s.option_id
                   WHERE s.consumer_id = ?""",
                (consumer,),
            ).fetchone()
            if row:
                expected = "REVOKED" if row["revoked_at"] else "ACTIVE"
                if row["status"] != expected:
                    raise PPError("PP_SELECTION_UNKNOWN", 503)
                return {
                    "consumerId": consumer,
                    "status": expected,
                    "ppNumber": row["number"],
                    "ppNumberId": row["option_id"],
                    "selectedAt": row["selected_at"],
                    "revokedAt": row["revoked_at"],
                }
            batch = db.execute(
                "SELECT 1 FROM batches WHERE consumer_id = ?", (consumer,)
            ).fetchone()
            return {"consumerId": consumer, "status": "OFFERED" if batch else "NEW"}

    def history(self, consumer):
        with self.connection() as db:
            rows = db.execute(
                """SELECT sequence,event,detail,created_at FROM audit
                   WHERE consumer_id = ? AND event IN
                   ('OPTION_OFFERED','NUMBER_SELECTED','NUMBER_REVOKED')
                   ORDER BY created_at ASC,sequence ASC LIMIT 100""",
                (consumer,),
            ).fetchall()
            option_rows = db.execute(
                """SELECT o.id,o.number,o.color,o.batch_id FROM options o
                   JOIN batches b ON b.id = o.batch_id WHERE b.consumer_id = ?""",
                (consumer,),
            ).fetchall()
        options_by_id = {row["id"]: dict(row) for row in option_rows}
        events = []
        for row in rows:
            try:
                detail = json.loads(row["detail"])
            except (TypeError, ValueError) as error:
                raise PPError("PP_SELECTION_UNKNOWN", 503) from error
            if not isinstance(detail, dict):
                raise PPError("PP_SELECTION_UNKNOWN", 503)
            option = options_by_id.get(detail.get("optionId"))
            if option:
                detail.setdefault("ppNumber", option["number"])
                detail.setdefault("color", option["color"])
                detail.setdefault("batchId", option["batch_id"])
            events.append(
                {
                    "sequence": row["sequence"],
                    "event": row["event"],
                    "detail": detail,
                    "createdAt": row["created_at"],
                }
            )
        return events

    @staticmethod
    def validate_memory_fields(title, content, tags):
        if not isinstance(title, str) or not isinstance(content, str):
            raise PPError("PP_MEMORY_INVALID", 400)
        title = title.strip()
        content = content.strip()
        if not title or len(title) > MEMORY_TITLE_MAX or not content or len(content) > MEMORY_CONTENT_MAX:
            raise PPError("PP_MEMORY_INVALID", 400)
        try:
            if len(title.encode("utf-8")) > MEMORY_TITLE_MAX * 4:
                raise PPError("PP_MEMORY_INVALID", 400)
            if len(content.encode("utf-8")) > MEMORY_CONTENT_MAX * 4:
                raise PPError("PP_MEMORY_INVALID", 400)
        except UnicodeEncodeError as error:
            raise PPError("PP_MEMORY_INVALID", 400) from error
        if any(ord(char) < 32 and char not in "\n\t\r" for char in title + content):
            raise PPError("PP_MEMORY_INVALID", 400)
        if not isinstance(tags, list) or len(tags) > MEMORY_TAG_LIMIT:
            raise PPError("PP_MEMORY_INVALID", 400)
        normalized_tags = []
        seen = set()
        for tag in tags:
            if not isinstance(tag, str):
                raise PPError("PP_MEMORY_INVALID", 400)
            normalized = tag.strip()
            if not normalized or len(normalized) > MEMORY_TAG_MAX:
                raise PPError("PP_MEMORY_INVALID", 400)
            if any(ord(char) < 32 for char in normalized):
                raise PPError("PP_MEMORY_INVALID", 400)
            key = normalized.casefold()
            if key not in seen:
                normalized_tags.append(normalized)
                seen.add(key)
        return title, content, normalized_tags

    def list_memory(self, consumer):
        with self.connection() as db:
            rows = db.execute(
                """SELECT id,title,content,tags_json,created_at,updated_at
                   FROM memory_entries WHERE consumer_id = ?
                   ORDER BY updated_at DESC,id LIMIT ?""",
                (consumer, MEMORY_ENTRY_LIMIT),
            ).fetchall()
        entries = []
        for row in rows:
            try:
                tags = json.loads(row["tags_json"])
            except (TypeError, ValueError) as error:
                raise PPError("PP_MEMORY_UNKNOWN", 503) from error
            if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
                raise PPError("PP_MEMORY_UNKNOWN", 503)
            entries.append(
                {
                    "id": row["id"],
                    "title": row["title"],
                    "content": row["content"],
                    "tags": tags,
                    "createdAt": row["created_at"],
                    "updatedAt": row["updated_at"],
                }
            )
        return {"entries": entries, "limit": MEMORY_ENTRY_LIMIT}

    def save_memory(self, consumer, entry_id, title, content, tags):
        title, content, tags = self.validate_memory_fields(title, content, tags)
        saved_at = now()
        tags_json = json.dumps(tags, ensure_ascii=False)
        with self.transaction() as db:
            if entry_id is None:
                count = db.execute(
                    "SELECT count(*) FROM memory_entries WHERE consumer_id = ?",
                    (consumer,),
                ).fetchone()[0]
                if count >= MEMORY_ENTRY_LIMIT:
                    raise PPError("PP_MEMORY_LIMIT", 409)
                entry_id = str(uuid4())
                db.execute(
                    """INSERT INTO memory_entries
                       (id,consumer_id,title,content,tags_json,created_at,updated_at)
                       VALUES(?,?,?,?,?,?,?)""",
                    (entry_id, consumer, title, content, tags_json, saved_at, saved_at),
                )
                event = "MEMORY_CREATED"
            else:
                if not isinstance(entry_id, str) or not 1 <= len(entry_id) <= 64:
                    raise PPError("PP_MEMORY_INVALID", 400)
                changed = db.execute(
                    """UPDATE memory_entries SET title = ?,content = ?,tags_json = ?,updated_at = ?
                       WHERE id = ? AND consumer_id = ?""",
                    (title, content, tags_json, saved_at, entry_id, consumer),
                ).rowcount
                if changed != 1:
                    raise PPError("PP_MEMORY_UNKNOWN", 404)
                event = "MEMORY_UPDATED"
            self.audit(db, consumer, event, {"memoryId": entry_id})
            row = db.execute(
                """SELECT id,title,content,tags_json,created_at,updated_at
                   FROM memory_entries WHERE id = ? AND consumer_id = ?""",
                (entry_id, consumer),
            ).fetchone()
        return {
            "id": row["id"],
            "title": row["title"],
            "content": row["content"],
            "tags": json.loads(row["tags_json"]),
            "createdAt": row["created_at"],
            "updatedAt": row["updated_at"],
        }

    def delete_memory(self, consumer, entry_id):
        if not isinstance(entry_id, str) or not 1 <= len(entry_id) <= 64:
            raise PPError("PP_MEMORY_INVALID", 400)
        with self.transaction() as db:
            changed = db.execute(
                "DELETE FROM memory_entries WHERE id = ? AND consumer_id = ?",
                (entry_id, consumer),
            ).rowcount
            if changed != 1:
                raise PPError("PP_MEMORY_UNKNOWN", 404)
            self.audit(db, consumer, "MEMORY_DELETED", {"memoryId": entry_id})
        return {"deleted": True, "id": entry_id}

    def verify_integrity(self):
        issues = []
        checks = []
        with self.connection() as db:
            db.execute("BEGIN")
            integrity = db.execute("PRAGMA integrity_check").fetchall()
            if len(integrity) != 1 or integrity[0][0] != "ok":
                issues.append("SQLITE_INTEGRITY_CHECK_FAILED")
            else:
                checks.append("SQLITE_INTEGRITY_OK")

            foreign_keys = db.execute("PRAGMA foreign_key_check").fetchall()
            if foreign_keys:
                issues.append("FOREIGN_KEY_CHECK_FAILED")
            else:
                checks.append("FOREIGN_KEYS_OK")

            invalid_batches = db.execute(
                """SELECT count(*) FROM (
                     SELECT b.id,count(o.id) AS option_count,count(DISTINCT o.color) AS color_count
                     FROM batches b LEFT JOIN options o ON o.batch_id = b.id
                     GROUP BY b.id
                     HAVING option_count != 10 OR color_count != 4
                   )"""
            ).fetchone()[0]
            if invalid_batches:
                issues.append("BATCH_SHAPE_INVALID")
            else:
                checks.append("BATCH_SHAPE_OK")

            invalid_lifecycles = db.execute(
                """SELECT count(*) FROM batches b
                   LEFT JOIN selections s ON s.consumer_id = b.consumer_id
                   LEFT JOIN options selected ON selected.id = s.option_id
                   WHERE (
                     s.consumer_id IS NULL AND (
                       SELECT count(*) FROM options o
                       WHERE o.batch_id = b.id AND o.status = 'OFFERED'
                     ) != 10
                   ) OR (
                     s.consumer_id IS NOT NULL AND (
                       selected.batch_id != b.id
                       OR selected.status != CASE
                            WHEN s.revoked_at IS NULL THEN 'ACTIVE'
                            ELSE 'REVOKED'
                          END
                       OR (SELECT count(*) FROM options o
                           WHERE o.batch_id = b.id AND o.status IN ('ACTIVE','REVOKED')) != 1
                       OR (SELECT count(*) FROM options o
                           WHERE o.batch_id = b.id AND o.status = 'EXPIRED') != 9
                     )
                   )"""
            ).fetchone()[0]
            if invalid_lifecycles:
                issues.append("SELECTION_LIFECYCLE_INVALID")
            else:
                checks.append("SELECTION_LIFECYCLES_OK")

            lifecycle_audits = db.execute(
                """SELECT consumer_id,event,detail FROM audit
                   WHERE event IN ('OPTION_OFFERED','NUMBER_SELECTED','NUMBER_REVOKED')"""
            ).fetchall()
            audited = {
                "OPTION_OFFERED": [],
                "NUMBER_SELECTED": [],
                "NUMBER_REVOKED": [],
            }
            invalid_audit_details = False
            for event in lifecycle_audits:
                try:
                    detail = json.loads(event["detail"])
                except (TypeError, ValueError):
                    invalid_audit_details = True
                    continue
                option_id = detail.get("optionId") if isinstance(detail, dict) else None
                if not isinstance(option_id, str):
                    invalid_audit_details = True
                    continue
                audited[event["event"]].append((event["consumer_id"], option_id))
            if invalid_audit_details:
                issues.append("AUDIT_DETAIL_INVALID")
            else:
                checks.append("AUDIT_DETAIL_VALID")

            option_owners = {
                (row["consumer_id"], row["id"])
                for row in db.execute(
                    """SELECT b.consumer_id,o.id FROM options o
                       JOIN batches b ON b.id = o.batch_id"""
                ).fetchall()
            }
            selections = db.execute(
                "SELECT consumer_id,option_id,revoked_at FROM selections"
            ).fetchall()
            selected_owners = {
                (selection["consumer_id"], selection["option_id"])
                for selection in selections
            }
            revoked_owners = {
                (selection["consumer_id"], selection["option_id"])
                for selection in selections
                if selection["revoked_at"] is not None
            }
            expected_audits = {
                "OPTION_OFFERED": option_owners,
                "NUMBER_SELECTED": selected_owners,
                "NUMBER_REVOKED": revoked_owners,
            }
            audit_codes = {
                "OPTION_OFFERED": "OFFER_AUDIT_INCOMPLETE",
                "NUMBER_SELECTED": "SELECTION_AUDIT_INCOMPLETE",
                "NUMBER_REVOKED": "REVOCATION_AUDIT_INCOMPLETE",
            }
            audit_check_names = {
                "OPTION_OFFERED": "OFFER_AUDIT_COMPLETE",
                "NUMBER_SELECTED": "SELECTION_AUDIT_COMPLETE",
                "NUMBER_REVOKED": "REVOCATION_AUDIT_COMPLETE",
            }
            for event_type, expected in expected_audits.items():
                actual_list = audited[event_type]
                actual = set(actual_list)
                if invalid_audit_details:
                    continue
                if actual != expected or any(
                    count > 1 for count in Counter(actual_list).values()
                ):
                    issues.append(audit_codes[event_type])
                else:
                    checks.append(audit_check_names[event_type])

            if not invalid_audit_details:
                checks.append("LIFECYCLE_AUDIT_INTEGRITY_OK")

            memory_audits = db.execute(
                """SELECT detail FROM audit WHERE event IN
                   ('MEMORY_CREATED','MEMORY_UPDATED','MEMORY_DELETED')"""
            ).fetchall()
            invalid_memory_audits = False
            for event in memory_audits:
                try:
                    detail = json.loads(event["detail"])
                except (TypeError, ValueError):
                    invalid_memory_audits = True
                    break
                if (
                    not isinstance(detail, dict)
                    or set(detail) != {"memoryId"}
                    or not isinstance(detail["memoryId"], str)
                ):
                    invalid_memory_audits = True
                    break
            if invalid_memory_audits:
                issues.append("MEMORY_AUDIT_DETAIL_INVALID")
            else:
                checks.append("MEMORY_AUDIT_CONTENT_EXCLUDED")

            counts = {
                "consumers": db.execute("SELECT count(*) FROM consumers").fetchone()[0],
                "batches": db.execute("SELECT count(*) FROM batches").fetchone()[0],
                "options": db.execute("SELECT count(*) FROM options").fetchone()[0],
                "selections": db.execute("SELECT count(*) FROM selections").fetchone()[0],
                "memoryEntries": db.execute("SELECT count(*) FROM memory_entries").fetchone()[0],
            }
            db.commit()
        return {"ok": not issues, "checks": checks, "issues": issues, "counts": counts}

    def revoke(self, consumer, *, admin_token=None, reason=None):
        with self.transaction() as db:
            admin = None
            if admin_token is not None:
                admin = self.require_admin(db, admin_token)
                if not isinstance(reason, str) or not 5 <= len(reason.strip()) <= 240:
                    raise PPError("PP_ADMIN_REASON_INVALID", 400)
            selection = db.execute(
                """SELECT s.*,o.number,o.color,o.batch_id FROM selections s
                   JOIN options o ON o.id = s.option_id WHERE s.consumer_id = ?""",
                (consumer,),
            ).fetchone()
            if not selection:
                raise PPError("PP_OPTION_INVALID", 404)
            if selection["revoked_at"]:
                raise PPError("PP_SELECTION_REVOKED")
            changed = db.execute(
                "UPDATE options SET status = 'REVOKED' WHERE id = ? AND status = 'ACTIVE'",
                (selection["option_id"],),
            ).rowcount
            if changed != 1:
                raise PPError("PP_SELECTION_UNKNOWN", 503)
            revoked_at = now()
            db.execute(
                "UPDATE selections SET revoked_at = ? WHERE consumer_id = ?",
                (revoked_at, consumer),
            )
            self.audit(
                db,
                consumer,
                "NUMBER_REVOKED",
                {
                    "batchId": selection["batch_id"],
                    "optionId": selection["option_id"],
                    "ppNumber": selection["number"],
                    "color": selection["color"],
                },
            )
            if admin:
                self.audit(db, consumer, "ADMIN_NUMBER_REVOKED",
                           {"adminId": admin["id"], "reason": reason.strip()})
            return {"status": "REVOKED", "revokedAt": revoked_at}


def smtp_configuration():
    names = ("PP_SMTP_HOST", "PP_SMTP_PORT", "PP_SMTP_FROM", "PP_SMTP_USER",
             "PP_SMTP_PASSWORD", "PP_SMTP_TLS", "PP_SMTP_AUTH", "PP_MICROSOFT_CLIENT_ID")
    if not any(os.environ.get(name) for name in names):
        return None
    auth = os.environ.get("PP_SMTP_AUTH", "password")
    if auth not in ("password", "microsoft"):
        raise ValueError("PP_SMTP_AUTH moet password of microsoft zijn")
    host = os.environ.get(
        "PP_SMTP_HOST", "smtp-mail.outlook.com" if auth == "microsoft" else ""
    ).strip()
    sender = Store.validate_email(os.environ.get("PP_SMTP_FROM", ""))
    mode = os.environ.get("PP_SMTP_TLS", "starttls")
    user = os.environ.get("PP_SMTP_USER", "")
    password = os.environ.get("PP_SMTP_PASSWORD", "")
    try:
        port = int(os.environ.get("PP_SMTP_PORT", "465" if mode == "ssl" else "587"))
    except ValueError as error:
        raise ValueError("PP_SMTP_PORT moet een geldig poortnummer zijn") from error
    if (not host or not sender or not 1 <= port <= 65535
            or mode not in ("starttls", "ssl")
            or (auth == "password" and bool(user) != bool(password))):
        raise ValueError("Onvolledige SMTP-configuratie; controleer PP_SMTP_*")
    result = {"host": host, "port": port, "sender": sender, "mode": mode,
              "user": user, "password": password}
    if auth == "microsoft":
        if (host != "smtp-mail.outlook.com" or port != 587 or mode != "starttls"
                or password or (user and user.casefold() != sender.casefold())):
            raise ValueError("Microsoft vereist smtp-mail.outlook.com:587, STARTTLS en geen SMTP-wachtwoord")
        result["microsoft"] = configured_mailer(sender)
        result["microsoft"].access_token()
    return result


def deliver_confirmation(config, job):
    microsoft = config.get("microsoft")
    token = microsoft.access_token() if microsoft else None
    message = EmailMessage()
    message["From"] = config["sender"]
    message["To"] = job["recipient"]
    message["Subject"] = "Bevestiging van je PALACO P.P.-keuze"
    domain = config["sender"].rsplit("@", 1)[1]
    message["Message-ID"] = f"<pp-{job['consumer_id']}@{domain}>"
    message.set_content(
        f"Je hebt op {job['created_at']} definitief gekozen voor P.P.-nummer "
        f"{job['number']}.\n\nDe overige negen opties zijn vervallen. "
        "Deze bevestiging beschrijft de keuze op dat moment; het nummer kan later "
        "zijn ingetrokken.\n\nDit is lokale PALACO-identificatie, geen telefoonlijn, "
        "telecomactivatie of officieel PALACO-ID.\n"
    )
    context = ssl.create_default_context()
    factory = smtplib.SMTP_SSL if config["mode"] == "ssl" else smtplib.SMTP
    options = {"timeout": 20}
    if config["mode"] == "ssl":
        options["context"] = context
    with factory(config["host"], config["port"], **options) as smtp:
        if config["mode"] == "starttls":
            smtp.starttls(context=context)
        if microsoft:
            smtp.auth("XOAUTH2", lambda challenge=None: (
                f"user={config['sender']}\x01auth=Bearer {token}\x01\x01"
                if challenge is None else ""
            ))
        elif config["user"]:
            smtp.login(config["user"], config["password"])
        refused = smtp.send_message(message)
        if refused:
            raise smtplib.SMTPRecipientsRefused(refused)


def process_confirmation(store, config):
    with store.transaction() as db:
        row = db.execute(
            """SELECT m.*,o.number FROM confirmation_mail m
               JOIN selections s ON s.consumer_id=m.consumer_id
               JOIN options o ON o.id=s.option_id
               WHERE m.status='QUEUED' AND m.next_attempt_at <= ?
               ORDER BY m.created_at LIMIT 1""", (now(),),
        ).fetchone()
        if not row:
            return False
        job = dict(row)
        db.execute(
            "UPDATE confirmation_mail SET status='SENDING',attempts=attempts+1 WHERE consumer_id=?",
            (job["consumer_id"],),
        )
    state = "SENT"
    try:
        deliver_confirmation(config, job)
    except MicrosoftMailError:
        state = "FAILED"
        LOG.error("Microsoft mail authorization unavailable; run --microsoft-login locally")
    except smtplib.SMTPServerDisconnected:
        # The remote server may have accepted DATA before the connection failed.
        state = "UNKNOWN"
        LOG.error("Confirmation SMTP outcome unknown; automatic retry blocked")
    except smtplib.SMTPException:
        state = "FAILED" if job["attempts"] >= 2 else "QUEUED"
        LOG.error("Confirmation SMTP request failed; state=%s", state)
    except OSError:
        state = "UNKNOWN"
        LOG.error("Confirmation transport outcome unknown; automatic retry blocked")
    with store.transaction() as db:
        db.execute(
            """UPDATE confirmation_mail SET status=?,sent_at=?,next_attempt_at=?
               WHERE consumer_id=?""",
            (state, now() if state == "SENT" else None,
             (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
             job["consumer_id"]),
        )
        store.audit(db, job["consumer_id"], f"CONFIRMATION_MAIL_{state}")
    return True


def confirmation_worker(store, config, stop):
    try:
        with store.transaction() as db:
            interrupted = db.execute(
                "SELECT consumer_id FROM confirmation_mail WHERE status='SENDING'"
            ).fetchall()
            for row in interrupted:
                db.execute(
                    "UPDATE confirmation_mail SET status='UNKNOWN' WHERE consumer_id=?",
                    (row["consumer_id"],),
                )
                store.audit(db, row["consumer_id"], "CONFIRMATION_MAIL_UNKNOWN")
        while not stop.is_set():
            process_confirmation(store, config)
            stop.wait(2)
    except sqlite3.Error:
        LOG.exception("Confirmation worker stopped due to database failure; pending mail retained")


class Server(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, store, mail_config=None):
        super().__init__(address, Handler)
        self.store = store
        self.mail_config = mail_config


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        LOG.info(fmt, *args)

    def respond(self, status, body, content_type="application/json", cookie=None):
        if content_type == "application/json":
            body = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "img-src 'self'; connect-src 'self'; frame-ancestors 'none'; "
            "base-uri 'none'; form-action 'self'",
        )
        if cookie:
            self.send_header("Set-Cookie", cookie)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self.dispatch("GET")

    def do_POST(self):
        self.dispatch("POST")

    @staticmethod
    def session_cookie(value):
        return (
            f"pp_session={value}; HttpOnly; SameSite=Strict; "
            f"Path=/; Max-Age={SESSION_DAYS * 86400}"
        )

    @staticmethod
    def admin_cookie(value, *, clear=False):
        return (
            f"pp_admin={value}; HttpOnly; SameSite=Strict; Path=/api/admin; "
            f"Max-Age={0 if clear else ADMIN_SESSION_HOURS * 3600}"
        )

    def dispatch(self, method):
        consumer = None
        try:
            host = f"127.0.0.1:{self.server.server_port}"
            if self.headers.get("Host") != host:
                raise PPError("PP_HOST_DENIED", 403)
            if method == "POST" and self.headers.get("Origin") != f"http://{host}":
                raise PPError("PP_ORIGIN_DENIED", 403)
            if method == "GET" and self.path in (
                "/", "/app.js", "/style.css", "/admin", "/admin.js", "/admin.css", "/offline.html", "/offline.js", "/offline.css", "/sw.js"
            ):
                name, mime = {
                    "/": ("index.html", "text/html; charset=utf-8"),
                    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
                    "/style.css": ("style.css", "text/css; charset=utf-8"),
                    "/admin": ("admin.html", "text/html; charset=utf-8"),
                    "/admin.js": ("admin.js", "text/javascript; charset=utf-8"),
                    "/admin.css": ("admin.css", "text/css; charset=utf-8"),
                    "/offline.html": ("offline.html", "text/html; charset=utf-8"),
                    "/offline.js": ("offline.js", "text/javascript; charset=utf-8"),
                    "/offline.css": ("offline.css", "text/css; charset=utf-8"),
                    "/sw.js": ("sw.js", "text/javascript; charset=utf-8"),
                }[self.path]
                self.respond(200, (ROOT / "static" / name).read_bytes(), mime)
                return
            cookies = SimpleCookie()
            try:
                cookies.load(self.headers.get("Cookie", ""))
            except CookieError:
                raise PPError("PP_SESSION_REQUIRED", 401)
            token = cookies.get("pp_session")
            session_token = token.value if token else None
            consumer = self.server.store.identify(session_token)
            data = {}
            if method == "POST":
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                except ValueError:
                    raise PPError("PP_REQUEST_INVALID", 400)
                if not 0 <= length <= 32768 or self.headers.get("Transfer-Encoding"):
                    raise PPError("PP_REQUEST_INVALID", 400)
                if self.headers.get_content_type() != "application/json":
                    raise PPError("PP_REQUEST_INVALID", 415)
                try:
                    data = json.loads(self.rfile.read(length))
                except (ValueError, UnicodeError):
                    raise PPError("PP_REQUEST_INVALID", 400)
                if not isinstance(data, dict):
                    raise PPError("PP_REQUEST_INVALID", 400)
            if self.path.startswith("/api/admin/"):
                admin_cookie = cookies.get("pp_admin")
                admin_token = admin_cookie.value if admin_cookie else None
                path, _, query = self.path.partition("?")
                if method == "POST" and path == "/api/admin/login":
                    if set(data) != {"username", "password"}:
                        raise PPError("PP_REQUEST_INVALID", 400)
                    _, username, value = self.server.store.login_account(
                        data["username"], data["password"], admin_token, admin=True,
                    )
                    self.respond(200, {"authenticated": True, "username": username},
                                 cookie=self.admin_cookie(value))
                    return
                if method == "GET" and path == "/api/admin/me":
                    result = self.server.store.admin_me(admin_token)
                elif method == "POST" and path == "/api/admin/logout":
                    result = self.server.store.admin_logout(admin_token)
                    self.respond(200, result, cookie=self.admin_cookie("", clear=True))
                    return
                elif method == "GET" and path in (
                    "/api/admin/overview", "/api/admin/audit"
                ):
                    try:
                        pairs = parse_qsl(query, keep_blank_values=True,
                                          strict_parsing=True, max_num_fields=4,
                                          errors="strict")
                    except (ValueError, UnicodeError) as error:
                        raise PPError("PP_REQUEST_INVALID", 400) from error
                    params = dict(pairs)
                    allowed = {"offset", "q", "status"}
                    if path.endswith("/audit"):
                        allowed.add("event")
                    if (len(params) != len(pairs) or set(params) - allowed
                            or not re.fullmatch(r"[0-9]{1,9}", params.get("offset", "0"))):
                        raise PPError("PP_REQUEST_INVALID", 400)
                    offset = int(params.get("offset", "0"))
                    if path.endswith("/overview"):
                        result = self.server.store.admin_overview(
                            admin_token, offset, search=params.get("q", ""),
                            status=params.get("status", ""),
                        )
                    else:
                        result = self.server.store.admin_audit(
                            admin_token, offset, search=params.get("q", ""),
                            event=params.get("event", ""), status=params.get("status", ""),
                        )
                elif method == "POST" and path == "/api/admin/revoke":
                    self.server.store.admin_me(admin_token)
                    if (set(data) != {"consumerId", "reason", "confirm"}
                            or data["confirm"] is not True
                            or not isinstance(data["consumerId"], str)):
                        raise PPError("PP_REQUEST_INVALID", 400)
                    result = self.server.store.revoke(
                        data["consumerId"], admin_token=admin_token or "",
                        reason=data["reason"],
                    )
                else:
                    raise PPError("PP_ROUTE_NOT_FOUND", 404)
                self.respond(200, result)
                return
            if method == "POST" and self.path == "/api/session":
                if not consumer:
                    if session_token:
                        self.respond(
                            200,
                            {"consumerId": None, "authenticated": False},
                            cookie="pp_session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0",
                        )
                        return
                    consumer, value = self.server.store.create_consumer()
                    session_token = value
                    cookie = self.session_cookie(value)
                else:
                    cookie = None
                state = self.server.store.auth_state(consumer)
                self.respond(
                    200,
                    {"consumerId": consumer, **state},
                    cookie=cookie,
                )
                return
            if method == "GET" and self.path == "/api/auth/me":
                self.respond(200, {"consumerId": consumer, **self.server.store.auth_state(consumer)})
                return
            if method == "POST" and self.path == "/api/auth/register":
                if not consumer:
                    raise PPError("PP_SESSION_REQUIRED", 401)
                username, value = self.server.store.register_account(
                    consumer, data.get("username"), data.get("password"), session_token
                )
                self.respond(
                    201,
                    {"consumerId": consumer, "authenticated": True, "username": username},
                    cookie=self.session_cookie(value),
                )
                return
            if method == "POST" and self.path == "/api/auth/login":
                consumer, username, value = self.server.store.login_account(
                    data.get("username"), data.get("password"), session_token
                )
                self.respond(
                    200,
                    {"consumerId": consumer, "authenticated": True, "username": username},
                    cookie=self.session_cookie(value),
                )
                return
            if method == "POST" and self.path == "/api/auth/logout":
                if not consumer or not self.server.store.auth_state(consumer)["authenticated"]:
                    raise PPError("PP_AUTH_REQUIRED", 401)
                self.server.store.logout(consumer, session_token)
                self.respond(
                    200,
                    {"authenticated": False},
                    cookie="pp_session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0",
                )
                return
            if not consumer:
                raise PPError("PP_SESSION_REQUIRED", 401)
            if not self.server.store.auth_state(consumer)["authenticated"]:
                raise PPError("PP_AUTH_REQUIRED", 401)
            if method == "GET" and self.path == "/api/pp/me":
                result = self.server.store.me(consumer)
            elif method == "GET" and self.path == "/api/pp/history":
                result = {"events": self.server.store.history(consumer)}
            elif method == "GET" and self.path == "/api/memory":
                result = self.server.store.list_memory(consumer)
            elif method == "GET" and self.path == "/api/pp/mail":
                result = {"available": self.server.mail_config is not None,
                          **self.server.store.mail_status(consumer)}
            elif method == "POST" and self.path == "/api/pp/options":
                result = self.server.store.options(consumer)
            elif method == "POST" and self.path == "/api/pp/select":
                option_id = data.get("optionId")
                if not isinstance(option_id, str) or not 1 <= len(option_id) <= 64:
                    raise PPError("PP_REQUEST_INVALID", 400)
                email = self.server.store.validate_email(data.get("email", ""))
                if email and self.server.mail_config is None:
                    raise PPError("PP_EMAIL_UNAVAILABLE", 503)
                result = self.server.store.select(consumer, option_id, email=email)
            elif method == "POST" and self.path == "/api/pp/revoke":
                result = self.server.store.revoke(consumer)
            elif method == "POST" and self.path == "/api/memory/save":
                unexpected = set(data) - {"id", "title", "content", "tags"}
                if unexpected:
                    raise PPError("PP_MEMORY_INVALID", 400)
                result = self.server.store.save_memory(
                    consumer,
                    data.get("id"),
                    data.get("title"),
                    data.get("content"),
                    data.get("tags", []),
                )
            elif method == "POST" and self.path == "/api/memory/delete":
                if set(data) != {"id"}:
                    raise PPError("PP_MEMORY_INVALID", 400)
                result = self.server.store.delete_memory(consumer, data.get("id"))
            else:
                raise PPError("PP_ROUTE_NOT_FOUND", 404)
            self.respond(200, result)
        except PPError as error:
            LOG.warning("Request rejected: %s", error.code)
            try:
                self.server.store.record_error(consumer, error.code)
            except sqlite3.Error:
                LOG.exception("Could not persist error audit event")
                self.respond(503, {"error": "PP_SELECTION_UNKNOWN"})
                return
            self.respond(error.status, {"error": error.code})
        except (sqlite3.Error, OSError):
            LOG.exception("Storage or I/O failure")
            try:
                self.server.store.record_error(consumer, "PP_SELECTION_UNKNOWN")
            except sqlite3.Error:
                LOG.exception("Could not persist storage failure audit event")
            self.respond(503, {"error": "PP_SELECTION_UNKNOWN"})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--db", type=Path, default=ROOT / "data" / "palaco.sqlite3")
    parser.add_argument("--create-admin", action="store_true",
                        help="create a local administrator using hidden password input")
    parser.add_argument("--microsoft-login", action="store_true",
                        help="authorize personal Outlook.com SMTP using Microsoft device login")
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify persisted P.P. and audit invariants, then exit",
    )
    args = parser.parse_args()
    if sum((args.create_admin, args.check, args.microsoft_login)) > 1:
        parser.error("--create-admin, --check and --microsoft-login cannot be combined")
    if args.microsoft_login:
        try:
            sender = Store.validate_email(os.environ.get("PP_SMTP_FROM", ""))
            if not sender:
                raise ValueError("Stel PP_SMTP_FROM in op het gewenste Hotmail/Outlook-afzenderadres")
            configured_mailer(sender).login()
        except (MicrosoftMailError, ValueError, PPError, KeyboardInterrupt) as error:
            print(f"Microsoft-aanmelding niet voltooid: {error}")
            return 1
        return 0
    if args.check and not args.db.is_file():
        parser.error(f"database does not exist: {args.db}")
    args.db.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    store = Store(args.db)
    if args.create_admin:
        try:
            username = input("Beheerdersnaam: ")
            with warnings.catch_warnings():
                warnings.simplefilter("error", getpass.GetPassWarning)
                password = getpass.getpass("Wachtwoord (12-128 tekens): ")
                confirmation = getpass.getpass("Herhaal wachtwoord: ")
            if password != confirmation:
                raise PPError("PP_PASSWORD_CONFIRMATION_INVALID", 400)
            username = store.create_admin(username, password)
        except (PPError, EOFError, KeyboardInterrupt, getpass.GetPassWarning) as error:
            LOG.error("Beheerder niet aangemaakt: %s", error)
            return 1
        print(f"Beheerder {username} aangemaakt. Open /admin op de lokale server.")
        return 0
    if args.check:
        result = store.verify_integrity()
        print(json.dumps(result, indent=2))
        return 0 if result["ok"] else 1
    try:
        mail_config = smtp_configuration()
    except (ValueError, PPError, MicrosoftMailError) as error:
        LOG.error("SMTP-configuratie ongeldig: %s", error)
        return 1
    server = Server(("127.0.0.1", args.port), store, mail_config)
    stop = threading.Event()
    worker = None
    if mail_config:
        worker = threading.Thread(
            target=confirmation_worker, args=(store, mail_config, stop), daemon=True,
        )
        worker.start()
    else:
        LOG.warning("SMTP not configured; optional email confirmation unavailable")
    LOG.info("PALACO local prototype: http://127.0.0.1:%s", server.server_port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        LOG.info("Stopping server")
    finally:
        server.server_close()
        stop.set()
        if worker:
            worker.join(timeout=25)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
