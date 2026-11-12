"""Deterministic Review 044 inspection fixtures; no validator execution.

build_inspection_fixtures() returns immutable byte inputs and specification-only
expectations. No disk writes, network requests, clock access or identities.
"""
import hashlib
import json

from review_044_owner_inspection import _FIXED, _ROW_BINDING
from review_044_owner_registry import _base, _canonical


def _encode(obj: object) -> bytes:
    return (json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")


def _registry_and_report() -> tuple[dict, dict]:
    snapshot = _base()
    row = {
        "sequence": 1,
        "previousEntrySha256": None,
        "technicalReportSha256": "1" * 64,
        "ownerWorksheetSha256": "2" * 64,
        "evidenceIndexSha256": "3" * 64,
        "binding": "THREE_FILE_HASH_MATCH_UNTRUSTED",
        "evidenceKind": "IMPORTED_UNATTESTED_LOCAL_DOSSIER",
        "verification": "NOT_VERIFIED",
        "authorization": "HOLD",
        "accessDecision": "DENY",
        "issuance": "NOT_AUTHORIZED",
    }
    row["entrySha256"] = hashlib.sha256(_canonical(row)).hexdigest()
    snapshot["entries"].append(row)
    report = {**_FIXED, **{key: row[source] for key, source in _ROW_BINDING.items()}}
    return snapshot, report


def build_inspection_fixtures() -> tuple[tuple[str, bytes, bytes, str], ...]:
    """Prepare inputs for a later, separately authorized owner-run review.

    Each tuple: (scenario_id, registry_bytes, inspection_bytes, EXPECTED_RESULT).
    This function intentionally does not import/call either validator entrypoint.
    """
    registry, report = _registry_and_report()
    valid_registry, valid_report = _encode(registry), _encode(report)
    invalid = "PP_REVIEW_044_OWNER_INSPECTION_INVALID"
    fixtures = [("baseline_consistent_untrusted", valid_registry, valid_report,
                 "REGISTER_ROW_HASH_BINDING_CONSISTENT_UNTRUSTED")]

    def altered_report(name: str, key: str, value: object) -> None:
        changed = dict(report)
        changed[key] = value
        fixtures.append((name, valid_registry, _encode(changed), invalid))

    def altered_registry(name: str, change) -> None:
        copy = json.loads(valid_registry)
        change(copy)
        fixtures.append((name, _encode(copy), valid_report, invalid))

    altered_report("wrong_sequence", "sequence", 2)
    altered_report("boolean_sequence", "sequence", True)
    altered_report("wrong_entry_hash", "entrySha256", "f" * 64)
    altered_report("wrong_technical_hash", "technicalReportSha256", "f" * 64)
    altered_report("wrong_owner_hash", "ownerWorksheetSha256", "f" * 64)
    altered_report("wrong_index_hash", "evidenceIndexSha256", "f" * 64)
    altered_report("forged_previous_hash", "previousEntrySha256", "f" * 64)
    altered_report("authorization_escalation", "authorization", "ALLOW")
    altered_report("verification_escalation", "independentVerification", "VERIFIED")
    altered_report("history_escalation", "historicalImmutability", "VERIFIED")

    missing = dict(report)
    del missing["limitations"]
    fixtures.append(("missing_field", valid_registry, _encode(missing), invalid))
    extra = {**report, "approved": True}
    fixtures.append(("unexpected_field", valid_registry, _encode(extra), invalid))
    # Append a duplicate top-level field; standard JSON.parse silently collapses it.
    duplicate = valid_report.rstrip().removesuffix(b"}") + b',"authorization":"ALLOW"}\n'
    fixtures.append(("duplicate_inspection_key", valid_registry, duplicate, invalid))
    fixtures.append(("truncated_inspection_json", valid_registry, valid_report[:-4], invalid))
    fixtures.append(("oversized_inspection", valid_registry,
                     valid_report + b" " * (16 * 1024 + 1), invalid))
    fixtures.append(("empty_inspection", valid_registry, b"", invalid))
    fixtures.append(("invalid_utf8_inspection", valid_registry, b"\xff", invalid))

    altered_registry("broken_registry_entry_hash",
                     lambda r: r["entries"][0].update(entrySha256="f" * 64))
    altered_registry("forged_registry_authorization",
                     lambda r: r.update(authorization="ALLOW"))
    altered_registry("empty_registry",
                     lambda r: r.update(entries=[]))
    altered_registry("wrong_registry_row_sequence",
                     lambda r: r["entries"][0].update(sequence=9))
    duplicate_registry = valid_registry.rstrip().removesuffix(b"}") + b',"authorization":"ALLOW"}\n'
    fixtures.append(("duplicate_registry_key", duplicate_registry, valid_report, invalid))
    fixtures.append(("oversized_registry", valid_registry + b" " * (256 * 1024 + 1),
                     valid_report, invalid))
    return tuple(fixtures)
