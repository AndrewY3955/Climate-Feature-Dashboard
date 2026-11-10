"""Build a Power BI import pack from reviewed project artifacts."""

import argparse
import csv
import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
REVIEWED_DIR = ROOT / "data" / "processed" / "reviewed"
POWERBI_DIR = ROOT / "data" / "powerbi"

METRIC_GUIDANCE = {
    "Total energy consumption": (
        "Operational energy demand can drive indirect and direct emissions.",
        "TSMC company operations; includes purchased electricity, natural gas, and diesel.",
        "Do not label as electricity-only or compare with a generation emissions factor.",
    ),
    "Water recycled from recovery systems": (
        "Recycling can reduce freshwater demand, but volume alone does not show local scarcity.",
        "TSMC recovery systems; company-reported recycled volume.",
        "Not equivalent to water withdrawal or water consumption.",
    ),
    "Tap water consumption": (
        "Fab water demand can affect local water resources and treatment needs.",
        "TSMC Taiwan fabs only.",
        "Not a global company total; do not combine with recycling volume.",
    ),
    "Water consumption per 12-inch equivalent wafer mask layer": (
        "Production-normalized water use provides intensity context.",
        "TSMC company-reported wafer-equivalent intensity; photomask-count basis.",
        "Compare only with the same functional and normalization basis; not an absolute volume.",
    ),
    "Scope 1 and Scope 2 greenhouse-gas emissions": (
        "Operational and purchased-energy emissions contribute to reported GHG totals.",
        "Samsung Device Solutions division; Scope 1 plus market-based Scope 2.",
        "Division is broader than semiconductor foundry operations; not a single-fab value.",
    ),
    "Electricity-generation CO2-equivalent output emission rate": (
        "Regional grid generation mix affects the emissions associated with electricity.",
        "EPA eGRID 2023 CAMX subregion generation factor.",
        "Regional average, not a company procurement factor or company emissions total.",
    ),
    "Reported greenhouse-gas emissions": (
        "Reported sector emissions provide broad industrial context.",
        "EPA 2017 US electronics-manufacturing reporting facilities.",
        "Includes non-semiconductor electronics activity and reporting thresholds; not company-level.",
    ),
}

THREAT_INTEL = [
    {
        "reference_id": "ATTACK-T1078",
        "framework": "MITRE ATT&CK Enterprise",
        "technique_id": "T1078",
        "technique_name": "Valid Accounts",
        "relevance": "A compromised contributor account could be used to change trusted project files or report settings.",
        "project_evidence": "Threat-model scenario only; no account compromise or unauthorized activity was observed.",
        "coverage_status": "Scenario mapping; not detected activity",
        "confidence_note": "Official technique definition; no actor, campaign, or attribution claim.",
        "source_url": "https://attack.mitre.org/techniques/T1078/",
    },
    {
        "reference_id": "ATTACK-T1565.001",
        "framework": "MITRE ATT&CK Enterprise",
        "technique_id": "T1565.001",
        "technique_name": "Stored Data Manipulation",
        "relevance": "Changing a stored CSV value, source label, or feature set could alter a climate conclusion.",
        "project_evidence": "The separate classroom adversarial copy demonstrates value alteration, provenance removal, and omitted rows.",
        "coverage_status": "Scenario mapping; controlled demo only",
        "confidence_note": "Official technique definition; the project simulation is not a real incident.",
        "source_url": "https://attack.mitre.org/techniques/T1565/001/",
    },
    {
        "reference_id": "ATTACK-T1565.002",
        "framework": "MITRE ATT&CK Enterprise",
        "technique_id": "T1565.002",
        "technique_name": "Transmitted Data Manipulation",
        "relevance": "Data changed while moving between a source, pipeline, storage location, or reporting layer could mislead users.",
        "project_evidence": "Threat-model consideration only; the local prototype does not test a network or Power BI transfer path.",
        "coverage_status": "Scenario mapping; not tested",
        "confidence_note": "Official technique definition; no claim that this occurred in the project.",
        "source_url": "https://attack.mitre.org/techniques/T1565/002/",
    },
]

