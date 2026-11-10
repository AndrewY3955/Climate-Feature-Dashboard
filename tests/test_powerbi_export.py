import csv
from pathlib import Path

from climate_dashboard.adversarial import create_adversarial_copy
from climate_dashboard.pipeline import ROOT, run_pipeline
from climate_dashboard.powerbi_export import build_powerbi_pack


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def test_powerbi_pack_preserves_reviewed_data_and_relationships(tmp_path):
    reviewed_dir = tmp_path / "reviewed"
    powerbi_dir = tmp_path / "powerbi"
    run_pipeline(ROOT / "data" / "intake" / "observations_template.csv", reviewed_dir)
    create_adversarial_copy(reviewed_dir / "trusted_data.csv", reviewed_dir)

    result = build_powerbi_pack(reviewed_dir, powerbi_dir)

    assert result["status"] == "PASS"
    assert result["manifest_match"] is True
    assert result["table_count"] == 13
    assert len(_rows(powerbi_dir / "trusted_observations.csv")) == 7
    assert len(_rows(powerbi_dir / "adversarial_observations.csv")) == 4
    assert len(_rows(powerbi_dir / "manipulation_events.csv")) == 5
    assert len(_rows(powerbi_dir / "source_register.csv")) == 5
    assert len(_rows(powerbi_dir / "research_papers.csv")) == 5

    source_urls = {
        row["source_id"]: row["source_url"]
        for row in _rows(powerbi_dir / "source_register.csv")
    }
    exported_observations = _rows(powerbi_dir / "trusted_observations.csv")
    assert all(
        row["source_url"] == source_urls[row["source_id"]]
        for row in exported_observations
    )

    dimension = _rows(powerbi_dir / "record_dimension.csv")
    assert len(dimension) == 7
    omitted = [row for row in dimension if row["adversarial_present"] == "false"]
    assert {row["record_id"] for row in omitted} == {"OBS002", "OBS003", "OBS004"}
    assert all(row["trusted_present"] == "true" for row in dimension)

    threat_intel = _rows(powerbi_dir / "threat_intel_reference.csv")
    assert {row["technique_id"] for row in threat_intel} == {
        "T1078",
        "T1565.001",
        "T1565.002",
    }
    assert all("not" in row["coverage_status"].lower() or "scenario" in row["coverage_status"].lower()
               for row in threat_intel)

    integrity = _rows(powerbi_dir / "integrity_summary.csv")[0]
    assert integrity["validation_status"] == "PASS"
    assert integrity["trusted_manifest_match"] == "true"
    assert integrity["trusted_record_count"] == "7"

    assert len(_rows(powerbi_dir / "metric_guide.csv")) == 7
    assert len(_rows(powerbi_dir / "incident_response.csv")) == 6
    assert all(row["validation_status"] == "PASS"
               for row in _rows(powerbi_dir / "table_validation.csv"))
