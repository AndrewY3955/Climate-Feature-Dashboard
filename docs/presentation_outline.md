# Final presentation and live demonstration outline

## Executable attack-lab behavior

The current Security Demo Center runs each technical attack as a separate Python child process against a disposable file in a newly created temporary directory. The child process receives only the fixed scenario identifier and runs with the temporary lab directory as its working directory. Its script opens one fixed lab filename; it does not receive a production-data path, credentials, or a network target. This is an isolated local attack exercise, not an exploit against the deployed dashboard or an OS-level sandbox.

For each technical scenario, the defender records the trusted file's SHA-256, runs the attacker process, reads the changed target, compares the new digest with the trusted baseline, copies the altered bytes into a quarantine-evidence file, deletes the altered working target, restores the trusted baseline, and verifies the recovered digest. CSV scenarios also rerun the project's schema/source validation after recovery. The UI reports the child-process exit code and output, before/after/quarantine/recovery hashes, detection result, and incident-response phases.

**How to present this accurately:** show the attacker process output and hash transition first; then show the defender's detected digest mismatch, quarantined evidence, eradication, and recovery hash matching the original. The target is a disposable lab copy, not the live dashboard dataset. The payload scenario modifies a local transfer fixture, not live network traffic. The visualization scenario changes a lab configuration file, not the deployed dashboard's active configuration. Valid Accounts (T1078) remains tabletop-only because the application has no authentication service or account-audit telemetry.

A PASS means the isolated attack process executed, the modified target was detected by the SHA-256 comparison, quarantine and eradication completed, trusted bytes were restored, and applicable validation passed. It does not mean the production application resisted an external attacker.

This outline maps the assignment's presentation requirements to a concise, reproducible live demonstration. It is a speaker outline, not a claim that a slide deck or recording already exists.

## Security demonstration results: findings and interpretation

Use this section when presenting the one-click Security Demo Center output. These are the reported results from the demonstrated run; rerun the local demonstration before quoting them as the result of a later build.

### Execution summary

| Result | Reported value | Correct interpretation |
|---|---:|---|
| Overall demonstration | PASS | Every automated check and technical scenario in this run completed successfully. This is not a certification that the whole application is secure. |
| Trusted records | 7 | Seven reviewed records were included in the integrity and validation checks. |
| Security control tests | 6 / 6 passed | The listed dataset, digest, encryption, fresh-parameter, wrong-passphrase, and ciphertext-tampering checks passed. |
| Scenarios | 7 | Six technical simulations and one tabletop exercise were run. |
| Technical scenarios | 6 passed | The six controlled data/payload/configuration exercises produced the expected detection and recovery results. |
| Tabletop-only scenarios | 1 | Valid Accounts (T1078) was discussed and its response workflow exercised; no account-compromise detection was tested. |
| Incident-response phases | 6 per scenario | Preparation, Detection and Analysis, Containment, Eradication, Recovery, and Lessons Learned were represented in each scenario workflow. |
| Pairwise comparisons | 21 | Seven records produce 7 × 6 ÷ 2 = 21 unique pairs. All 21 were classified NOT COMPARABLE by the current rules. |

### What the six security tests establish

- **Schema and source validation — PASS:** the seven-record trusted dataset produced zero validation errors and zero warnings in this run. This checks the implemented schema and source rules; it does not independently validate the truth of the source reports.
- **SHA-256 manifest — PASS:** the actual digest matched the expected digest for the trusted file. SHA-256 is an integrity hash, not encryption. The comparison is only as trustworthy as the separately protected reference digest; a writable manifest stored beside writable data is not an independent trust anchor.
- **AES-256-GCM — PASS:** the standalone demonstration encrypted a temporary in-memory copy and recovered identical bytes after authenticated decryption. It did not encrypt dashboard storage, GitHub Pages, or network traffic.
- **Fresh salt and nonce — PASS:** two encryptions of the same input produced different salt/nonce headers, as expected for the demonstration.
- **Wrong passphrase — PASS:** authenticated decryption rejected the incorrect passphrase and did not return unauthenticated plaintext.
- **Ciphertext tampering — PASS:** changing one ciphertext byte caused AES-GCM authentication to fail.

