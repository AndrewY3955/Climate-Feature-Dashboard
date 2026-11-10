from hashlib import sha256
import json
from pathlib import Path

import pandas as pd
import pytest

from climate_dashboard.adversarial import create_adversarial_copy
from climate_dashboard.integrity import verify_manifest, write_manifest
from climate_dashboard.pipeline import run_pipeline, TRUSTED_FILE, MANIFEST_FILE, OUT_DIR


def test_trusted_manifest_verifies():
    run_pipeline()
    ok, expected, actual = verify_manifest(TRUSTED_FILE, MANIFEST_FILE)
    assert ok
    assert expected == actual


def test_tampering_is_detected(tmp_path):
    run_pipeline()
    tampered = tmp_path / "trusted_data.csv"
    df = pd.read_csv(TRUSTED_FILE)
    df.loc[0, "value"] = float(df.loc[0, "value"]) + 1
    df.to_csv(tampered, index=False)
    ok, expected, actual = verify_manifest(tampered, MANIFEST_FILE)
    assert not ok
    assert expected != actual


def test_manifest_rejects_dataset_name_mismatch(tmp_path):
    dataset = tmp_path / "trusted.csv"
    dataset.write_text("record_id,value\nOBS001,10\n", encoding="utf-8")
    manifest = tmp_path / "manifest.json"
    write_manifest(dataset, manifest, "test")

    with pytest.raises(ValueError, match="file name does not match"):
        verify_manifest(tmp_path / "renamed.csv", manifest)


@pytest.mark.parametrize(
    "payload",
    [
        [],
        {"file": "trusted.csv", "sha256": "not-a-hash"},
        {"file": "other.csv", "sha256": "0" * 64},
        {"sha256": "0" * 64},
    ],
)
def test_manifest_rejects_invalid_structure_or_digest(tmp_path, payload):
    dataset = tmp_path / "trusted.csv"
    dataset.write_text("record_id,value\nOBS001,10\n", encoding="utf-8")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError):
        verify_manifest(dataset, manifest)


def test_manifest_rejects_invalid_json(tmp_path):
    dataset = tmp_path / "trusted.csv"
    dataset.write_text("record_id,value\nOBS001,10\n", encoding="utf-8")
    manifest = tmp_path / "manifest.json"
    manifest.write_text("{invalid", encoding="utf-8")

    with pytest.raises(ValueError, match="Unable to read a valid integrity manifest"):
        verify_manifest(dataset, manifest)


def test_adversarial_copy_is_separate_and_documented():
    run_pipeline()
    changes = create_adversarial_copy()
    assert (OUT_DIR / "adversarial_data.csv").exists()
    assert (OUT_DIR / "adversarial_change_log.csv").exists()
    assert len(changes) >= 2
    trusted = pd.read_csv(TRUSTED_FILE)
    adversarial = pd.read_csv(OUT_DIR / "adversarial_data.csv")
    assert len(adversarial) < len(trusted)
    ok, _, _ = verify_manifest(OUT_DIR / "adversarial_data.csv", OUT_DIR / "adversarial_manifest.json")
    assert ok


def test_reviewed_adversarial_branch_does_not_modify_trusted_input(tmp_path):
    intake_file = tmp_path / "observations.csv"
    intake_file.write_bytes(Path("data/intake/observations_template.csv").read_bytes())
    trusted_dir = tmp_path / "reviewed"
    run_pipeline(input_file=intake_file, output_dir=trusted_dir)
    trusted_file = trusted_dir / "trusted_data.csv"
    trusted_hash = sha256(trusted_file.read_bytes()).hexdigest()
    intake_hash = sha256(intake_file.read_bytes()).hexdigest()

    changes = create_adversarial_copy(
        trusted_file=trusted_file,
        output_dir=tmp_path / "adversarial",
    )

    altered = pd.read_csv(tmp_path / "adversarial" / "adversarial_data.csv")
    log = pd.read_csv(tmp_path / "adversarial" / "adversarial_change_log.csv")
    adversarial_manifest = tmp_path / "adversarial" / "adversarial_manifest.json"
    assert {"ADV-001", "ADV-002", "ADV-003"}.issubset(set(log["change_id"]))
    assert len(altered) < 7
    assert not altered["metric"].str.contains("water", case=False).any()
    assert sha256(trusted_file.read_bytes()).hexdigest() == trusted_hash
    assert sha256(intake_file.read_bytes()).hexdigest() == intake_hash
    assert len(changes) == len(log)
    assert verify_manifest(tmp_path / "adversarial" / "adversarial_data.csv", adversarial_manifest)[0]
