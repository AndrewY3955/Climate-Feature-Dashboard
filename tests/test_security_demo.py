from __future__ import annotations

import pandas as pd

from climate_dashboard.security_demo import (
    SCENARIO_CATALOG,
    classify_comparability,
    run_security_demo,
)


def test_comparability_requires_matching_metric_and_unit():
    left = {
        "record_id": "A", "metric": "Water consumption", "unit": "m3",
        "data_year": "2024", "geography": "Taiwan", "facility": "Fab",
        "lifecycle_boundary": "Fab only", "calculation_method": "reported",
        "data_status": "reported",
    }
    right = {**left, "record_id": "B", "metric": "Water intensity"}
    result = classify_comparability(left, right)
    assert result["status"] == "NOT COMPARABLE"
    assert any("metric" in reason for reason in result["reasons"])


def test_comparability_marks_scope_difference_conditional():
    left = {
        "record_id": "A", "metric": "Water consumption", "unit": "m3",
        "data_year": "2024", "geography": "Taiwan", "facility": "Fab",
        "lifecycle_boundary": "Fab only", "calculation_method": "reported",
        "data_status": "reported",
    }
    right = {**left, "record_id": "B", "geography": "Global"}
    assert classify_comparability(left, right)["status"] == "CONDITIONAL"


def test_comparability_direct_only_when_dimensions_match():
    left = {
        "record_id": "A", "metric": "Water consumption", "unit": "m3",
        "data_year": "2024", "geography": "Taiwan", "facility": "Fab",
        "lifecycle_boundary": "Fab only", "calculation_method": "reported",
        "data_status": "reported", "company": "Company A",
    }
    right = {**left, "record_id": "B", "company": "Company B"}
    assert classify_comparability(left, right)["status"] == "DIRECTLY COMPARABLE"


def test_full_security_demo_passes_without_modifying_trusted_data():
    from climate_dashboard.security_demo import TRUSTED_FILE, _sha256

    before = _sha256(TRUSTED_FILE.read_bytes())
    result = run_security_demo()
    after = _sha256(TRUSTED_FILE.read_bytes())

    for item in result["tests"]:
        assert item["status"] == "PASS", (item["id"], item["detail"])
    for item in result["scenarios"]:
        if item["status"] != "TABLETOP ONLY":
            assert item["status"] == "PASS", (
                item["scenario_id"],
                item.get("validation_status"),
                item.get("detail"),
                item.get("phases"),
            )
    assert before == after
    assert len(result["scenarios"]) == len(SCENARIO_CATALOG)
    assert all(
        item["status"] == "PASS"
        for item in result["scenarios"]
        if item["status"] != "TABLETOP ONLY"
    )
    assert all(len(item["phases"]) == 6 for item in result["scenarios"])
    assert any(item["status"] == "TABLETOP ONLY" for item in result["scenarios"])

    for item in result["scenarios"]:
        evidence = item["attack_execution"]
        if item["status"] == "TABLETOP ONLY":
            assert evidence["executed"] is False
            continue
        assert evidence["executed"] is True, item["scenario_id"]
        assert evidence["exit_code"] == 0, item["scenario_id"]
        assert evidence["before_sha256"] != evidence["after_sha256"], item["scenario_id"]
        assert evidence["quarantine_sha256"] == evidence["after_sha256"], item["scenario_id"]
        assert evidence["recovery_sha256"] == evidence["before_sha256"], item["scenario_id"]
        assert evidence["network_access"] == "not used"