### How to explain the seven scenarios

- **T1078 — Compromised contributor account (TABLETOP ONLY):** the scenario assumes an identity is compromised. The project has no login, MFA, authorization, or account-audit service, so it does not technically detect account compromise. The six response phases are a classroom walkthrough.
- **T1565.001 — Stored Data Manipulation:** four exercises alter a copied value, omit water records, remove source attribution, or change a unit. A fifth changes a synthetic visualization-filter configuration. They demonstrate why record-level baselines, provenance, unit/scope validation, and filter review matter.
- **T1565.002 — Transmitted Data Manipulation:** the transfer exercise changes bytes in a simulated payload and checks it against the sender-side digest. It is not a live network interception or transport-security test.
- **Recovery:** for the technical scenarios, altered working data is copied to a quarantine evidence file in the temporary lab directory, the altered working file is deleted, and trusted bytes are restored. The temporary directory, including quarantine evidence, is removed when the scenario ends. A matching restored digest and applicable schema validation show that this simulated recovery path worked; this is not a production backup/restore test.

### Comparability finding: 0 direct, 0 conditional, 21 not comparable

The audit compares every unique pair among seven observations. It requires matching metric and unit, then evaluates data year, geography, facility/organizational scope, lifecycle boundary, calculation method, and data status. Company identity may differ. The reported run found metric and/or unit mismatches in every pair, so no pair reached DIRECTLY COMPARABLE or CONDITIONAL.

**Say:** “The current seven-record dataset does not contain a like-for-like pair under our comparison rules. The dashboard therefore avoids presenting these unlike observations as a fair ranking.”

Do not say that the 21 results mean the audit failed, that the observations are invalid, or that no semiconductor companies can ever be compared. The result describes this dataset and the implemented comparison criteria. A larger dataset with aligned metrics, units, years, geography, scope, boundaries, methods, and status could produce comparable pairs.

### Simulation boundary and residual controls

All technical scenario changes occur in disposable files inside temporary directories; the trusted dataset and project files are not modified. The Valid Accounts exercise is tabletop-only. These are defensive classroom exercises, not live attacks, penetration tests, a production SOC, or a live threat feed. ATT&CK IDs are static technique references, not evidence of attribution or live detection.

The prototype does not deploy MFA, role-based access enforcement, central account/audit logging, independent manifest custody, production key management, immutable backups, or automated production recovery. AES-GCM is a standalone file demonstration. SHA-256 detects a difference only against a separately trusted reference.

## Recommended 8–10 minute sequence

| Slide / segment | Time | Required content | Evidence and speaker notes |
|---|---:|---|---|
| 1. Purpose and research question | 0:45 | Project purpose, research question, why semiconductor climate data need context | Use the proposal's question. Explain that the project evaluates transparent reporting and manipulation, not a global footprint estimate. |
| 2. Semiconductor climate features | 1:00 | Energy, electricity mix, grid intensity, water, GHG, process gases, node/mask layers, materials, packaging, location, waste, lifecycle and use phase | Show the feature-coverage view. Distinguish source-reported, partial, research context, and not collected. |
| 3. Five research papers | 1:30 | Five paper objectives, features/variables, environmental findings, limitations, dashboard relevance | Use the five-paper summary below. Emphasize different methods and that modeled/contextual results were not copied into the observation dataset. |
| 4. Data-source plan and validation | 1:00 | Five registered sources, seven observations, source years/data years, units, geography, boundaries, validation | Show Records & Provenance and Reports & Studies. Explain original units, conversion notes, and why unlike measures are not compared directly. |
| 5. Trusted dashboard | 1:00 | Accurate environmental view, measure guide, feature coverage, source transparency | Show OBS001 energy, then water measures and emissions. State the data is heterogeneous and not industry representative. |
| 6. Threat model and defender strategy | 1:00 | Assets, attackers, motivation, attack vectors, vulnerabilities, indicators, consequences, controls | Show Threat Intelligence and Security Controls. Explain ATT&CK is a static defensive mapping, not live threat detection. |
| 7. Integrity and encryption | 1:00 | Validation, SHA-256, audit/change evidence, AES-GCM encryption demo, control limitations | Show Integrity Checks. Then run the standalone encryption utility; demonstrate successful decryption and rejection of modified ciphertext. Do not claim dashboard storage or network encryption. |
| 8. Manipulated dashboard comparison | 1:15 | Numeric alteration, source-label removal, water-row omission; why unnoticed, conclusion/trust effects, detection/prevention, evidence | Show the adversarial comparison and expanded event analysis. State clearly that the manipulated branch is a controlled classroom simulation. |
| 9. Incident response and conclusion | 0:45 | Six response phases, limitations, findings, final lesson | Show Incident Response and finish with the required lesson quoted below. |

