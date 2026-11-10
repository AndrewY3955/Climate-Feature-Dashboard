# Semiconductor Climate Data Dashboard

A local, source-aware dashboard for exploring environmental observations related to semiconductor manufacturing and demonstrating how data manipulation can mislead users.

## Purpose

The project presents selected energy, water, and greenhouse-gas observations with their sources, units, years, geography, reporting boundaries, and limitations. A separate, intentionally altered dataset demonstrates why provenance and integrity checks matter.

This is a classroom proof of concept—not a complete industry footprint or company-ranking tool.

## Dashboard preview

The screenshots below show the local browser dashboard, not Power BI Desktop.

<p>
  <img src="evidence/trusted-overview.png" width="32%" alt="Trusted environmental data overview">
  <img src="evidence/measure-guide.png" width="32%" alt="Metric and unit guidance">
  <img src="evidence/provenance.png" width="32%" alt="Record provenance">
</p>
<p>
  <img src="evidence/integrity.png" width="32%" alt="Integrity verification view">
  <img src="evidence/adversarial-energy-source-units.png" width="32%" alt="Simulated energy and source manipulation">
  <img src="evidence/adversarial-water-omission.png" width="32%" alt="Simulated omission of water records">
</p>

See [dashboard evidence](evidence/README.md) for descriptions and interpretation notes.

## Key features

- Explore reviewed environmental observations and their source details.
- Inspect units, reporting boundaries, years, geography, and limitations.
- Validate input records and generate normalized datasets.
- Compare a trusted dataset with a separate, intentionally manipulated copy.
- Review SHA-256 integrity results, validation reports, and manipulation logs.
- Export a 13-table CSV model for optional Power BI import.

## Technology

- **Python** for data processing, validation, integrity checks, and the local server.
- **pandas** for tabular data processing.
- **HTML, CSS, and JavaScript** for the browser dashboard.
- **pytest and GitHub Actions** for automated testing.
- **CodeQL and dependency auditing** for repository security checks.

## Run the dashboard

You need **Python 3.10 or newer**. From the repository root, run the command for your terminal:

| Platform | Command |
| --- | --- |
| Windows PowerShell | `.\run.ps1` |
| Windows Command Prompt | `run.cmd` |
| macOS or Linux | `./run` |

The launcher prepares the data, starts the local server, and opens the dashboard. First launch may need internet access to install dependencies. Stop the server with **Ctrl+C**.

The dashboard is local-only and is intended for use in a browser on the same computer. See the [dashboard guide](docs/dashboard_local.md) for troubleshooting and optional shell shortcuts.

## How the data workflow works

1. Register sources and record-level observations, including source locators and original units.
2. Validate required fields, metric/unit pairs, source links, and record structure.
3. Generate the trusted dataset and integrity reference.
4. Keep synthetic test data and intentional manipulations separate from reviewed observations.
5. Review the trusted and controlled adversarial views in the dashboard.

A matching SHA-256 value checks bytes against a reference; it does not prove that a source claim is true, complete, or independently audited. See the [integrity and recovery guide](docs/integrity_and_recovery.md).

## Data and limitations

The reviewed dataset contains **seven source-checked observations** from company reports and US EPA sources. The observations use different years, geographies, reporting boundaries, and definitions; they cannot support an industry-wide estimate, trend, or company ranking.

Synthetic test data and manipulated records are separate from the reviewed observations and are not research findings. The project includes a **Power BI import-ready CSV model**, not a completed native `.pbix` or `.pbip` report. The browser dashboard is the primary interactive dashboard.

## Repository guide

**Research and deliverables**
- [Week 1 deliverables](docs/week1_deliverables.md)
- [Final project report](docs/final_report.md)
- [Literature review](docs/literature_review.md)
- [Project proposal](docs/proposal.md)
- [Project plan and status](docs/project_plan.md)

**Data and methods**
- [Data-source plan](docs/data_source_plan.md)
- [Data dictionary](docs/data_dictionary.md)
- [Source collection guide](docs/collecting_sources_and_data.md)
- [Requirement traceability](docs/requirement_traceability.md)

**Dashboard and security**
- [Dashboard setup and views](docs/dashboard_local.md)
- [Demo runbook](docs/demo_runbook.md)
- [System architecture](docs/system_architecture.md)
- [Threat model](docs/threat_model.md)
- [Incident response](docs/incident_response.md)
- [Integrity and recovery](docs/integrity_and_recovery.md)
- [Security policy](SECURITY.md)
- [Optional Power BI setup](docs/power_bi_setup.md)
- [Dashboard evidence screenshots](evidence/README.md)

## Tests

Install development dependencies and run the test suite:

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -W error::DeprecationWarning
```

GitHub Actions tests Python 3.10–3.14 on Ubuntu and Python 3.11 on Windows and macOS.
