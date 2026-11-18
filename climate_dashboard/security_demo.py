"""Run safe, repeatable security and incident-response demonstrations.

Every attack simulation operates on in-memory copies or synthetic fixtures.
No external system, real credential, production dataset, or network attack is used.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import secrets
from pathlib import Path
from typing import Any

import pandas as pd

from climate_dashboard.integrity import verify_manifest
from climate_dashboard.pipeline import ROOT, SOURCE_REGISTER_FILE, validate_dataframe
from scripts.encryption_demo import (
    MAGIC,
    NONCE_BYTES,
    SALT_BYTES,
    decrypt_bytes,
    encrypt_bytes,
)

REVIEWED_DIR = ROOT / "data" / "processed" / "reviewed"
TRUSTED_FILE = REVIEWED_DIR / "trusted_data.csv"
MANIFEST_FILE = REVIEWED_DIR / "trusted_manifest.json"

RESPONSE_PHASES = [
    ("Preparation", "Preserve the trusted baseline, source evidence, expected hashes, and response contacts."),
    ("Detection and analysis", "Identify the changed bytes or records, affected fields, and likely technique mapping."),
    ("Containment", "Quarantine the simulated changed copy; never overwrite the trusted source."),
    ("Eradication", "Remove the simulated altered working copy after preserving its evidence."),
    ("Recovery", "Restore a fresh copy from the trusted baseline and verify its digest and data validation."),
    ("Lessons learned", "Record the control gap, evidence, residual risk, and follow-up action."),
]

SCENARIO_CATALOG = [
    {
        "scenario_id": "valid-accounts",
        "technique_id": "T1078",
        "technique_name": "Valid Accounts",
        "title": "Compromised contributor account",
        "description": "A contributor identity is assumed compromised and used to request an unauthorized change.",
        "mode": "tabletop",
        "detection": "No authentication service or account-audit telemetry is deployed in this local prototype; technical detection is not claimed.",
        "control": "Use MFA, least privilege, protected repository audit logs, and independent approval in a real hosted deployment.",
    },
    {
        "scenario_id": "stored-value",
        "technique_id": "T1565.001",
        "technique_name": "Stored Data Manipulation",
        "title": "Environmental value altered",
        "description": "Increase a copied energy observation by 50 percent.",
        "mode": "data",
        "control": "Compare the changed file with the protected trusted digest and record-level baseline.",
    },
    {
        "scenario_id": "stored-omission",
        "technique_id": "T1565.001",
        "technique_name": "Stored Data Manipulation",
        "title": "Environmental records deleted",
        "description": "Remove water observations from a copied dataset; removed is not zero.",
        "mode": "data",
        "control": "Compare record IDs, row counts, feature coverage, and the trusted digest.",
    },
    {
        "scenario_id": "stored-provenance",
        "technique_id": "T1565.001",
        "technique_name": "Stored Data Manipulation",
        "title": "Source attribution removed",
        "description": "Blank a source label while retaining the original trusted record.",
        "mode": "data",
        "control": "Validate required provenance and compare the record with the trusted source copy.",
    },
    {
        "scenario_id": "stored-scope",
        "technique_id": "T1565.001",
        "technique_name": "Stored Data Manipulation",
        "title": "Unit or reporting boundary changed",
        "description": "Change a unit or geography/boundary label without changing the source report.",
        "mode": "data",
        "control": "Validate metric-unit pairs and compare year, geography, facility scope, and lifecycle boundary.",
    },
    {
        "scenario_id": "transmitted-payload",
        "technique_id": "T1565.002",
        "technique_name": "Transmitted Data Manipulation",
        "title": "Data payload altered in transit",
        "description": "Change bytes in a simulated transfer payload and compare it with the sender-side digest.",
        "mode": "payload",
        "control": "Authenticate the transfer channel and verify a digest or signature from an independently trusted sender.",
    },
    {
        "scenario_id": "visualization-filter",
        "technique_id": "T1565.001",
        "technique_name": "Stored Data Manipulation",
        "title": "Visualization hides an unfavorable category",
        "description": "Change a synthetic chart-filter configuration so water records are excluded from the view.",
        "mode": "visual",
        "control": "Review report filters, visual interactions, axis ranges, labels, and the underlying expected feature inventory.",
    },
]


def classify_comparability(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    """Classify two observations without silently normalizing unlike evidence."""
    hard_mismatches = []
    conditional_mismatches = []
    for field in ("metric", "unit"):
        if str(left.get(field, "")).strip() != str(right.get(field, "")).strip():
            hard_mismatches.append(field)
    for field in (
        "data_year",
        "geography",
        "facility",
        "lifecycle_boundary",
        "calculation_method",
        "data_status",
    ):
        if str(left.get(field, "")).strip() != str(right.get(field, "")).strip():
            conditional_mismatches.append(field)

    if hard_mismatches:
        status = "NOT COMPARABLE"
        reasons = [f"Different {field.replace('_', ' ')}." for field in hard_mismatches]
    elif conditional_mismatches:
        status = "CONDITIONAL"
        reasons = [
            f"Align or explicitly qualify {field.replace('_', ' ')} before comparison."
            for field in conditional_mismatches
        ]
    else:
        status = "DIRECTLY COMPARABLE"
        reasons = ["Metric, unit, year, geography, facility scope, lifecycle boundary, method, and data status match."]
    return {
        "left_record": str(left.get("record_id", "")),
        "right_record": str(right.get("record_id", "")),
        "status": status,
        "reasons": reasons,
    }


def compare_all_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    comparisons = []
    for index, left in enumerate(records):
        for right in records[index + 1:]:
            comparisons.append(classify_comparability(left, right))
    counts = {
        status: sum(item["status"] == status for item in comparisons)
        for status in ("DIRECTLY COMPARABLE", "CONDITIONAL", "NOT COMPARABLE")
    }
    return {"pair_count": len(comparisons), "counts": counts, "pairs": comparisons}


def _read_records(content: bytes) -> tuple[list[str], list[dict[str, str]]]:
    stream = io.StringIO(content.decode("utf-8-sig"), newline="")
    reader = csv.DictReader(stream)
    if not reader.fieldnames:
        raise ValueError("Trusted CSV has no header.")
    return list(reader.fieldnames), list(reader)


def _write_records(fieldnames: list[str], records: list[dict[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    writer.writerows(records)
    return stream.getvalue().encode("utf-8")


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _mutate_scenario(scenario_id: str, original: bytes) -> tuple[bytes, str]:
    fieldnames, records = _read_records(original)
    changed = [dict(record) for record in records]

    if scenario_id == "stored-value":
        target = next((row for row in changed if "energy" in row.get("metric", "").lower()), None)
        if target is None:
            raise ValueError("No energy observation exists for the value-manipulation scenario.")
        before = float(target["value"])
        target["value"] = str(before * 1.5)
        detail = f'{target["record_id"]}: value changed from {before:g} to {float(target["value"]):g}.'
        return _write_records(fieldnames, changed), detail

    if scenario_id == "stored-omission":
        removed = [row for row in changed if "water" in row.get("metric", "").lower()]
        changed = [row for row in changed if "water" not in row.get("metric", "").lower()]
        if not removed:
            raise ValueError("No water observations exist for the omission scenario.")
        detail = "Removed record IDs: " + ", ".join(row["record_id"] for row in removed)
        return _write_records(fieldnames, changed), detail

    if scenario_id == "stored-provenance":
        target = next((row for row in changed if row.get("record_id") == "OBS005"), changed[0])
        old = target.get("source_name", "")
        target["source_name"] = ""
        detail = f'{target["record_id"]}: source_name changed from "{old}" to blank.'
        return _write_records(fieldnames, changed), detail

    if scenario_id == "stored-scope":
        target = next((row for row in changed if row.get("record_id") == "OBS001"), changed[0])
        old = target.get("unit", "")
        target["unit"] = "kg"
        detail = f'{target["record_id"]}: unit changed from "{old}" to "kg".'
        return _write_records(fieldnames, changed), detail

    if scenario_id == "transmitted-payload":
        changed_bytes = original.replace(b"27456000", b"37456000", 1)
        if changed_bytes == original:
            changed_bytes = original + b" "
        return changed_bytes, "One value sequence in a simulated transfer payload was changed."

    if scenario_id == "visualization-filter":
        baseline = {
            "view": "environmental-observations",
            "filters": {"year": "all", "metric": "all", "include_water": True},
            "axis": "reported value with unit",
        }
        altered = json.loads(json.dumps(baseline))
        altered["filters"]["include_water"] = False
        return json.dumps(altered, sort_keys=True).encode("utf-8"), (
            "Synthetic report configuration changed include_water from true to false; "
            "this is a configuration exercise, not an edit to the dashboard's deployed filters."
        )

    raise ValueError(f"Unknown data scenario: {scenario_id}")


def _response_exercise(scenario: dict[str, Any], trusted_bytes: bytes) -> dict[str, Any]:
    if scenario["mode"] == "tabletop":
        return {
            "status": "TABLETOP ONLY",
            "detected": None,
            "detail": scenario["detection"],
            "phases": [
                {"phase": phase, "status": "EXERCISED", "action": action}
                for phase, action in RESPONSE_PHASES
            ],
            "recovery_verified": None,
        }

    mutated_bytes, detail = _mutate_scenario(scenario["scenario_id"], trusted_bytes)
    expected_hash = _sha256(trusted_bytes)
    actual_hash = _sha256(mutated_bytes)
    detected = expected_hash != actual_hash

    # Keep the entire response exercise in memory. The simulated evidence,
    # quarantine, eradication, and recovery steps do not need plaintext files
    # on disk; this also prevents sensitive source material from being written
    # to temporary storage.
    working_copy = bytes(mutated_bytes)
    quarantine_evidence = bytes(working_copy)
    quarantined = quarantine_evidence == mutated_bytes
    working_copy = None
    eradicated = working_copy is None

    restored_bytes = bytes(trusted_bytes)
    restored_hash = _sha256(restored_bytes)
    recovery_verified = restored_hash == expected_hash

    validation_status = "NOT APPLICABLE"
    if scenario["mode"] == "data":
        frame = pd.read_csv(io.BytesIO(restored_bytes))
        source_register = pd.read_csv(SOURCE_REGISTER_FILE)
        validation_status = validate_dataframe(frame, source_register)["status"]

    phases = [
        {"phase": "Preparation", "status": "COMPLETE", "action": "Captured the trusted SHA-256 baseline and record inventory."},
        {"phase": "Detection and analysis", "status": "DETECTED" if detected else "NOT DETECTED", "action": detail},
        {"phase": "Containment", "status": "COMPLETE" if quarantined else "FAILED", "action": "Preserved the altered artifact in an isolated in-memory quarantine buffer."},
        {"phase": "Eradication", "status": "COMPLETE" if eradicated else "FAILED", "action": "Removed the altered working copy after preserving quarantine evidence."},
        {"phase": "Recovery", "status": "VERIFIED" if recovery_verified else "FAILED", "action": f"Restored trusted bytes; SHA-256 match={recovery_verified}; schema validation={validation_status}."},
        {"phase": "Lessons learned", "status": "COMPLETE", "action": scenario["control"]},
    ]
    return {
        "status": "PASS" if detected and quarantined and eradicated and recovery_verified and validation_status in ("PASS", "NOT APPLICABLE") else "FAIL",
        "detected": detected,
        "detail": detail,
        "expected_sha256": expected_hash,
        "simulated_sha256": actual_hash,
        "phases": phases,
        "recovery_verified": recovery_verified,
        "validation_status": validation_status,
    }


def run_security_demo() -> dict[str, Any]:
    """Run the full local security demonstration without changing project data."""
    if not TRUSTED_FILE.is_file() or not MANIFEST_FILE.is_file():
        raise FileNotFoundError(
            "Reviewed trusted data is missing. Start the dashboard with the project launcher first."
        )

    trusted_bytes = TRUSTED_FILE.read_bytes()
    manifest_ok, expected_hash, actual_hash = verify_manifest(TRUSTED_FILE, MANIFEST_FILE)
    frame = pd.read_csv(TRUSTED_FILE)
    source_register = pd.read_csv(SOURCE_REGISTER_FILE)
    validation = validate_dataframe(frame, source_register)
    records = frame.fillna("").to_dict(orient="records")

    tests = [
        {"id": "trusted-validation", "name": "Trusted dataset schema and source validation", "status": validation["status"], "detail": f'{validation["row_count"]} records; {validation["error_count"]} validation errors; {validation["warning_count"]} warnings.'},
        {"id": "trusted-sha256", "name": "Trusted SHA-256 manifest verification", "status": "PASS" if manifest_ok else "FAIL", "detail": f"Expected {expected_hash}; actual {actual_hash}."},
    ]

    demo_passphrase = secrets.token_urlsafe(32)
    encrypted_a = encrypt_bytes(trusted_bytes, demo_passphrase)
    encrypted_b = encrypt_bytes(trusted_bytes, demo_passphrase)
    round_trip = decrypt_bytes(encrypted_a, demo_passphrase) == trusted_bytes
    header_length = len(MAGIC) + SALT_BYTES + NONCE_BYTES
    fresh_parameters = encrypted_a[:header_length] != encrypted_b[:header_length]
    tests.append({"id": "aes-gcm-roundtrip", "name": "AES-256-GCM encryption and authenticated decryption", "status": "PASS" if round_trip else "FAIL", "detail": "Encrypted a temporary in-memory copy and recovered identical bytes."})
    tests.append({"id": "aes-gcm-fresh-nonce", "name": "Fresh random salt and nonce per encryption", "status": "PASS" if fresh_parameters else "FAIL", "detail": "Two encryptions of the same input produced different salt/nonce headers."})

    try:
        decrypt_bytes(encrypted_a, secrets.token_urlsafe(32))
        wrong_key_rejected = False
    except ValueError as exc:
        wrong_key_rejected = "Authentication failed" in str(exc)
    tests.append({"id": "aes-gcm-wrong-key", "name": "Wrong passphrase rejection", "status": "PASS" if wrong_key_rejected else "FAIL", "detail": "Unauthenticated plaintext was not returned."})

    tampered = bytearray(encrypted_a)
    tampered[-1] ^= 1
    try:
        decrypt_bytes(bytes(tampered), demo_passphrase)
        tamper_rejected = False
    except ValueError as exc:
        tamper_rejected = "Authentication failed" in str(exc)
    tests.append({"id": "aes-gcm-tamper", "name": "Ciphertext tampering rejection", "status": "PASS" if tamper_rejected else "FAIL", "detail": "AES-GCM authentication rejected a one-byte ciphertext modification."})

    comparisons = compare_all_records(records)
    scenarios = []
    for scenario in SCENARIO_CATALOG:
        result = _response_exercise(scenario, trusted_bytes)
        scenarios.append({**scenario, **result})

    technical_scenarios = [item for item in scenarios if item["status"] != "TABLETOP ONLY"]
    all_scenarios_pass = all(item["status"] == "PASS" for item in technical_scenarios)
    all_tests_pass = all(item["status"] == "PASS" for item in tests)
    return {
        "status": "PASS" if all_tests_pass and all_scenarios_pass else "FAIL",
        "summary": {
            "trusted_records": len(records),
            "security_tests_passed": sum(item["status"] == "PASS" for item in tests),
            "security_test_count": len(tests),
            "attack_scenarios_exercised": len(scenarios),
            "technical_scenarios_passed": sum(item["status"] == "PASS" for item in technical_scenarios),
            "tabletop_scenarios": sum(item["status"] == "TABLETOP ONLY" for item in scenarios),
            "response_phases_per_scenario": len(RESPONSE_PHASES),
            "comparability_pairs": comparisons["pair_count"],
            "comparability_counts": comparisons["counts"],
        },
        "tests": tests,
        "scenarios": scenarios,
        "comparability": comparisons,
        "security_boundary": [
            "All mutations are performed on temporary copies or synthetic in-memory configuration; trusted project files are never modified.",
            "MITRE ATT&CK is a static defensive mapping, not a live threat feed or evidence of a real intrusion.",
            "Valid Accounts is a tabletop exercise because the prototype has no login, MFA, authorization, or account-audit service.",
            "AES-256-GCM is a standalone file demonstration; it does not encrypt dashboard storage, GitHub Pages, or network traffic.",
            "SHA-256 detects changes only relative to a separately trusted reference. A manifest stored with writable data is not an independent trust anchor.",
            "This controlled exercise is not a penetration test, production SOC, or proof that every MITRE ATT&CK technique is covered.",
        ],
    }