## Five selected research papers: presentation summary

1. **Kuo, Kuo, and Chen (2022):** Life-cycle assessment of nanoscale semiconductor manufacturing, including electricity, fuels, water, process gases, chemicals, materials, and waste across 20/30/40 nm cases. Supports showing process node, functional unit, mask layers, and lifecycle boundary. Limitations include a confidential single-manufacturer case and incomplete packaging/outsourced testing.
2. **Ruberti (2024):** Foundry-industry environmental trends from 2012–2021 using corporate disclosures and a manufacturing index. Shows absolute resource totals and normalized intensity can tell different stories. Coverage, company disclosures, and index assumptions limit comparability.
3. **Wang et al. (2023):** Compilation of water, energy, Scope 1/2 GHG, and ultrapure-water disclosures for semiconductor corporations. Useful for identifying relevant features and reporting denominators. It relies on corporate disclosures with different coverage and reporting periods.
4. **Ruberti (2023):** Environmental performance and eco-efficiency across six foundries, including energy, water, waste, and GHG indicators. Shows advanced technology or company size does not automatically imply lower per-unit impact. Selective disclosures, index assumptions, and incomplete Scope 3 constrain conclusions.
5. **Frost and Hua (2019):** Spatial and temporal modeling of direct and electricity-related water withdrawals and water scarcity. Supports geographic and watershed context. Results are modeled withdrawals, not direct company measurements, and depend on production and regional-factor assumptions.

Full citations, objectives, variables, findings, limitations, and dashboard relevance are in literature_review.md.

## Threat-model talking points

- **Assets:** original source reports, trusted observations, transformations, manifests, dashboard settings, adversarial copy, and final conclusions.
- **Actors:** malicious contributor/insider, attacker with a compromised account, vendor/source publisher, and accidental contributor error.
- **Scenario:** a contributor account is compromised; an attacker changes a numeric value, removes a source label, or omits water observations.
- **Defender:** preserve originals and protected backups, limit write access, review changes, validate units/provenance/feature coverage, compare trusted versions, and preserve logs.
- **Indicators:** hash mismatch against an independently protected reference, unexpected row/feature changes, blank or changed provenance, altered filters/axes, and unexplained validation warnings.
- **ATT&CK:** T1078, T1565.001, and T1565.002 are reference mappings only; no real intrusion or actor attribution is claimed.

## Six incident-response phases

1. Preparation
2. Detection and Analysis
3. Containment
4. Eradication
5. Recovery
6. Lessons Learned

Investigators preserve files and report versions, compare trusted and suspect records, inspect source and visualization changes, consult platform audit logs for supported attribution, and restore only from a protected validated baseline.

## Required closing lesson

> Reliable climate analysis requires more than accurate numbers. The data source, assumptions, lifecycle boundaries, feature selection, security controls, and visualization design must also be protected from manipulation.

## Presentation accuracy checklist

- Identify the reviewed dataset as seven source-reported observations, five registered source documents, and five selected journal papers.
- State that the dataset is heterogeneous and not representative of the semiconductor industry.
- Never call SHA-256 encryption.
- Describe AES-GCM as a standalone file-encryption demonstration, not dashboard-at-rest or network encryption.
- Describe ATT&CK entries as static scenario references, not a live feed.
- Label all altered values and omitted rows as an intentional simulation.
- Show the feature coverage view so the audience can see which features are only contextual or not collected.
- Do not claim a native Power BI report exists; the browser dashboard is the implemented prototype and the Power BI CSV pack is import-ready.