SECURITY_CONTROLS = [
    {
        "control_id": "CTRL-01",
        "control": "Preserve original source documents and source locators",
        "purpose": "Keep reported values traceable to publisher, page/table, period, unit, and boundary.",
        "control_type": "Preventive / detective",
        "implementation_status": "Implemented for supplied evidence",
        "evidence": "data/intake/incoming/; source_register.csv; reviewed observation locators",
        "limitation": "Source traceability does not independently assure the publisher's measurement.",
    },
    {
        "control_id": "CTRL-02",
        "control": "Validate schema, metric-unit pairs, numeric values, years, and required metadata",
        "purpose": "Reject malformed or unsupported trusted observations before export.",
        "control_type": "Preventive / detective",
        "implementation_status": "Implemented in Python pipeline",
        "evidence": "climate_dashboard/pipeline.py; validation_report.json; automated tests",
        "limitation": "Validation does not prove scientific accuracy or completeness.",
    },
    {
        "control_id": "CTRL-03",
        "control": "Generate SHA-256 manifests and compare trusted data to its reference",
        "purpose": "Detect byte-level changes when the reference digest is independently trusted.",
        "control_type": "Detective",
        "implementation_status": "Implemented; reference separation is manual",
        "evidence": "trusted_manifest.json; dashboard integrity view",
        "limitation": "A manifest writable by the same actor as the data can be replaced.",
    },
    {
        "control_id": "CTRL-04",
        "control": "Keep trusted and adversarial datasets on separate output paths",
        "purpose": "Prevent intentional classroom changes from contaminating trusted analysis.",
        "control_type": "Preventive",
        "implementation_status": "Implemented",
        "evidence": "data/processed/reviewed/trusted_data.csv and adversarial_data.csv",
        "limitation": "Separate paths do not provide operating-system access control.",
    },
    {
        "control_id": "CTRL-05",
        "control": "Run the local dashboard on loopback with fixed read-only routes",
        "purpose": "Limit the prototype's exposure and prevent browser requests from editing source data.",
        "control_type": "Preventive",
        "implementation_status": "Implemented for local prototype",
        "evidence": "climate_dashboard/dashboard.py; docs/dashboard_local.md",
        "limitation": "No login, authorization, TLS, remote hosting, or enterprise audit service.",
    },
    {
        "control_id": "CTRL-06",
        "control": "MFA, least privilege, role-based access, and protected audit logs",
        "purpose": "Reduce account compromise and constrain/trace write access in shared hosting.",
        "control_type": "Preventive / detective",
        "implementation_status": "Recommended; not deployed in this local project",
        "evidence": "docs/threat_model.md; docs/incident_response.md",
        "limitation": "Requires an identity and hosting platform outside this repository.",
    },
    {
        "control_id": "CTRL-07",
        "control": "Protect a known-good manifest and backup independently from data writers",
        "purpose": "Keep an integrity baseline and recovery copy outside a shared write path.",
        "control_type": "Preventive / detective / recovery",
        "implementation_status": "Recommended; independent trust anchor not configured",
        "evidence": "docs/threat_model.md; docs/incident_response.md",
        "limitation": "Local matching hashes alone cannot establish who changed a file or prove source truth.",
    },
    {
        "control_id": "CTRL-08",
        "control": "Review report filters, axis scales, units, sources, and missing features before publication",
        "purpose": "Detect presentation-layer manipulation that file hashes cannot reveal.",
        "control_type": "Detective / preventive",
        "implementation_status": "Documented manual review; no Power BI workspace deployed",
        "evidence": "docs/manipulation_comparison.md; docs/power_bi_setup.md",
        "limitation": "Requires reviewer access to the actual report/model and refresh history.",
    },
]

