# Controlled manipulation comparison

## Evidence boundary

This is a reproducible, local classroom simulation, not a real attack or evidence of an actual incident. The trusted source-backed file is generated from the reviewed intake at `data/processed/reviewed/trusted_data.csv`. The separate manipulated copy and event log are generated at `data/processed/reviewed/adversarial_data.csv` and `data/processed/reviewed/adversarial_change_log.csv`. Do not use the adversarial file for trusted analysis.

The generator changes a copy only. It does not edit the intake CSV or trusted output. The adversarial manifest hashes the manipulated artifact itself; detection requires comparing it with the separately protected trusted reference and reviewing the change log.

## Recorded changes

| Change | Trusted state | Manipulated state / method | Why it may go unnoticed | Climate-conclusion and trust effect | Detection control | Prevention control | Incident-response evidence |
|---|---|---|---|---|---|---|---|
| ADV-001 — numeric alteration | OBS001 reports 27,456,000 MWh total energy (27,456 GWh). | The generator multiplies the numeric value by 1.5, producing 41,184,000 MWh (41,184 GWh). | A plausible-looking number can pass a casual visual review when the reader does not open the source or compare the trusted version. | The displayed total is overstated by 50%; the mismatch between report and source undermines confidence in the dashboard. | Compare row-level values and the file digest with an independently protected trusted baseline; inspect the event log. | Restrict write access, require second-person review, preserve versioned source records, and protect the reference manifest separately. | Trusted/adversarial CSVs, TSMC report p. 120, hashes, version history, approval records, and platform audit logs. |
| ADV-002 — source-label removal | OBS005 identifies the Samsung Electronics Sustainability Report 2026. | The generator blanks the human-readable source_name while retaining source_id and source_url. | The remaining source ID and URL make the record appear partly traceable, so the missing publisher label may be overlooked. | The value is unchanged, but the evidence is harder to interpret and verify quickly; incomplete attribution weakens trust. | Validate required source labels and compare metadata with the source register and trusted record. | Require complete provenance fields, flag blank labels, and review metadata changes before publication. | Before/after record diff, source register, validation warning, source PDF, and approved change record. |
| ADV-003 — water-feature omission | OBS002, OBS003, and OBS004 represent recycled water, Taiwan-fab tap-water consumption, and normalized wafer-layer water intensity. | The generator removes all three water rows from the adversarial copy; the copy contains four records rather than seven. | A simplified or filtered view can omit a category; readers may mistake missing water records for an absence of water impact. | The view loses all water coverage and shifts attention toward energy and emissions; selective omission creates an incomplete climate narrative even though remaining values are unchanged. | Compare expected record IDs, row counts, and feature coverage; inspect filters, the change log, and the trusted baseline. | Maintain a feature-coverage register, require review of omissions and filters, and prevent adversarial files from replacing trusted data. | Trusted/adversarial CSV diff, expected feature inventory, dashboard filter settings, screenshots, change log, and repository history. |

The exact before/after values and record IDs are generated in `adversarial_change_log.csv`; the table above summarizes the current deterministic manipulation rules. Regenerate the artifacts after changing the trusted dataset and update this analysis from the new log.

## Comparison findings

The numeric edit changes an energy total but does not establish a real-world increase; it is a deliberately altered single record. The missing water rows remove all water coverage from this seven-record demonstration. The source-label edit weakens human-readable provenance but does not fully unlink the observation because its source ID and URL remain. Together, these demonstrate data-value, completeness, and presentation risks. They do not demonstrate manipulation of a real Power BI report, hidden filters, or changed visual scales.

The dataset is heterogeneous and does not support ranking TSMC, Samsung, eGRID, or the EPA sector total. The meaningful lesson is that integrity checks and visible provenance help reviewers detect tampering but cannot make unlike boundaries comparable or prove that publisher-reported values are scientifically correct.

## Captured dashboard evidence

The current local browser prototype was recaptured after the multi-screen dashboard refactor and saved under `evidence/`:

- `trusted-overview.png` - reviewed energy observation, unit, source, and limitation.
- `measure-guide.png` - measure definitions and comparison cautions.
- `provenance.png` - record-level source and conversion information.
- `integrity.png` - validation and manifest status.
- `adversarial-energy-source-units.png` - trusted 27,456 GWh versus simulated 41,184 GWh.
- `adversarial-water-omission.png` - removed water rows shown as removed, not zero.

These are screenshots of the local browser dashboard, not a native Power BI report. Power BI Desktop was unavailable; no `.pbix`/`.pbip` or Power BI screenshot is claimed. The import-ready CSV model and report design are documented in [`power_bi_setup.md`](power_bi_setup.md).
