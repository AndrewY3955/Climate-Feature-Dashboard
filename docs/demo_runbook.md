# Dashboard demonstration runbook

## Before presenting

1. From the repository root, run `.\run_dashboard.ps1` on Windows or `sh ./run.sh` on macOS/Linux. The installed shell-profile shortcut is `run`.
2. Confirm the launcher reports successful validation and export, then open the local dashboard URL.
3. Confirm the **Project summary** appears and that the integrity panel does not show a warning.
4. Use the **Dashboard screen** dropdown to navigate among the ten views.

## Five-minute walkthrough

| Time | Dashboard screen and action | Talk track |
|---:|---|---|
| 0:00–0:40 | **Project summary**: introduce the research question, record coverage, and scope caveat. | “This is a small, heterogeneous reviewed dataset, not a representative industry sample or a total semiconductor footprint.” |
| 0:40–1:25 | **Environmental data**: select **Total energy consumption**, then inspect year, organization, unit basis, and source report filters. | “This TSMC observation is a reported total, not electricity-only; it includes electricity, natural gas, and diesel.” |
| 1:25–1:55 | **Measure guide**: compare water recycling, tap-water consumption, water intensity, energy, and emissions definitions. | “These measures use different units, reporting boundaries, and denominators; they cannot be combined or directly ranked.” |
| 1:55–2:25 | **Records & provenance** and **Reports & studies**: search an observation, then select a report. Try the registered report with no reviewed observations. | “The record keeps the source locator, original value, conversion, boundary, and limitation. An unobserved source is not shown as zero.” |
| 2:25–2:55 | **Integrity checks**: show pipeline validation, the trusted-file hash, and context-pack checks. | “A matching hash checks file bytes against a manifest; it does not establish source accuracy or protect a writable manifest.” |
| 2:55–3:45 | **Adversarial comparison**: select **Total energy consumption** and **Original source units**; review the event log. | “The controlled simulation changes 27,456 GWh to 41,184 GWh, a +50% alteration. It is not evidence of an actual attack.” |
| 3:45–4:15 | In comparison, select **Water recycled from recovery systems**. | “The simulation removes these records; the dashboard says removed, never zero. This demonstrates how selective omission can change a presentation.” |
| 4:15–4:40 | **Threat intelligence** and **Security controls**. | “ATT&CK items are scenario references only. The screen separates implemented prototype controls from manual and recommended controls.” |
| 4:40–5:00 | **Incident response**: choose a stage and point to its evidence/exit criteria. | “The response workflow emphasizes preserving evidence and validating the trusted branch before recovery.” |

## Interpretation guardrails

- The manipulated data are an intentionally generated classroom copy, not incident evidence.
- ATT&CK mappings are taxonomy/scenario references; there is no live threat feed, indicator of compromise, observed intrusion, or actor attribution.
- The reviewed observations do not support an industry footprint estimate, company ranking, or cross-metric sum.
- The browser dashboard is the implemented presentation prototype. Power BI is an optional alternate tool; the CSV pack can be imported if needed, but a native `.pbix`/`.pbip` is not required or claimed.
- The server binds to localhost only. Do not expose it to a network.

## Security terminology for the live demo

- **SHA-256 integrity check:** describe this as cryptographic hashing. It produces a one-way digest and detects byte-level changes only when compared with a trusted reference.
- **Encryption:** do not describe the SHA-256 feature as encryption. The current application does not encrypt/decrypt dataset files and does not implement encryption-key management. Encryption at rest, TLS configuration, and key custody are deployment controls discussed in the threat model, not application features delivered by this prototype.
- **Threat intelligence:** describe the three MITRE ATT&CK entries as defensive scenario mappings. They are not live threat feeds, indicators of compromise, observed attacks, or actor attribution.
- **Adversarial comparison:** emphasize that the altered dataset is a controlled classroom simulation, kept separate from the reviewed trusted observations.

## Offline fallback

Use the screenshots under `evidence/` only if they match the current dashboard version. State that they are static local-prototype captures, not a native Power BI report.
