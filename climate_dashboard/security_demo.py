"""Run safe, repeatable security and incident-response demonstrations.

Each technical attack runs in a short-lived, isolated child process against a
 disposable lab file. The lab uses temporary copies/synthetic fixtures only;
no external system, real credential, production dataset, or network target is used.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import secrets
import subprocess
import sys
import tempfile
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
        "attack_vector": "Misuse of a valid contributor identity to request an unauthorized change (assumed, not technically executed).",
        "simulated_change": "No account, credential, repository permission, or audit record is changed; the identity compromise is a tabletop assumption.",
        "defense_used": "Tabletop response: preserve repository evidence; recommend MFA, least privilege, protected audit logs, and independent approval. These controls are not deployed by this prototype.",
        "result_basis": "TABLETOP ONLY — response steps discussed; no technical account-compromise detection or prevention was tested.",
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
        "attack_vector": "Stored record value tampering (MITRE ATT&CK T1565.001).",
        "simulated_change": "Increase the value field of one copied energy observation by 50%; the trusted CSV remains unchanged.",
        "defense_used": "Compare the altered copy's SHA-256 with the trusted baseline; preserve the changed bytes in a quarantine evidence file in the temporary lab directory; restore trusted bytes and validate the restored dataset. Record-level review is a recommended follow-up, not a separate automated detector in this scenario.",
        "result_basis": "PASS when the digest mismatch detects the altered copy and the trusted-byte recovery digest and schema validation pass.",
        "mode": "data",
        "control": "Compare the changed file with the protected trusted digest and record-level baseline.",
    },
    {
        "scenario_id": "stored-omission",
        "technique_id": "T1565.001",
        "technique_name": "Stored Data Manipulation",
        "title": "Environmental records deleted",
        "description": "Remove water observations from a copied dataset; removed is not zero.",
        "attack_vector": "Stored record deletion / omission (MITRE ATT&CK T1565.001).",
        "simulated_change": "Remove copied water-observation rows and retain their record IDs in the scenario evidence; trusted records remain intact.",
        "defense_used": "The SHA-256 baseline comparison detects the changed file; quarantine the altered bytes and restore trusted bytes. Record-ID, row-count, and feature-coverage review are recommended follow-up checks, not separate automated detectors in this scenario.",
        "result_basis": "PASS when the altered-copy digest differs and restored trusted bytes match the baseline and pass schema validation.",
        "mode": "data",
        "control": "Compare record IDs, row counts, feature coverage, and the trusted digest.",
    },
    {
        "scenario_id": "stored-provenance",
        "technique_id": "T1565.001",
        "technique_name": "Stored Data Manipulation",
        "title": "Source attribution removed",
        "description": "Blank a source label while retaining the original trusted record.",
        "attack_vector": "Stored provenance / source-attribution tampering (MITRE ATT&CK T1565.001).",
        "simulated_change": "Blank the source_name field on one copied observation; the original trusted record is preserved.",
        "defense_used": "The SHA-256 baseline comparison detects the changed file; quarantine the altered bytes and restore trusted bytes. Required-source and provenance validation are recommended follow-up controls, not separately demonstrated detection in this scenario.",
        "result_basis": "PASS when the altered copy is detected and the restored trusted dataset passes digest and schema checks.",
        "mode": "data",
        "control": "Validate required provenance and compare the record with the trusted source copy.",
    },
    {
        "scenario_id": "stored-scope",
        "technique_id": "T1565.001",
        "technique_name": "Stored Data Manipulation",
        "title": "Unit or reporting boundary changed",
        "description": "Change a unit or geography/boundary label without changing the source report.",
        "attack_vector": "Stored unit / reporting-scope tampering (MITRE ATT&CK T1565.001).",
        "simulated_change": "Change the unit field on one copied observation (for example, MWh to kg) without changing the source report.",
        "defense_used": "The SHA-256 baseline comparison detects the changed file; quarantine the altered bytes and restore trusted bytes. Metric-unit and reporting-scope validation are recommended follow-up controls, not separately demonstrated detection in this scenario.",
        "result_basis": "PASS when the changed copy is detected and restored trusted bytes pass digest and schema checks.",
        "mode": "data",
        "control": "Validate metric-unit pairs and compare year, geography, facility scope, and lifecycle boundary.",
    },
    {
        "scenario_id": "transmitted-payload",
        "technique_id": "T1565.002",
        "technique_name": "Transmitted Data Manipulation",
        "title": "Data payload altered in transit",
        "description": "Change bytes in a simulated transfer payload and compare it with the sender-side digest.",
        "attack_vector": "In-transit payload modification (MITRE ATT&CK T1565.002); simulated bytes only, not a live network interception.",
        "simulated_change": "Alter one value sequence in a synthetic transfer payload; no network traffic or deployed transport path is modified.",
        "defense_used": "Compare the received payload digest with the sender-side trusted digest; preserve the altered payload in a quarantine evidence file in the temporary lab directory and recover the original trusted bytes.",
        "result_basis": "PASS when the payload digest mismatch is detected and the original trusted-byte digest is verified after recovery.",
        "mode": "payload",
        "control": "Authenticate the transfer channel and verify a digest or signature from an independently trusted sender.",
    },
    {
        "scenario_id": "visualization-filter",
        "technique_id": "T1565.001",
        "technique_name": "Stored Data Manipulation",
        "title": "Visualization hides an unfavorable category",
        "description": "Change a synthetic chart-filter configuration so water records are excluded from the view.",
        "attack_vector": "Report / visualization configuration manipulation (mapped to MITRE ATT&CK T1565.001 as a stored-data integrity scenario; not a dedicated visualization technique claim).",
        "simulated_change": "Set include_water from true to false in a disposable dashboard-config.json file; deployed dashboard filters are not changed.",
        "defense_used": "Compare the synthetic configuration bytes with the original configuration digest, preserve the altered configuration in a quarantine evidence file and restore the original synthetic configuration. This does not test the deployed dashboard filters.",
        "result_basis": "PASS when the synthetic configuration change is identified and the original configuration is restored; this does not test deployed dashboard visuals.",
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
    """Execute an attacker child process against a disposable lab file, then defend it."""
    if scenario["mode"] == "tabletop":
        return {
            "status": "TABLETOP ONLY",
            "detected": None,
            "detail": scenario["detection"],
            "result": scenario["result_basis"],
            "phases": [
                {"phase": phase, "status": "EXERCISED", "action": action}
                for phase, action in RESPONSE_PHASES
            ],
            "recovery_verified": None,
            "attack_execution": {
                "mode": "tabletop",
                "executed": False,
                "reason": "No authentication service or account-audit telemetry exists in this application.",
            },
        }

    baseline = trusted_bytes
    target_name = "lab-target.data"
    if scenario["mode"] == "visual":
        baseline = json.dumps({
            "view": "environmental-observations",
            "filters": {"year": "all", "metric": "all", "include_water": True},
            "axis": "reported value with unit",
        }, sort_keys=True).encode("utf-8")
        target_name = "lab-target.data"

    # This child process is the attacker. It has one target path in a temporary
    # directory, no shell, no network code, and no access to project paths.
    attacker_script = r'''
import csv, io, json, pathlib, sys
scenario, filename = sys.argv[1], pathlib.Path("lab-target.data")
original = filename.read_bytes()
if scenario == "transmitted-payload":
    changed = original.replace(b"27456000", b"37456000", 1)
    if changed == original:
        changed = original + b" "
    filename.write_bytes(changed)
    print("Modified one payload byte sequence in the isolated transfer fixture.")
elif scenario == "visualization-filter":
    config = json.loads(original.decode("utf-8"))
    before = config["filters"]["include_water"]
    config["filters"]["include_water"] = False
    filename.write_text(json.dumps(config, sort_keys=True), encoding="utf-8")
    print(f"Changed include_water from {before} to false in the lab configuration.")
else:
    stream = io.StringIO(original.decode("utf-8-sig"), newline="")
    reader = csv.DictReader(stream)
    fields = reader.fieldnames
    rows = list(reader)
    if not fields or not rows:
        raise SystemExit("Lab CSV is empty or has no header.")
    if scenario == "stored-value":
        target = next((r for r in rows if "energy" in r.get("metric", "").lower()), None)
        if target is None:
            raise SystemExit("No energy observation available.")
        before = float(target["value"])
        target["value"] = str(before * 1.5)
        detail = f'{target["record_id"]}: value {before:g} -> {float(target["value"]):g}'
    elif scenario == "stored-omission":
        removed = [r for r in rows if "water" in r.get("metric", "").lower()]
        rows = [r for r in rows if "water" not in r.get("metric", "").lower()]
        if not removed:
            raise SystemExit("No water observations available.")
        detail = "Deleted record IDs: " + ", ".join(r.get("record_id", "?") for r in removed)
    elif scenario == "stored-provenance":
        target = next((r for r in rows if r.get("record_id") == "OBS005"), rows[0])
        before = target.get("source_name", "")
        target["source_name"] = ""
        detail = f'{target.get("record_id")}: source_name "{before}" -> blank'
    elif scenario == "stored-scope":
        target = next((r for r in rows if r.get("record_id") == "OBS001"), rows[0])
        before = target.get("unit", "")
        target["unit"] = "kg"
        detail = f'{target.get("record_id")}: unit "{before}" -> "kg"'
    else:
        raise SystemExit("Unknown attack scenario.")
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    filename.write_bytes(output.getvalue().encode("utf-8"))
    print(detail)
'''
    with tempfile.TemporaryDirectory(prefix="climate-attack-lab-") as temporary:
        lab_dir = Path(temporary).resolve()
        target = lab_dir / target_name
        quarantine = lab_dir / "quarantine.evidence"
        target.write_bytes(baseline)
        expected_hash = _sha256(baseline)

        # Do not pass application credentials, API tokens, or unrelated
        # environment variables into the attacker process. Windows receives
        # only the OS variables needed to start Python reliably.
        child_env = {
            key: os.environ[key]
            for key in ("SYSTEMROOT", "WINDIR", "TEMP", "TMP")
            if key in os.environ
        }
        try:
            process = subprocess.run(
                [sys.executable, "-I", "-c", attacker_script, scenario["scenario_id"]],
                cwd=lab_dir,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=5,
                check=False,
                env=child_env,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return {
                "status": "FAIL",
                "detected": False,
                "detail": f"Attacker process could not complete: {exc}",
                "result": "FAIL — attack execution did not complete.",
                "phases": [
                    {"phase": "Preparation", "status": "COMPLETE", "action": "Created disposable target and retained trusted baseline."},
                    {"phase": "Detection and analysis", "status": "FAILED", "action": "Attacker process did not complete: " + str(exc)},
                    {"phase": "Containment", "status": "NOT RUN", "action": "No altered artifact was confirmed for quarantine."},
                    {"phase": "Eradication", "status": "NOT RUN", "action": "No altered working target was confirmed for removal."},
                    {"phase": "Recovery", "status": "NOT RUN", "action": "Recovery was not claimed after failed attack execution."},
                    {"phase": "Lessons learned", "status": "REVIEW REQUIRED", "action": scenario["control"]},
                ],
                "recovery_verified": False,
                "attack_execution": {"mode": "isolated child process", "executed": False, "error": str(exc)},
            }

        if process.returncode != 0 or not target.is_file():
            error = (process.stderr or process.stdout or "Attacker process did not modify the lab target.").strip()
            return {
                "status": "FAIL",
                "detected": False,
                "detail": error,
                "result": "FAIL — attack process failed; no defensive success is claimed.",
                "phases": [
                    {"phase": "Preparation", "status": "COMPLETE", "action": "Created disposable target and retained trusted baseline."},
                    {"phase": "Detection and analysis", "status": "FAILED", "action": "Attacker process failed: " + error},
                    {"phase": "Containment", "status": "NOT RUN", "action": "No successful attack artifact was confirmed for quarantine."},
                    {"phase": "Eradication", "status": "NOT RUN", "action": "No altered working target was confirmed for removal."},
                    {"phase": "Recovery", "status": "NOT RUN", "action": "Recovery was not claimed after failed attack execution."},
                    {"phase": "Lessons learned", "status": "REVIEW REQUIRED", "action": scenario["control"]},
                ],
                "recovery_verified": False,
                "attack_execution": {
                    "mode": "isolated child process",
                    "executed": False,
                    "exit_code": process.returncode,
                    "stdout": process.stdout.strip(),
                    "stderr": process.stderr.strip(),
                },
            }

        attacked_bytes = target.read_bytes()
        actual_hash = _sha256(attacked_bytes)
        detected = actual_hash != expected_hash
        detail = process.stdout.strip() or "Attacker process modified the isolated target."
        quarantine.write_bytes(attacked_bytes)
        quarantine_hash = _sha256(quarantine.read_bytes())
        quarantined = quarantine_hash == actual_hash

        # Eradicate the compromised working file, then recover from the
        # independently retained in-process trusted baseline.
        target.unlink(missing_ok=True)
        eradicated = not target.exists()
        target.write_bytes(baseline)
        restored_hash = _sha256(target.read_bytes())
        recovery_verified = restored_hash == expected_hash

        validation_status = "NOT APPLICABLE"
        if scenario["mode"] == "data":
            frame = pd.read_csv(target)
            source_register = pd.read_csv(SOURCE_REGISTER_FILE)
            validation_status = validate_dataframe(frame, source_register)["status"]

        success = (
            process.returncode == 0
            and detected
            and quarantined
            and eradicated
            and recovery_verified
            and validation_status in ("PASS", "NOT APPLICABLE")
        )
        phases = [
            {"phase": "Preparation", "status": "COMPLETE", "action": f"Created disposable target {target_name}; attacker child process exit code {process.returncode}; {detail} Trusted SHA-256={expected_hash}."},
            {"phase": "Detection and analysis", "status": "DETECTED" if detected else "NOT DETECTED", "action": f"Defender compared target SHA-256 {actual_hash} with trusted SHA-256 {expected_hash}."},
            {"phase": "Containment", "status": "COMPLETE" if quarantined else "FAILED", "action": f"Copied altered target to isolated quarantine evidence; evidence SHA-256={quarantine_hash}."},
            {"phase": "Eradication", "status": "COMPLETE" if eradicated else "FAILED", "action": "Deleted the altered working target after preserving quarantine evidence."},
            {"phase": "Recovery", "status": "VERIFIED" if recovery_verified else "FAILED", "action": f"Restored trusted baseline; digest match={recovery_verified}; schema validation={validation_status}."},
            {"phase": "Lessons learned", "status": "COMPLETE", "action": scenario["control"]},
        ]
        return {
            "status": "PASS" if success else "FAIL",
            "detected": detected,
            "detail": detail,
            "result": scenario["result_basis"] if success else "FAIL — attack, detection, quarantine, eradication, recovery, or validation did not pass.",
            "expected_sha256": expected_hash,
            "simulated_sha256": actual_hash,
            "phases": phases,
            "recovery_verified": recovery_verified,
            "validation_status": validation_status,
            "attack_execution": {
                "mode": "isolated child process",
                "executed": process.returncode == 0,
                "exit_code": process.returncode,
                "target": target_name,
                "before_sha256": expected_hash,
                "after_sha256": actual_hash,
                "quarantine_sha256": quarantine_hash,
                "recovery_sha256": restored_hash,
                "stdout": process.stdout.strip(),
                "stderr": process.stderr.strip(),
                "network_access": "not used",
                "scope": "disposable temporary directory only",
            },
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
            "Technical attacks modify disposable files inside temporary directories; quarantine evidence is also temporary. Trusted project files are never modified. The account scenario remains tabletop-only.",
            "MITRE ATT&CK is a static defensive mapping, not a live threat feed or evidence of a real intrusion.",
            "Valid Accounts is a tabletop exercise because the prototype has no login, MFA, authorization, or account-audit service.",
            "AES-256-GCM is a standalone file demonstration; it does not encrypt dashboard storage, GitHub Pages, or network traffic.",
            "SHA-256 detects changes only relative to a separately trusted reference. A manifest stored with writable data is not an independent trust anchor.",
            "This controlled exercise is not a penetration test, production SOC, or proof that every MITRE ATT&CK technique is covered.",
        ],
    }
