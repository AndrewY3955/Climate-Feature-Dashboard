from climate_dashboard.security_demo import _response_exercise


def test_payload_attack_executes_child_process_and_recovers_trusted_bytes():
    scenario = {
        "scenario_id": "transmitted-payload",
        "mode": "payload",
        "control": "Verify sender and receiver integrity evidence.",
        "result_basis": "PASS when modified payload is detected and recovered.",
    }

    result = _response_exercise(scenario)

    assert result["status"] == "PASS"
    assert result["attack_execution"]["executed"] is True
    assert result["attack_execution"]["exit_code"] == 0
    assert result["attack_execution"]["before_sha256"] != result["attack_execution"]["after_sha256"]
    assert result["attack_execution"]["quarantine_sha256"] == result["attack_execution"]["after_sha256"]
    assert result["attack_execution"]["recovery_sha256"] == result["attack_execution"]["before_sha256"]
    assert result["recovery_verified"] is True


def test_visualization_attack_executes_child_process_and_recovers_configuration():
    scenario = {
        "scenario_id": "visualization-filter",
        "mode": "visual",
        "control": "Review visualization configuration integrity.",
        "result_basis": "PASS when configuration is detected and restored.",
    }

    result = _response_exercise(scenario)

    assert result["status"] == "PASS"
    assert result["attack_execution"]["executed"] is True
    assert "include_water from True to false" in result["attack_execution"]["stdout"]
    assert result["detected"] is True
    assert result["recovery_verified"] is True
