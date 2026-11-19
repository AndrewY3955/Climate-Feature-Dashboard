from __future__ import annotations

import json

from climate_dashboard.active_defense_lab import (
    run_active_defense_lab,
    verify_evidence_bundle,
)


def test_live_attacker_process_is_blocked_and_credential_revoked(tmp_path):
    result = run_active_defense_lab(evidence_dir=tmp_path)

    assert result["status"] == "PASS"
    assert result["outcome"] == "PREVENTED_AND_DETECTED_ROLLED_BACK"
    assert result["evidence_verifiable"] is True
    evidence = result["evidence"]
    assert evidence["attacker_process"]["executed"] is True
    assert evidence["attacker_process"]["exit_code"] == 0
    assert evidence["attacker_process"]["pid"] > 0
    assert evidence["attacker_process"]["reported_pid"] == evidence["attacker_process"]["pid"]
    assert evidence["attacker_process"]["pid_matches_os_process"] is True
    assert evidence["attacker_process"]["audit_pid_matches_os_pid"] is True
    assert evidence["attacker_process"]["transport"] == "HTTP over loopback TCP"
    requests = evidence["attacker_process"]["requests"]
    assert [item["http_status"] for item in requests] == [200, 403, 401, 200, 409, 401]
    assert requests[4]["response"]["decision"] == "DETECT_QUARANTINE_ROLLBACK_REVOKE"
    assert requests[1]["response"]["decision"] == "DENY_AND_REVOKE"
    assert evidence["defense"]["prevented_before_mutation"] is True
    assert evidence["defense"]["credential_revoked"] is True
    assert evidence["defense"]["unapproved_write_detected"] is True
    assert evidence["defense"]["working_copy_rolled_back"] is True
    quarantine = evidence["target_state"]["quarantine_evidence"]
    assert len(quarantine) == 1
    assert quarantine[0]["changed_record"]["value"] == 777777.0
    assert quarantine[0]["rollback_verified"] is True
    assert quarantine[0]["modified_sha256"] != quarantine[0]["restored_sha256"]
    assert quarantine[0]["before_sha256"] == quarantine[0]["restored_sha256"]
    assert evidence["target_state"]["unchanged"] is True
    assert evidence["target_state"]["before_sha256"] == evidence["target_state"]["after_sha256"]
    assert evidence["audit_chain_verified"] is True
    assert [event["sequence"] for event in evidence["audit_events"]] == list(
        range(1, len(evidence["audit_events"]) + 1)
    )
    assert any(event["event_type"] == "protected_write_blocked" for event in evidence["audit_events"])
    assert any(event["event_type"] == "credential_revoked" for event in evidence["audit_events"])
    assert result["evidence_file_sha256"]
    saved = json.loads((tmp_path / f"{result['run_id']}.json").read_text(encoding="utf-8"))
    assert verify_evidence_bundle(saved)


def test_evidence_tampering_is_detected(tmp_path):
    result = run_active_defense_lab(evidence_dir=tmp_path)
    altered = json.loads(json.dumps(result["evidence"]))
    altered["audit_events"][1]["decision"] = "ALLOW_WRITE"
    assert verify_evidence_bundle(result["evidence"]) is True
    assert verify_evidence_bundle(altered) is False


def test_evidence_report_hash_detects_report_changes(tmp_path):
    result = run_active_defense_lab(evidence_dir=tmp_path)
    altered = dict(result["evidence"])
    altered["outcome"] = "ATTACK_SUCCEEDED"
    assert verify_evidence_bundle(altered) is False
