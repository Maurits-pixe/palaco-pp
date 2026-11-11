"""Pure, offline Review 044 owner-evidence registry builder.

The returned snapshot is an append-only *claim* chain: it does not persist
files, prove historical source authenticity, or grant any permission.
"""

import hashlib
import json

from review_044_owner_dossier import assess_owner_dossier
from review_044_owner_index import _unique_pairs


MAX_REGISTRY_BYTES = 256 * 1024
MAX_ENTRIES = 256
_TOP = frozenset({"schema", "reference", "entries", "verification", "authorization", "accessDecision"})
_ROW = frozenset({
    "sequence", "previousEntrySha256", "entrySha256", "technicalReportSha256",
    "ownerWorksheetSha256", "evidenceIndexSha256", "binding", "evidenceKind",
    "verification", "authorization", "accessDecision", "issuance",
})


def _canonical(entry: dict[str, object]) -> bytes:
    return json.dumps(entry, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def _base() -> dict[str, object]:
    return {
        "schema": "palaco.pp.review-044-owner-registry.v0",
        "reference": "PP-RECOVERY-002",
        "entries": [],
        "verification": "NOT_VERIFIED",
        "authorization": "HOLD",
        "accessDecision": "DENY",
    }


def _check_snapshot(raw: bytes | None) -> dict[str, object]:
    if raw is None:
        return _base()
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_REGISTRY_BYTES:
        raise ValueError
    snapshot = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_pairs)
    expected = _base()
    if (type(snapshot) is not dict or set(snapshot) != _TOP
            or any(snapshot[field] != expected[field] for field in _TOP - {"entries"})):
        raise ValueError
    rows = snapshot["entries"]
    if type(rows) is not list or len(rows) > MAX_ENTRIES:
        raise ValueError
    previous = None
    identities = set()
    for i, row in enumerate(rows):
        if type(row) is not dict or set(row) != _ROW:
            raise ValueError
        if (type(row["sequence"]) is not int or row["sequence"] != i + 1
                or row["previousEntrySha256"] != previous):
            raise ValueError
        fixed = {
            "binding": "THREE_FILE_HASH_MATCH_UNTRUSTED",
            "evidenceKind": "IMPORTED_UNATTESTED_LOCAL_DOSSIER",
            "verification": "NOT_VERIFIED", "authorization": "HOLD",
            "accessDecision": "DENY", "issuance": "NOT_AUTHORIZED",
        }
        if any(row[field] != value for field, value in fixed.items()):
            raise ValueError
        for field in ("entrySha256", "technicalReportSha256", "ownerWorksheetSha256",
                      "evidenceIndexSha256"):
            value = row[field]
            if (type(value) is not str or len(value) != 64
                    or any(char not in "0123456789abcdef" for char in value)):
                raise ValueError
        without_hash = {key: value for key, value in row.items() if key != "entrySha256"}
        actual = hashlib.sha256(_canonical(without_hash)).hexdigest()
        if row["entrySha256"] != actual:
            raise ValueError
        identity = (row["technicalReportSha256"], row["ownerWorksheetSha256"],
                    row["evidenceIndexSha256"])
        if identity in identities:
            raise ValueError
        identities.add(identity)
        previous = row["entrySha256"]
    return snapshot


def append_owner_dossier(
    existing_registry: bytes | None,
    technical_report: bytes,
    owner_worksheet: bytes,
    evidence_index: bytes,
) -> bytes:
    """Return a new snapshot containing one additional, non-authoritative row.

    The caller must persist the returned bytes explicitly; no storage is
    changed here. A previous snapshot is structurally checked, not notarized.
    """
    try:
        snapshot = _check_snapshot(existing_registry)
        assessment = assess_owner_dossier(technical_report, owner_worksheet, evidence_index)
        rows = snapshot["entries"]
        if len(rows) >= MAX_ENTRIES:
            raise ValueError
        index_digest = hashlib.sha256(evidence_index).hexdigest()
        identity = (assessment["technicalReportSha256"],
                    assessment["ownerWorksheetSha256"], index_digest)
        if any((row["technicalReportSha256"], row["ownerWorksheetSha256"],
                row["evidenceIndexSha256"]) == identity for row in rows):
            raise ValueError
        new_row: dict[str, object] = {
            "sequence": len(rows) + 1,
            "previousEntrySha256": rows[-1]["entrySha256"] if rows else None,
            "technicalReportSha256": assessment["technicalReportSha256"],
            "ownerWorksheetSha256": assessment["ownerWorksheetSha256"],
            "evidenceIndexSha256": index_digest,
            "binding": "THREE_FILE_HASH_MATCH_UNTRUSTED",
            "evidenceKind": "IMPORTED_UNATTESTED_LOCAL_DOSSIER",
            "verification": "NOT_VERIFIED", "authorization": "HOLD",
            "accessDecision": "DENY", "issuance": "NOT_AUTHORIZED",
        }
        new_row["entrySha256"] = hashlib.sha256(_canonical(new_row)).hexdigest()
        rows.append(new_row)
        result = json.dumps(snapshot, ensure_ascii=False, indent=2).encode("utf-8") + b"\n"
        if len(result) > MAX_REGISTRY_BYTES:
            raise ValueError
        return result
    except (ValueError, TypeError, KeyError, UnicodeError, OverflowError) as exc:
        raise ValueError("PP_REVIEW_044_OWNER_REGISTRY_INVALID") from exc