INCIDENT_RESPONSE = [
    {
        "phase": "Preparation",
        "objective": "Preserve known-good sources, datasets, manifests, schemas, owners, and recovery steps.",
        "actions": "Keep originals and protected backups; document provenance and boundaries; establish access controls and audit logging on any shared host.",
        "evidence_or_exit_criteria": "Known-good version, source register, access records, and response contacts are available.",
    },
    {
        "phase": "Detection and Analysis",
        "objective": "Scope data, provenance, code, model, and visualization changes without destroying evidence.",
        "actions": "Record the alert; preserve a copy; compare protected versions, hashes, IDs, coverage, units, filters, and audit logs; separate simulation from unexplained events.",
        "evidence_or_exit_criteria": "Change timeline, affected records/metrics/views, validation output, and attribution limits documented.",
    },
    {
        "phase": "Containment",
        "objective": "Stop publication and prevent further changes while preserving evidence.",
        "actions": "Mark output under review; restrict affected write access; preserve suspect files, manifests, report versions, logs, and screenshots.",
        "evidence_or_exit_criteria": "Affected outputs quarantined and evidence copies hashed and access-controlled.",
    },
    {
        "phase": "Eradication",
        "objective": "Remove unauthorized changes and address the root cause after preserving evidence.",
        "actions": "Review code, credentials, data sources, access paths, and report settings; restore provenance and approved assumptions; rotate or revoke compromised credentials where supported.",
        "evidence_or_exit_criteria": "Root cause and corrective changes reviewed; suspect credentials/access paths addressed.",
    },
    {
        "phase": "Recovery",
        "objective": "Restore a validated, reviewed trusted state before republishing.",
        "actions": "Restore from protected source; rerun validation/tests; verify integrity; refresh the report and inspect units, boundaries, filters, labels, and feature coverage.",
        "evidence_or_exit_criteria": "Independent review approves the recovered output and its supporting evidence.",
    },
    {
        "phase": "Lessons Learned",
        "objective": "Reduce recurrence and communicate corrected or withdrawn conclusions.",
        "actions": "Record impact and uncertainty; notify stakeholders as needed; add a targeted test, control, monitor, approval, backup, or review step.",
        "evidence_or_exit_criteria": "Follow-up actions have owners and the threat model, source plan, or response procedure is updated.",
    },
]


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.is_file():
        raise FileNotFoundError(f"Required Power BI input is missing: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames:
            raise ValueError(f"CSV has no header row: {path}")
        rows = list(reader)
        return list(reader.fieldnames), rows


def _write_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> int:
    if fields is None:
        if not rows:
            raise ValueError(f"Field names are required for an empty table: {path}")
        fields = list(rows[0])
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def _copy_table(
    source: Path, output_dir: Path, output_name: str
) -> tuple[str, int, list[dict[str, str]]]:
    fields, rows = _read_csv(source)
    _write_csv(output_dir / output_name, rows, fields)
    return output_name, len(rows), rows


def _metric_rows(trusted_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    metrics: dict[str, dict[str, str]] = {}
    for row in trusted_rows:
        metric = row["metric"]
        if metric not in METRIC_GUIDANCE:
            raise ValueError(f"No Power BI comparison guidance defined for metric: {metric}")
        climate, boundary, caution = METRIC_GUIDANCE[metric]
        if metric in metrics and metrics[metric]["unit"] != row["unit"]:
            raise ValueError(f"Metric has inconsistent units in trusted data: {metric}")
        metrics[metric] = {
            "metric": metric,
            "unit": row["unit"],
            "climate_relevance": climate,
            "primary_boundary": boundary,
            "comparison_rule": caution,
            "data_status": row["data_status"],
        }
    return [metrics[key] for key in sorted(metrics)]


def _record_dimension(
    trusted_rows: list[dict[str, str]],
    adversarial_rows: list[dict[str, str]],
    change_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    by_id: dict[str, dict[str, str]] = {}
    for row in trusted_rows:
        by_id[row["record_id"]] = row
    for row in adversarial_rows:
        by_id.setdefault(row["record_id"], row)
    changes_by_id: dict[str, list[str]] = {}
    for row in change_rows:
        changes_by_id.setdefault(row["record_id"], []).append(row["manipulation"])

    adversarial_ids = {row["record_id"] for row in adversarial_rows}
    result = []
    for record_id in sorted(by_id):
        row = by_id[record_id]
        result.append({
            "record_id": record_id,
            "metric": row["metric"],
            "company": row["company"],
            "data_year": row["data_year"],
            "unit": row["unit"],
            "trusted_present": str(any(r["record_id"] == record_id for r in trusted_rows)).lower(),
            "adversarial_present": str(record_id in adversarial_ids).lower(),
            "manipulation_summary": "; ".join(changes_by_id.get(record_id, [])),
        })
    return result


def build_powerbi_pack(
    reviewed_dir: str | Path = REVIEWED_DIR,
    output_dir: str | Path = POWERBI_DIR,
) -> dict:
    """Export reviewed observations and contextual tables for Power BI import."""
    reviewed_dir = Path(reviewed_dir)
    output_dir = Path(output_dir)

    table_counts: dict[str, int] = {}
    trusted_name, trusted_count, trusted_rows = _copy_table(
        reviewed_dir / "trusted_data.csv", output_dir, "trusted_observations.csv"
    )
    table_counts[trusted_name] = trusted_count
    adversarial_name, adversarial_count, adversarial_rows = _copy_table(
        reviewed_dir / "adversarial_data.csv", output_dir, "adversarial_observations.csv"
    )
    table_counts[adversarial_name] = adversarial_count
    change_name, change_count, change_rows = _copy_table(
        reviewed_dir / "adversarial_change_log.csv", output_dir, "manipulation_events.csv"
    )
    table_counts[change_name] = change_count
    source_name, source_count, source_rows = _copy_table(
        ROOT / "data" / "intake" / "sources_template.csv",
        output_dir,
        "source_register.csv",
    )
    table_counts[source_name] = source_count
    paper_name, paper_count, paper_rows = _copy_table(
        ROOT / "data" / "intake" / "papers_template.csv",
        output_dir,
        "research_papers.csv",
    )
    table_counts[paper_name] = paper_count

    trusted_ids = {row["record_id"] for row in trusted_rows}
    adversarial_ids = {row["record_id"] for row in adversarial_rows}
    if len(trusted_ids) != trusted_count:
        raise ValueError("Trusted Power BI export contains duplicate record IDs.")
    if len(adversarial_ids) != adversarial_count:
        raise ValueError("Adversarial Power BI export contains duplicate record IDs.")
    if not adversarial_ids.issubset(trusted_ids):
        raise ValueError("Adversarial records must be a subset of trusted record IDs.")
    unknown_change_ids = {row["record_id"] for row in change_rows} - trusted_ids
    if unknown_change_ids:
        raise ValueError(f"Manipulation log contains unknown record IDs: {sorted(unknown_change_ids)}")
    source_ids = {row["source_id"] for row in source_rows if row.get("source_id")}
    observation_source_ids = {row.get("source_id", "") for row in trusted_rows}
    missing_source_ids = observation_source_ids - source_ids
    if "" in observation_source_ids or missing_source_ids:
        raise ValueError(f"Trusted records reference missing source IDs: {sorted(missing_source_ids)}")

    source_by_id = {row["source_id"]: row for row in source_rows if row.get("source_id")}
    for row in trusted_rows:
        source_id = row.get("source_id", "").strip()
        observation_url = row.get("source_url", "").strip()
        registered_url = source_by_id[source_id].get("source_url", "").strip()
        parsed_url = urlparse(observation_url)
        if parsed_url.scheme != "https" or not parsed_url.netloc:
            raise ValueError(
                f"Trusted record {row.get('record_id')} has an invalid HTTPS source URL."
            )
        if observation_url != registered_url:
            raise ValueError(
                f"Trusted record {row.get('record_id')} source URL does not match "
                f"the registered URL for {source_id}."
            )

    paper_ids = [row.get("paper_id", "") for row in paper_rows]
    if len(paper_ids) != len(set(paper_ids)) or len(paper_ids) < 5:
        raise ValueError("Research register must contain at least five unique paper IDs.")

    guidance_rows = _metric_rows(trusted_rows)
    table_counts["metric_guide.csv"] = _write_csv(
        output_dir / "metric_guide.csv", guidance_rows
    )
    table_counts["threat_intel_reference.csv"] = _write_csv(
        output_dir / "threat_intel_reference.csv", THREAT_INTEL
    )
    table_counts["security_controls.csv"] = _write_csv(
        output_dir / "security_controls.csv", SECURITY_CONTROLS
    )
    table_counts["incident_response.csv"] = _write_csv(
        output_dir / "incident_response.csv", INCIDENT_RESPONSE
    )

    record_rows = _record_dimension(trusted_rows, adversarial_rows, change_rows)
    table_counts["record_dimension.csv"] = _write_csv(
        output_dir / "record_dimension.csv", record_rows
    )

    validation_path = reviewed_dir / "validation_report.json"
    manifest_path = reviewed_dir / "trusted_manifest.json"
    validation = json.loads(validation_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    digest = hashlib.sha256((reviewed_dir / "trusted_data.csv").read_bytes()).hexdigest()
    manifest_matches = digest == manifest.get("sha256")
    if validation.get("status") != "PASS":
        raise ValueError("Trusted data validation must pass before Power BI export.")

    summary = [{
        "project": "Climate-Feature Dashboard for Semiconductor Technology",
        "research_question": (
            "How can a provenance-aware dashboard communicate reported semiconductor-relevant "
            "energy, water, and GHG indicators while exposing source-scope differences and "
            "intentional manipulation?"
        ),
        "trusted_observation_count": trusted_count,
        "adversarial_observation_count": adversarial_count,
        "source_count": len(source_rows),
        "research_paper_count": len(paper_rows),
        "manipulation_event_count": change_count,
        "data_scope": (
            "Seven heterogeneous reported observations; not a representative industry sample "
            "and not suitable for ranking companies."
        ),
        "threat_intelligence_scope": (
            "MITRE ATT&CK reference mapping only; no live feed, indicators of compromise, "
            "observed incident, or actor attribution."
        ),
        "power_bi_status": "Import-ready CSV model; no PBIX/PBIP authored in this environment.",
    }]
    table_counts["project_summary.csv"] = _write_csv(
        output_dir / "project_summary.csv", summary
    )

    integrity_summary = [{
        "validation_status": validation.get("status", "UNKNOWN"),
        "validation_error_count": validation.get("error_count", ""),
        "validation_warning_count": validation.get("warning_count", ""),
        "trusted_record_count": trusted_count,
        "adversarial_record_count": adversarial_count,
        "manipulation_event_count": change_count,
        "trusted_sha256": digest,
        "manifest_sha256": manifest.get("sha256", ""),
        "trusted_manifest_match": str(manifest_matches).lower(),
        "interpretation": (
            "A matching local hash detects byte changes only relative to a trusted reference; "
            "it does not establish source accuracy."
        ),
    }]
    table_counts["integrity_summary.csv"] = _write_csv(
        output_dir / "integrity_summary.csv", integrity_summary
    )
    if not manifest_matches:
        raise ValueError("Trusted Power BI export hash does not match its manifest.")

    checks = [
        ("trusted-validation", "Trusted dataset validation", validation.get("status"), "PASS"),
        ("trusted-hash", "Trusted hash matches manifest", str(manifest_matches).lower(), "true"),
        ("trusted-ids", "Unique trusted record IDs", len(trusted_ids), trusted_count),
        ("adversarial-subset", "Adversarial IDs are a trusted subset", len(adversarial_ids - trusted_ids), 0),
        ("change-log-ids", "Change-log IDs resolve to trusted records", len(unknown_change_ids), 0),
        ("source-links", "Trusted source IDs resolve to source register", len(missing_source_ids), 0),
        ("research-papers", "Unique research-paper records", len(set(paper_ids)), len(paper_ids)),
        ("metric-guide", "Metrics have comparison guidance", len(guidance_rows), len({row["metric"] for row in trusted_rows})),
        ("incident-response", "Incident-response phases", len(INCIDENT_RESPONSE), 6),
        ("threat-references", "Threat references include source URLs", sum(bool(row["source_url"]) for row in THREAT_INTEL), len(THREAT_INTEL)),
    ]
    validation_rows = [
        {
            "check_id": check_id,
            "check": label,
            "actual": actual,
            "expected": expected,
            "validation_status": "PASS" if actual == expected else "FAIL",
        }
        for check_id, label, actual, expected in checks
    ]
    table_counts["table_validation.csv"] = _write_csv(
        output_dir / "table_validation.csv",
        validation_rows,
    )
    if any(row["validation_status"] != "PASS" for row in validation_rows):
        raise ValueError(f"Power BI pack validation failed; review {output_dir / 'table_validation.csv'}")
    return {
        "status": "PASS",
        "table_count": len(table_counts),
        "counts": table_counts,
        "trusted_sha256": digest,
        "manifest_match": manifest_matches,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Export reviewed data and context tables for Power BI.")
    parser.add_argument("--input-dir", type=Path, default=REVIEWED_DIR)
    parser.add_argument("--output-dir", type=Path, default=POWERBI_DIR)
    args = parser.parse_args()
    result = build_powerbi_pack(args.input_dir, args.output_dir)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
