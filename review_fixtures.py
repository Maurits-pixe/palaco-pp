"""Deterministic, synthetic P.P. review fixtures; no file I/O or execution.

Call ``build_review_fixtures()`` explicitly during a later authorized test.
All identities below are invented test UUIDs, never production identities.
"""

from copy import deepcopy
import hashlib
import json
from typing import Any


def _bytes(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")


def build_review_fixtures() -> dict[str, tuple[bytes, bytes, bytes, bytes]]:
    """Return one internally consistent chain and explicit negative variants.

    This is only fixture preparation. It never invokes review validators.
    Each result contains (handoff, report, index, observation) in that order.
    """
    handoff = {
        "schema": "palaco.pp.one.review-handoff.v0", "reference": "PP-RECOVERY-002",
        "createdAt": "2026-11-11T09:00:00.000Z",
        "source": "LOCAL_PP_PROTOTYPE_USER_EXPORTED",
        "destination": "PALACO_ONE_MANUAL_REVIEW_ONLY",
        "subjectReference": {"consumerId": "00000000-0000-4000-8000-000000000001"},
        "registration": {
            "ppNumberId": "00000000-0000-4000-8000-000000000002",
            "ppNumberLast4": "0000", "status": "ACTIVE",
            "selectedAt": "2026-11-11T08:59:00.000Z", "revokedAt": None,
        },
        "provenance": "UNSIGNED_USER_CONTROLLED_FILE",
        "identityVerification": "NOT_VERIFIED", "reviewDecision": "PENDING_HUMAN_REVIEW",
        "authorization": "HOLD", "accessDecision": "DENY", "issuance": "NOT_AUTHORIZED",
        "constraints": ["NO_AUTOMATIC_ACCOUNT_LINK", "NO_AUTHENTICATION", "NO_AUTO_ISSUANCE"],
    }
    hb = _bytes(handoff)
    report = {
        "schema": "palaco.pp.manual-review.v0", "evidenceReference": "PP-RECOVERY-002",
        "capturedAt": "2026-11-11T09:01:00.000Z",
        "fileSha256": hashlib.sha256(hb).hexdigest(),
        "structuralStatus": "CLIENT_STRUCTURE_RECOGNIZED_UNTRUSTED",
        "sourceEvidence": "UNSIGNED_USER_SUPPLIED_FILE", "verification": "NOT_VERIFIED",
        "reviewDecision": "HOLD", "authorization": "HOLD", "accessDecision": "DENY",
        "issuance": "NOT_AUTHORIZED", "note": "Synthetisch voorbeeld, niet beoordeeld",
        "noteClass": "LOCAL_ADMIN_NOTE_NOT_INDEPENDENTLY_VERIFIED",
    }
    rb = _bytes(report)
    index = {
        "schema": "palaco.pp.evidence-index.v0", "reference": "PP-RECOVERY-002",
        "createdAt": "2026-11-11T09:02:00.000Z",
        "linkage": "HASH_MATCH_UNTRUSTED_CLIENT_OBSERVATION",
        "handoffSha256": hashlib.sha256(hb).hexdigest(),
        "reportSha256": hashlib.sha256(rb).hexdigest(),
        "verification": "NOT_VERIFIED", "reviewDecision": "HOLD",
        "authorization": "HOLD", "accessDecision": "DENY", "issuance": "NOT_AUTHORIZED",
        "note": "Geen digitale handtekening, onafhankelijke bronverificatie of accountkoppeling.",
    }
    ib = _bytes(index)
    observation = {
        "schema": "palaco.pp.chain-observation.v0", "reference": "PP-RECOVERY-002",
        "capturedAt": "2026-11-11T09:03:00.000Z",
        "outcome": "CLIENT_THREE_FILE_HASH_MATCH_UNTRUSTED",
        "handoffSha256": hashlib.sha256(hb).hexdigest(),
        "reportSha256": hashlib.sha256(rb).hexdigest(),
        "indexSha256": hashlib.sha256(ib).hexdigest(),
        "verification": "NOT_VERIFIED", "reviewDecision": "HOLD",
        "authorization": "HOLD", "accessDecision": "DENY", "issuance": "NOT_AUTHORIZED",
        "provenance": "UNSIGNED_LOCAL_BROWSER_OBSERVATION",
    }
    ob = _bytes(observation)
    base = (hb, rb, ib, ob)
    fixtures = {"baseline_untrusted_hold": base}

    changed = deepcopy(handoff)
    changed["registration"]["ppNumberLast4"] = "9999"
    fixtures["handoff_changed_without_rebinding"] = (_bytes(changed), rb, ib, ob)

    changed_report = deepcopy(report)
    changed_report["authorization"] = "ALLOW"
    fixtures["report_authority_escalation"] = (hb, _bytes(changed_report), ib, ob)

    changed_index = deepcopy(index)
    changed_index["reportSha256"] = "0" * 64
    fixtures["index_wrong_report_digest"] = (hb, rb, _bytes(changed_index), ob)

    changed_observation = deepcopy(observation)
    changed_observation["indexSha256"] = "f" * 64
    fixtures["observation_wrong_index_digest"] = (hb, rb, ib, _bytes(changed_observation))

    changed_observation = deepcopy(observation)
    changed_observation["authorization"] = "APPROVED"
    fixtures["observation_authority_escalation"] = (hb, rb, ib, _bytes(changed_observation))

    fixtures["observation_duplicate_key"] = (
        hb, rb, ib, ob.rstrip(b"\n")[:-1] + b',"authorization":"HOLD"}\n',
    )
    fixtures["observation_truncated_json"] = (hb, rb, ib, ob[:-4])
    fixtures["observation_oversized"] = (hb, rb, ib, ob + b" " * 16384)
    return fixtures
