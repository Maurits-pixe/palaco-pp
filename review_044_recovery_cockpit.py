"""Offline PP-RECOVERY-002 recovery cockpit: five distinct trust boundaries.

Strictly revalidates original source files and the submitted plan/register.
A consistent bundle remains UNSIGNED, unverified, blocked and unauthorized.
No I/O, identity binding, test execution or account mutation.
"""
import hashlib

from review_044_human_review_queue import _dossier, _queue, _digest
from review_044_review_intake import _check_intake
from review_044_verification_plan import prepare_verification_plan
from review_044_observation_register import _plan, _register

ERROR = "PP_RECOVERY_002_COCKPIT_INVALID"


def prepare_recovery_cockpit(
    dossier_bytes: bytes, queue_bytes: bytes, intake_bytes: bytes,
    plan_bytes: bytes, register_bytes: bytes,
) -> dict[str, object]:
    """Produce non-authorizing counts and digest links from five source files."""
    try:
        dossier = _dossier(dossier_bytes)
        dossier_sha = _digest(dossier)
        queue = _queue(queue_bytes, dossier_sha)
        queue_sha = _digest(queue)
        requests = {event["sequence"]: event for event in queue["events"]}
        intake = _check_intake(intake_bytes, dossier_sha, queue_sha, requests)
        # Require a plan exactly matching recomputation from original sources.
        plan = _plan(plan_bytes, dossier_bytes, queue_bytes, intake_bytes)
        expected = prepare_verification_plan(dossier_bytes, queue_bytes, intake_bytes)
        if plan != expected or len(intake["items"]) != plan["intakeCount"]:
            raise ValueError
        plan_raw_sha = hashlib.sha256(plan_bytes).hexdigest()
        register = _register(register_bytes, plan_raw_sha, plan)
        counts = {mark: 0 for mark in (
            "OBSERVATION_REPORTED", "BLOCKER_REPORTED", "RECHECK_REQUESTED"
        )}
        for event in register["events"]:
            counts[event["mark"]] += 1
        return {
            "schema": "palaco.pp.recovery-002-cockpit.v0",
            "reference": "PP-RECOVERY-002",
            "sources": {
                "decisionDossierSha256": hashlib.sha256(dossier_bytes).hexdigest(),
                "reviewQueueSha256": hashlib.sha256(queue_bytes).hexdigest(),
                "reviewIntakeSha256": hashlib.sha256(intake_bytes).hexdigest(),
                "verificationPlanSha256": plan_raw_sha,
                "observationRegisterSha256": hashlib.sha256(register_bytes).hexdigest(),
            },
            "contractBinding": "STRICT_INTERNAL_FIVE_FILE_CONSISTENCY_ONLY",
            "requestCount": len(queue["events"]),
            "intakeCount": len(intake["items"]),
            "plannedCheckCount": plan["checkCount"],
            "observationCount": len(register["events"]),
            "observationKinds": counts,
            "decisionGates": [
                {"requirementId": gate["requirementId"],
                 "gate": "BLOCKED", "verification": "NOT_VERIFIED"}
                for gate in plan["decisionGates"]
            ],
            "independentSourceAttestation": "ABSENT",
            "reviewerAuthority": "NOT_ESTABLISHED",
            "subjectBinding": "NOT_ESTABLISHED",
            "historicalImmutability": "NOT_ESTABLISHED",
            "humanReview": "NOT_COMPLETED",
            "palacoOneHandoff": "BLOCKED",
            "palacoOneSession": "NOT_CREATED",
            "independentVerification": "NOT_VERIFIED",
            "reviewDecision": "HOLD",
            "authorization": "HOLD",
            "accessDecision": "DENY",
            "issuance": "NOT_AUTHORIZED",
        }
    except (ValueError, TypeError, KeyError, IndexError, UnicodeError, OverflowError) as exc:
        raise ValueError(ERROR) from exc
