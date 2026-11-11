"""Strict offline validator for a browser-exported Review 044 row inspection.

This checks structural and hash-binding consistency only. It never establishes
source authenticity, historical immutability, identity or permission.
"""

import json

from review_044_owner_index import _unique_pairs
from review_044_owner_registry import _check_snapshot


MAX_INSPECTION_BYTES = 16 * 1024
_FIXED = {
    "schema": "palaco.pp.review-044-registry-row-inspection.v0",
    "reference": "PP-RECOVERY-002",
    "sourceRegistrySchema": "palaco.pp.review-044-owner-registry.v0",
    "internalConsistency": "BROWSER_INDICATED_CHAIN_CONSISTENT",
    "evidenceKind": "IMPORTED_UNATTESTED_LOCAL_DOSSIER",
    "independentVerification": "NOT_VERIFIED",
    "historicalImmutability": "NOT_ESTABLISHED",
    "identityBinding": "NOT_ESTABLISHED",
    "executionProvenance": "NOT_INDEPENDENTLY_ESTABLISHED",
    "authorization": "HOLD",
    "accessDecision": "DENY",
    "issuance": "NOT_AUTHORIZED",
    "limitations": (
        "No external attestation, source authenticity, historical integrity, "
        "clock or identity proof; Python validation required."
    ),
}
_ROW_BINDING = {
    "sequence": "sequence",
    "technicalReportSha256": "technicalReportSha256",
    "ownerWorksheetSha256": "ownerWorksheetSha256",
    "evidenceIndexSha256": "evidenceIndexSha256",
    "entrySha256": "entrySha256",
    "previousEntrySha256": "previousEntrySha256",
}


def validate_owner_inspection(registry_bytes: bytes, inspection_bytes: bytes) -> dict[str, object]:
    """Validate an inspection against the exact referenced registry row.

    Returns a non-authoritative result. Raises a single stable ValueError for
    malformed input, duplicate JSON keys, hash mismatch or a modified claim.
    """
    try:
        registry = _check_snapshot(registry_bytes)
        if type(inspection_bytes) is not bytes or not 0 < len(inspection_bytes) <= MAX_INSPECTION_BYTES:
            raise ValueError
        report = json.loads(inspection_bytes.decode("utf-8"), object_pairs_hook=_unique_pairs)
        if (type(report) is not dict
                or set(report) != set(_FIXED) | set(_ROW_BINDING)
                or any(report[key] != value for key, value in _FIXED.items())):
            raise ValueError
        sequence = report["sequence"]
        rows = registry["entries"]
        if type(sequence) is not int or not 1 <= sequence <= len(rows):
            raise ValueError
        row = rows[sequence - 1]
        if any(report[key] != row[source] or type(report[key]) is not type(row[source])
               for key, source in _ROW_BINDING.items()):
            raise ValueError
        return {
            "schema": "palaco.pp.review-044-registry-row-validation.v0",
            "reference": "PP-RECOVERY-002",
            "sequence": sequence,
            "entrySha256": row["entrySha256"],
            "result": "REGISTER_ROW_HASH_BINDING_CONSISTENT_UNTRUSTED",
            "independentVerification": "NOT_VERIFIED",
            "authorization": "HOLD",
            "accessDecision": "DENY",
            "issuance": "NOT_AUTHORIZED",
        }
    except (ValueError, TypeError, KeyError, UnicodeError, OverflowError) as exc:
        raise ValueError("PP_REVIEW_044_OWNER_INSPECTION_INVALID") from exc
