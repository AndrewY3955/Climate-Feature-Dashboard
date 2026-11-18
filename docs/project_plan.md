# Practical four-week plan

## Completed project phases

1. **Research and data planning:** The proposal, source plan, data dictionary, five paper reviews, and seven source-checked observations are available. Paper 6 is supplemental dissertation background. The selected observations remain heterogeneous and cannot support an industry-wide estimate or company ranking.
2. **Threat model and response:** Assets, scenario, risk assessment, defender controls, integrity limitations, and the six-stage incident-response plan are documented. MITRE ATT&CK references are mapped as scenario context only, not as evidence of a real attack.
3. **Dashboard and adversarial demonstration:** The local dashboard-as-presentation has eleven selectable screens, including a new 17-topic environmental feature-coverage view. It distinguishes source-reported, partial, research-context, and uncollected features; summary, environmental data, measure guidance, provenance, reports/studies, threat references, controls, incident response, integrity, and adversarial comparison remain available. Report, metric, year, organization, and unit-basis filters are wired; missing observations are not shown as zero. Five deterministic manipulation events are logged separately from trusted records.
4. **Power BI preparation:** A repeatable exporter creates 13 import-ready tables containing trusted/adversarial data, source and paper registers, metric guidance, threat references, controls, response steps, hash/validation status, and model-validation results. Power BI Desktop was unavailable, so no native `.pbix`/`.pbip` is claimed.
5. **Security demonstration:** A standalone AES-256-GCM file-encryption utility uses scrypt-derived keys and authenticates ciphertext. It is separate from dashboard storage/transport and has automated wrong-passphrase and tamper tests.
6. **Final report and dashboard presentation:** The 31-section report, dashboard-screen demo runbook, and six existing browser screenshots are present. A separate 8–10 minute presentation outline now covers all required topics and all five papers. No slide deck or recording has been generated.

## Handoff status and remaining limitations

- The project owner has certified the five selected papers as eligible. The seven-record source-backed dataset is complete for the declared proof-of-concept scope; do not expand it with unverified or incomparable data. Add records only if the assignment requires broader coverage and suitable sources are reviewed.
- Final tests passed: 46 tests across Ubuntu Python 3.10–3.14, Windows Python 3.11, and macOS Python 3.11. Dependency security audit, CodeQL, and GitHub Pages static build also passed; the PR publish step was skipped, so production Pages remains unchanged.
- These changes remain on the open QA pull request and are not yet merged into main; the production GitHub Pages site is therefore unchanged.\n- Non-x86 CPU/platform combinations were not individually tested. The local service remains loopback-only by design.
- The interactive browser dashboard fulfills the dashboard requirement. A native Power BI report is optional unless specifically required by the instructor; the CSV export is available as an alternate workflow.
