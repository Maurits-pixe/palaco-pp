"""PP-IDB-001 local offline lineage outbox, without authorization semantics.

The caller must provide only opaque, server-issued references; this module must
never receive raw P.P. numbers, contact details or credentials.
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone

ALLOWED_EVENTS = frozenset({
    "PP_ACCOUNT_CREATED", "PERSON_BINDING_PROPOSED",
    "EXTERNAL_BINDING_PROPOSED", "CONTACT_VERIFICATION_RECORDED",
    "BINDING_REJECTED", "BINDING_REVOKED", "HUMAN_REVIEW_RECORDED",
})
SCHEMA = """
CREATE TABLE IF NOT EXISTS pp_lineage_outbox (
    event_id TEXT PRIMARY KEY,
    source_event_ref TEXT NOT NULL UNIQUE,
    event_type TEXT NOT NULL,
    local_consumer_ref TEXT NOT NULL,
    policy_version TEXT NOT NULL,
    provenance_ref TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    receipt_json TEXT
);
CREATE TRIGGER IF NOT EXISTS pp_outbox_no_delete
BEFORE DELETE ON pp_lineage_outbox
BEGIN SELECT RAISE(ABORT, 'PP_OUTBOX_APPEND_ONLY'); END;
CREATE TRIGGER IF NOT EXISTS pp_outbox_immutable
BEFORE UPDATE ON pp_lineage_outbox
WHEN NEW.event_id != OLD.event_id
  OR NEW.source_event_ref != OLD.source_event_ref
  OR NEW.event_type != OLD.event_type
  OR NEW.local_consumer_ref != OLD.local_consumer_ref
  OR NEW.policy_version != OLD.policy_version
  OR NEW.provenance_ref != OLD.provenance_ref
  OR NEW.payload_json != OLD.payload_json
  OR NEW.created_at != OLD.created_at
  OR OLD.receipt_json IS NOT NULL
  OR NEW.receipt_json IS NULL
BEGIN SELECT RAISE(ABORT, 'PP_OUTBOX_IMMUTABLE'); END;
"""

def _opaque(value: str) -> str:
    if not isinstance(value, str) or not 16 <= len(value) <= 256:
        raise ValueError("opaque reference required (16..256 characters)")
    if any(ch.isspace() for ch in value):
        raise ValueError("reference must not contain whitespace")
    return value

def initialize(connection: sqlite3.Connection) -> None:
    connection.executescript(SCHEMA)

def enqueue(connection: sqlite3.Connection, *, source_event_ref: str,
            event_type: str, local_consumer_ref: str,
            provenance_ref: str, policy_version: str = "PP-IDB-001-v0.1") -> str:
    """Enqueue evidence, not authority. Duplicate source refs return one ID."""
    if event_type not in ALLOWED_EVENTS:
        raise ValueError("unsupported event")
    source_event_ref = _opaque(source_event_ref)
    local_consumer_ref = _opaque(local_consumer_ref)
    provenance_ref = _opaque(provenance_ref)
    if not isinstance(policy_version, str) or not 3 <= len(policy_version) <= 80:
        raise ValueError("invalid policy version")
    event_id = str(uuid.uuid4())
    payload = {
        "event_id": event_id,
        "source_event_ref": source_event_ref,
        "event_type": event_type,
        "local_consumer_ref": local_consumer_ref,
        "provenance_ref": provenance_ref,
        "policy_version": policy_version,
        "identity_state": "CREATED_UNVERIFIED",
        "authorization_ref": None,
    }
    created_at = datetime.now(timezone.utc).isoformat()
    connection.execute(
        "INSERT OR IGNORE INTO pp_lineage_outbox VALUES(?,?,?,?,?,?,?, ?,NULL)",
        (event_id, source_event_ref, event_type, local_consumer_ref,
         policy_version, provenance_ref, json.dumps(payload, sort_keys=True), created_at),
    )
    row = connection.execute(
        "SELECT event_id, event_type, local_consumer_ref, provenance_ref "
        "FROM pp_lineage_outbox WHERE source_event_ref = ?",
        (source_event_ref,),
    ).fetchone()
    if row is None or row[1:] != (event_type, local_consumer_ref, provenance_ref):
        raise ValueError("conflicting event replay")
    return row[0]

def pending(connection: sqlite3.Connection, limit: int = 100) -> list[dict]:
    """Offline envelopes for a future trusted transport; never auto-send."""
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 100:
        raise ValueError("invalid limit")
    rows = connection.execute(
        "SELECT payload_json FROM pp_lineage_outbox WHERE receipt_json IS NULL "
        "ORDER BY created_at, event_id LIMIT ?", (limit,),
    )
    return [json.loads(row[0]) for row in rows]

def record_receipt(connection: sqlite3.Connection, event_id: str,
                   receipt_id: str) -> None:
    """Store trusted receipt reference; caller MUST verify server response first."""
    event_id = str(uuid.UUID(event_id))
    receipt_id = _opaque(receipt_id)
    row = connection.execute(
        "SELECT receipt_json FROM pp_lineage_outbox WHERE event_id = ?", (event_id,)
    ).fetchone()
    if row is None:
        raise ValueError("unknown event")
    receipt = json.dumps({"receipt_ref": receipt_id}, sort_keys=True)
    if row[0] is not None:
        if row[0] != receipt:
            raise ValueError("conflicting receipt")
        return
    connection.execute(
        "UPDATE pp_lineage_outbox SET receipt_json = ? "
        "WHERE event_id = ? AND receipt_json IS NULL", (receipt, event_id),
    )
