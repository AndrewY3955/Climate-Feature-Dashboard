# Final presentation and live demonstration outline

This outline maps the assignment's presentation requirements to a concise, reproducible live demonstration. It is a speaker outline, not a claim that a slide deck or recording already exists.

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
