# Climate-Feature Dashboard for Semiconductor Technology

## 1. Title Page

**Final Project Report**
**Climate-Feature Dashboard for Semiconductor Technology**
Course project on climate literacy, threat intelligence, cybersecurity, data integrity, and incident response
Prepared: October 20, 2026

## 2. Abstract or Executive Summary

This project examines how a provenance-aware dashboard can communicate reported semiconductor-relevant energy, water, and greenhouse-gas (GHG) indicators without implying that unlike sources are directly comparable. It also demonstrates how a separate, intentionally manipulated dataset can change what users see. The project combines five full-text-reviewed journal research papers, five registered data sources, seven report-checked observations, a Python validation and hashing pipeline, a local browser dashboard, an adversarial comparison, and an import-ready Power BI CSV model.

The observations cover TSMC operational energy and water measures, Samsung Electronics Device Solutions Scope 1 and market-based Scope 2 emissions, an EPA eGRID regional electricity-generation factor, and an EPA electronics-manufacturing sector total. They differ in year, geography, organizational boundary, metric definition, and unit. They are not a representative semiconductor-industry sample and do not support a company ranking or an industry-wide footprint estimate. The raw pipeline demonstration data remain synthetic and are not treated as research findings.

The adversarial branch records five events across three manipulation types: a 50% increase to one energy value, removal of a human-readable source label, and removal of three water records. The dashboard and Power BI model identify missing observations as removed rather than zero. MITRE ATT&CK references provide a defensive scenario taxonomy only; there is no live threat feed, indicator of compromise, observed intrusion, or actor attribution.

The key finding is that trustworthy climate communication depends on more than correct numeric values. Provenance, units, time periods, feature coverage, system boundaries, assumptions, security controls, and visualization choices must also be visible and protected. A passing schema check or matching local hash supports file integrity against a reference; neither proves that a publisher's claim is true or complete.

## 3. Introduction

Semiconductor devices enable computing, communications, transport, industrial control, and data-center services. Their production depends on complex fabrication processes, specialized materials, energy, water, and supply chains. Environmental indicators are reported at different levels—from individual products and process nodes to factories, corporate divisions, and national sectors—so a dashboard that places numbers next to one another can create a misleading comparison if it hides those differences.

The project therefore treats data integrity and data interpretation as linked concerns. A dashboard may mislead because a value was changed, but it can also mislead when a row is omitted, a source is hidden, a reporting boundary shifts, or a chart encourages an invalid comparison.

## 4. Project Purpose

The purpose is to build a traceable, locally runnable dashboard workflow that:

- presents reviewed semiconductor-relevant environmental observations with their source, unit, year, geography, boundary, and caveat;
- separates source-backed observations from synthetic test data and intentional adversarial changes;
- validates schema and metric-unit combinations, records a SHA-256 reference, and exposes integrity status; and
- shows how value, provenance, and feature-completeness manipulation can change interpretation.

This is a classroom prototype, not an enterprise-secured service, scientific inventory, or completed native Power BI report.

## 5. Research Question

**How can a provenance-aware dashboard communicate reported energy, water, and greenhouse-gas indicators relevant to semiconductor manufacturing while making differences in source scope and intentional data manipulation visible to users?**

The project evaluates transparency and workflow behavior, not semiconductor-sector performance or causal climate effects.

## 6. Background on Semiconductor Technology

Semiconductor fabrication converts patterned wafers through repeated deposition, lithography, etching, cleaning, doping, and polishing steps. A wafer may pass through many process layers; the exact process, technology node, product, yield, facility, and production mix affect required resources. Fabrication uses electricity and fuels for equipment and facility systems, ultrapure and other water streams for cleaning and process support, and specialty chemicals and gases. Packaging, testing, transport, and chip use can add further life-cycle impacts.

Consequently, a total reported by a company, an intensity per wafer-equivalent, and a product life-cycle assessment answer different questions. Process-node labels alone do not establish which product has lower total or per-functional-unit environmental impact.

## 7. Background on Semiconductor Environmental Impacts

Electricity demand can contribute indirect GHG emissions depending on grid generation and contractual accounting; on-site fuels and process gases can contribute direct emissions. Water withdrawal, consumption, recycling, and wastewater discharge have distinct definitions. Local scarcity depends on geography, timing, watershed conditions, and return flows, so a water volume is not itself a scarcity score. Materials, hazardous waste, packaging, and use-phase electricity can also matter across the life cycle.

The reviewed literature finds that absolute resource totals and normalized indicators can move differently. Scope, denominator, coverage, and method must accompany any environmental value. The project's intake contains no comparable facility-level process-gas inventory, water-stress index, packaging footprint, or product life-cycle assessment.

## 8. Literature Review

Five scholarly journal research articles were reviewed in full text. Paper 2 was reviewed from rendered page images because the supplied PDF has no embedded text. A sixth uploaded work, Boyd's doctoral dissertation, is treated as supplemental background and not counted among the five journal papers. The project owner certified Papers 1-5 as eligible under the assignment requirements on October 20, 2026; this records the owner's confirmation and is not an independent audit of each journal's peer-review process. Detailed methods, findings, and limitations are in [`literature_review.md`](literature_review.md).

Across the papers, life-cycle assessment, corporate disclosure analysis, production-normalized intensity, and spatial water-scarcity modeling address different questions. Findings motivate the dashboard's unit and scope cautions; none of the papers' modeled or aggregated results has been copied into the seven-observation intake dataset.

## 9. Summary of the Five Selected Research Papers

| Paper | Objective and feature | Data/method | Main finding | Key limitation and dashboard use |
|---|---|---|---|---|
| Kuo, Kuo, and Chen (2022) | Life-cycle impacts for embedded nonvolatile memory across 20, 30, and 40 nm cases | 2018-2020 data from two factories; electricity, fuels, water, gases, chemicals, materials, and waste; SimaPro/ReCiPe assessment | The 20 nm case has lower impacts than the 30/40 nm cases; manufacturing electricity and wafer use are important contributors | Confidential single-manufacturer/product case; packaging and outsourced testing are excluded; some percentage statements are unclear. Supports showing functional unit, process node, and boundary without generalizing. |
| Ruberti (2024) | Foundry-industry environmental trends and manufacturing-index intensity | Company disclosures, 2012-2021; six foundries in common-index analysis; approximate 30-mask-layer conversion | Absolute energy and water increased while per-index energy and water were broadly stable; Scope 1/2 GHG per index declined | Disclosure coverage and comparability vary; index depends on assumptions; incomplete Scope 3 and F-GHG coverage. Supports separating totals from normalized trends. |
| Wang et al. (2023) | Compile semiconductor-company water, energy, and GHG reporting | CSR/ESG data for 28 corporations; denominator varies by indicator; UPW and normalized data available for subsets | Reports 2021 totals for 27 companies for water and energy and 26 for GHG | Disclosure-derived aggregates with different coverage and periods, not independently measured or fully harmonized. Supports visible denominator and coverage notes. |
| Ruberti (2023) | Compare environmental performance and eco-efficiency across six foundries | CSR-derived energy, water, waste, revenue, production, and emissions; common index assumes about 45 mask layers | Company size, revenue, or advanced technology does not consistently imply lower per-unit environmental impacts | Selective reporting, six-company sample, index assumptions, and incomplete Scope 3. Supports resisting simplistic technology or company rankings. |
| Frost and Hua (2019) | Quantify geographic and temporal interaction of semiconductor water use and scarcity | Q4 2016 production records, facility geolocation, modeled direct and electricity-related water, and AWaRe factors | Electricity-related withdrawals dominate in many cases; estimated production overlaps water-scarce watersheds | Modeled withdrawals are not measured consumption; assumptions and a 1,021/1,020 record-count discrepancy are reported. Supports distinguishing direct and electricity-related water and labeling modeled estimates. |

Full citations and the supplemental dissertation summary appear in Section 31 and [`literature_review.md`](literature_review.md).

## 10. Data-Source Plan

The source register contains five sources. Four sources are linked to the seven current observations; the Intel report is registered as a candidate source but no observation has been extracted from it.

| Source | Use in this project | Coverage and limitation |
|---|---|---|
| TSMC 2024 Sustainability Report | Four 2024 energy/water observations | Company/recovery-system totals and Taiwan-fab subset; values are company-reported and boundaries differ by metric. |
| Intel 2025-26 Corporate Responsibility Report | Registered candidate source | No values were extracted; a table, unit, period, boundary, and page locator must be reviewed before adding records. |
| Samsung Electronics Sustainability Report 2026 | 2024 Device Solutions Scope 1 plus market-based Scope 2 GHG | Division-level, not one semiconductor fab or foundry-only. |
| US EPA eGRID Summary Tables 2023 | CAMX regional generation CO2e rate | Rounded regional grid factor, not a company procurement factor. |
| US EPA GHGRP Electronics Manufacturing profile | 2017 sector emissions | Includes electronics activity beyond semiconductors and reporting thresholds; not company-specific. |

The register also records publication year, data year, geography, boundary, reliability evidence, limitation, and validation method in `data/intake/sources_template.csv`. Source-specific page/table locators and original units are preserved in `data/intake/observations_template.csv`.

## 11. Description of Selected Technological Features

| Feature/measure | Current observation | Interpretation |
|---|---|---|
| Manufacturing energy | TSMC reported total energy, 2024 | Includes purchased electricity, natural gas, and diesel; not electricity-only. |
| Water recovery | TSMC recovered/recycled water, 2024 | Recycled volume, not withdrawal or consumption. |
| Facility water demand | TSMC Taiwan-fab tap-water consumption, 2024 | Regional subset, not company-wide. |
| Production-normalized water intensity | TSMC water per 12-inch equivalent wafer mask layer, 2024 | Intensity on the report's photomask-count basis; not an absolute volume. |
| Operational GHG | Samsung Device Solutions Scope 1 plus market-based Scope 2, 2024 | Division aggregate with a broader boundary than foundry operations. |
| Electricity carbon context | EPA CAMX eGRID output rate, 2023 | Regional generation factor; cannot be substituted for a company's emissions. |
| Sector GHG context | EPA electronics manufacturing, 2017 | Sector includes non-semiconductor facilities and is not comparable with the Samsung division total. |

Process node, packaging, manufacturing yield, water scarcity, fluorinated process gases, and life-cycle impacts are important features in the research literature but do not have comparable source-backed observations in the current seven-row dataset.

## 12. Data Collection Methodology

Original PDFs were retained in `data/intake/incoming/`. For each accepted observation, the reviewer checked publisher/report identity, reporting period, metric definition, value, unit, geography and reporting boundary against the cited PDF page/table. The intake record preserves the source-reported value/unit, normalized value/unit when converted, conversion explanation, source URL and locator, data status, uncertainty note, and limitation.

No estimate was inserted to fill a gap. The source-backed intake remains separate from `data/raw/environmental_data.csv`, a synthetic 24-row pipeline demonstration. Literature aggregates and modeled estimates are discussed as context only and are not merged into the observations.

## 13. Data Validation Methodology

The pipeline accepts columns in arbitrary order, trims header whitespace/BOM, validates required columns, unique record IDs, nonblank required metadata, finite nonnegative numeric values, integer years, allowed data status, and registered metric-unit pairs. It writes normalized columns, a validation report, and a SHA-256 manifest. The launcher then generates a separate adversarial copy and the Power BI exporter checks record uniqueness, adversarial ID subset, manipulation-log linkage, source-register linkage, paper-register uniqueness/count, metric guidance coverage, six response stages, and trusted-hash agreement.

The reviewed validation report returned **PASS, 7 rows, 0 errors, 0 warnings**. The Power BI export returned **PASS across 13 tables**, with 10 cross-table validation checks. These checks demonstrate workflow consistency; they do not prove source truth, completeness, representative sampling, or comparability. The digest is meaningful only against an independently protected reference.

## 14. Dashboard Architecture

The flow is: preserved source PDFs and intake registers → reviewed observations → schema/unit validation and normalization → trusted CSV and manifest → separate adversarial copy and event log → local browser dashboard and Power BI import pack. The default synthetic input and its outputs remain a separate branch.

The architecture, trust boundaries, and file responsibilities are documented in [`system_architecture.md`](system_architecture.md). The local prototype binds to `127.0.0.1`, serves fixed read-only routes, and does not implement cloud identity, a remote data service, or a native Power BI model.

## 15. Secure Dashboard Design

Implemented controls include explicit source metadata, record IDs, unit/period/geography/boundary/limitation display, metric-unit validation, separate trusted and adversarial paths, a SHA-256 manifest, validation results, and a loopback-only local server with fixed routes and response headers. The dashboard has trusted overview, measure guide, provenance, environmental feature coverage, integrity, and adversarial comparison views. Values are not aggregated across unlike metrics; omitted records are shown as removed rather than zero. A separate AES-256-GCM utility demonstrates authenticated file encryption, but is not integrated into dashboard storage or transport.

The Power BI import model adds source, literature, metric, threat-reference, control, incident-response, integrity, and project-summary tables. It remains a CSV model, not an authored or deployed Power BI report. MFA, role-based access, encryption/key management, centralized audit logging, separate manifest custody, and platform workspace controls are recommendations, not implemented features.

## 16. Threat Model

Assets include source documents, observation data, conversion rules, code/dependencies, manifests/backups, Power BI model and visuals, the adversarial log, and conclusions derived from the evidence. Relevant actors include a malicious insider/contributor, an external actor using a compromised account, a publisher providing selective disclosures, and an unintentional contributor error. Motivations include influencing a climate conclusion, concealing an unfavorable feature, damaging confidence, or disrupting the project.

Threats include data-value changes, source removal, feature omission, invalid conversions, report filter/axis edits, replacement of both data and its manifest, and selective or incomplete publisher disclosure. The qualitative risk register, indicators, residual risks, and controls are in [`threat_model.md`](threat_model.md).

## 17. Attacker Scenario

A contributor account with write access to shared project materials is assumed compromised. The scenario actor seeks to influence interpretation by changing an energy value, obscuring source identity, or hiding water records; a report editor could also change a filter or label. The local exercise reproduces only the first three data-level behaviors on a separate copy as a controlled classroom simulation. It does not exploit software, compromise an account, alter an actual Power BI report, or evidence a real attack.

MITRE ATT&CK Enterprise references T1078 (Valid Accounts), T1565.001 (Stored Data Manipulation), and T1565.002 (Transmitted Data Manipulation) classify scenario-relevant behavior. They are taxonomy references, not an active threat feed, actor indicators, or attribution.

## 18. Defender Strategy

A data steward preserves sources, validates transcriptions and conversions, and reviews pipeline results. A report reviewer checks metric selection, units, source, geography, boundary, filters, labels, chart scales, and feature coverage before publication. A response lead preserves suspect artifacts, compares them with independently protected known-good data, coordinates access changes, and approves restoration. In shared hosting, defenders should enforce MFA, least privilege, role separation, change approval, protected backups, and platform audit logging.

These are project responsibilities and recommendations; identities, remote access controls, and cloud audit services have not been configured in this local prototype.

## 19. Data-Integrity Controls

| Control | Status | Detects/prevents | Residual limitation |
|---|---|---|---|
| Original source preservation and page locators | Implemented for supplied files | Loss of provenance; transcription review | Publisher's measurement is not independently assured. |
| Schema, unit, year, and required-field validation | Implemented and tested | Malformed records and unsupported metric-unit pairs | Does not detect valid-looking but incomplete or inaccurate source claims. |
| SHA-256 manifest | Implemented | Byte changes relative to trusted reference | Reference must be independently protected; hash does not establish identity or truth. |
| Separate trusted/adversarial outputs | Implemented | Accidental mixing of training manipulation with trusted analysis | Local paths do not impose operating-system access control. |
| Loopback-only, read-only local dashboard | Implemented | Remote exposure and browser-side file writes | No authentication, TLS, authorization, or enterprise audit. |
| Source-register linkage in Power BI export | Implemented and tested | Observations with unresolved source IDs | Publisher identity and source reliability still require human review. |
| MFA, least privilege, access audit, protected backups | Recommended | Account misuse and recovery gaps | Not deployed; requires shared hosting controls. |
| Filter/axis/label/report-version review | Documented manual review | Visualization-only manipulation | No native Power BI report/workspace is included. |\n| AES-256-GCM authenticated file-encryption demo | Implemented as a standalone utility and tested | Demonstrates confidentiality and ciphertext tamper rejection | Does not encrypt dashboard storage, GitHub Pages content, network traffic, or production backups; passphrase/key custody remains external. |

## 20. Incident-Response Process

The response plan follows six stages: **Preparation** (preserve sources and protected baseline); **Detection and Analysis** (record hashes, compare versions, inspect rows, units, sources, model and filters); **Containment** (stop publishing, restrict affected access, preserve evidence); **Eradication** (remove unauthorized edits and address access/root-cause weaknesses after evidence preservation); **Recovery** (restore protected state, revalidate, rerun tests, inspect report and obtain independent approval); and **Lessons Learned** (record impact and uncertainty, notify stakeholders if needed, improve tests/controls, and update plans).

Investigators should retain source copies, record-level diffs, manifests, validation reports, report/model versions, refresh history, approved changes, identity logs, and screenshots. Local file timestamps or an account event alone do not prove the identity or intent of a human actor. Full procedures and evidence-to-question mapping appear in [`incident_response.md`](incident_response.md).

## 21. Accurate Dashboard Analysis

The dashboard is the project's presentation surface, organized into eleven navigable views: project summary, environmental data, measure guide, environmental feature coverage, records and provenance, reports and studies, threat references, security controls, incident response, integrity checks, and adversarial comparison. Dropdowns select reports, measures, years, organizations, and original-versus-standardized units. Each selected measure is shown as an individual record, not a sum or company ranking. Captured views are [trusted overview](../evidence/trusted-overview.png), [measure guide](../evidence/measure-guide.png), [provenance](../evidence/provenance.png), and [integrity](../evidence/integrity.png). The feature coverage view maps every rubric feature to its evidence status and limitations; see [environmental feature coverage](environmental_feature_coverage.md).

The trusted export validated with seven rows and no validation warnings. The browser prototype is available via the documented `run` command and is distinct from Power BI Desktop. Screenshots in `evidence/` are for the local browser prototype and must not be described as Power BI screenshots.

## 22. Manipulated Dashboard Analysis

The adversarial copy is generated only from the trusted reviewed CSV and is stored separately. The [energy comparison screenshot](../evidence/adversarial-energy-source-units.png) and [water-omission screenshot](../evidence/adversarial-water-omission.png) show the actual local browser prototype. Five logged events cover:

- **ADV-001:** OBS001 total energy changes from 27,456,000 MWh (27,456 GWh) to 41,184,000 MWh (41,184 GWh), a deliberate 50% increase.
- **ADV-002:** OBS005's human-readable Samsung source name is blanked; its source ID and URL remain, so provenance is weakened rather than fully removed.
- **ADV-003:** OBS002, OBS003, and OBS004 water observations are removed.

The manipulated branch contains four records; the trusted branch remains at seven. This is a controlled simulation and does not indicate a real incident or a truthful environmental change.

## 23. Side-by-Side Comparison

| Manipulation | Trusted versus simulated state | Likely interpretation and noticeability | Detection, prevention, and response evidence |
|---|---|---|---|
| Numeric change (ADV-001) | OBS001: 27,456,000 → 41,184,000 MWh | A larger bar may imply a real operational increase. A single value can appear plausible without a visible source comparison. | Trusted-hash mismatch, row-level comparison, and event log detect it. Prevent with protected baselines, access control, approval, and independent review. Preserve both versions and pipeline logs. |
| Source label removed (ADV-002) | OBS005 publisher/report name becomes blank; URL and source ID remain | Users lose the immediate source identity and may not inspect the remaining link. | Required source-name validation warns; source-register and trusted-row comparison detect. Preserve source metadata and review warnings. |
| Water feature omission (ADV-003) | Three water rows disappear; 7 trusted vs 4 adversarial rows | A dashboard can suggest the feature was never measured. Treating absence as zero would falsely imply no water impact. | Compare expected IDs, count, and metric coverage; event log and dimension flags expose removals. Prevent with required-feature and version checks. Preserve data/model screenshots. |

The impacts on interpretation are controlled examples only. The values do not describe a real change, and the local prototype does not implement manipulated axes, colors, assumptions, or a changed native Power BI report.

## 24. Analysis of Climate-Related Conclusions

The trustworthy conclusion is limited: the cited reports disclose indicators related to energy, water, emissions, and electricity generation, but the observed values describe different entities, years, definitions, and boundaries. Total energy includes multiple fuels; recycled water differs from consumed water; Samsung's division GHG is not a foundry-only facility value; the EPA regional factor is not company emissions; and the EPA sector total includes non-semiconductor electronics. The records cannot be summed into a total semiconductor footprint or directly ranked.

Manipulating the energy number changes the apparent value for that record; omitting water eliminates water coverage from the adversarial view; hiding the publisher label weakens traceability. More broadly, missing features or shifted boundaries can change apparent conclusions without changing any remaining number. Results in the literature further show that absolute totals, normalized intensity, and modeled scarcity-weighted estimates answer different questions.

## 25. Analysis of User Trust

Trust can be undermined by a plausible but altered value, missing rows, a hidden source, unexplained unit conversion, or a display that implies invalid comparability. Visible provenance, source locators, metric guidance, validation warnings, missing-row indicators, and a known-good hash make review more transparent. However, a matching hash can only compare bytes with the referenced digest; it does not establish who produced a file, whether the source is correct, or whether an unaltered source selectively omitted information.

The Power BI import model labels threat mappings as scenario references, distinguishes implemented from proposed controls, and flags the adversarial copy as simulation. These labels reduce the risk of presenting a taxonomy or exercise as active threat intelligence.

## 26. Discussion

The project answers its research question with a workflow that places source scope and manipulation visibility beside environmental values. It shows that a useful dashboard is not just a collection of charts: it must preserve source context, expose conversion and limitation details, prevent invalid aggregation, and make missing data visible.

The main cybersecurity lesson is that file integrity controls cannot detect every form of misleading information. A publisher may provide incomplete but untampered data; a chart may hide a feature while the underlying file remains unchanged; and a local manifest is weak if data writers can replace it too. A layered response combines source review, validation, separate copies, independently protected baselines, access controls, audit history, and visual review.

The generated Power BI model provides concise executive, environmental, provenance, integrity, threat-reference, control, incident-response, and manipulation tables. Its import and relationships are documented, but the report pages still need to be authored and visually reviewed in Power BI Desktop if a native report is required.

## 27. Limitations

- Seven observations are a small, heterogeneous collection, not a representative sector sample or time series.
- Four source IDs are represented in observations; the Intel source is registered but no observation has been extracted.
- Values are reported by companies or agencies and checked against the supplied report pages; the underlying measurement systems were not independently audited.
- Reporting year, organizational coverage, geography, units, boundaries, and definitions differ. The data do not support direct company ranking or aggregation.
- There is no current comparable process-gas inventory, water-scarcity index, facility-level energy/emissions panel, or packaging/product life-cycle dataset.
- The project owner certified the five selected journal papers as assignment-eligible on October 20, 2026. The project did not independently audit each journal's peer-review process. Paper 2 was reviewed from images; Paper 6 is a dissertation and is supplementary.
- ATT&CK references are taxonomy mappings. The project contains no live threat feed, IoCs, actor attribution, or real incident evidence.
- The local server is a loopback-only classroom prototype without identity, authorization, TLS, remote audit, or protected manifest custody. A standalone AES-256-GCM demonstration is available, but it is not connected to the dashboard's storage or transport path.
- No Power BI Desktop was available to produce or inspect a `.pbix`/`.pbip`; the tested deliverable is an import-ready CSV model.
- Screenshots demonstrate the local browser dashboard, not a Power BI report.

## 28. Recommendations

1. Keep source originals, source locators, original units, conversions, reporting boundaries, and limitations with every record.
2. Do not compare totals, combine different water definitions, or rank companies until reporting periods, boundaries, units, and denominators are harmonized.
3. Add facility/process-level data for electricity and fuel, process-gas emissions, water withdrawal and consumption, geography, and scarcity only when the source and method are documented.
4. Protect the trusted baseline and backups independently from data writers; add access approvals, MFA, least privilege, and platform audit logging on any shared service.
5. Review every filter, chart scale, unit label, source label, and missing-feature indicator before publishing.
6. In Power BI, use the documented dimension relationships and `SELECTEDVALUE` measures; preserve blank results when a selection is not comparable rather than summing mixed measures.
7. If a native `.pbix`/`.pbip` is required, create and independently review the report in Power BI Desktop; the current deliverable is the tested CSV model and browser dashboard.

## 29. Future Improvements

- Import and review Intel, process-gas, water-stress, and newer government data only from table-specific, source-located evidence.
- Develop a compatible multi-year facility/foundry dataset with clear production denominators, scope coverage, and uncertainty.
- Build and test the report pages in Power BI Desktop, capture actual Power BI screenshots, and compare report/model versions as well as CSVs.
- Add independently protected signatures or an external trusted hash service, role-based access, MFA, centralized audit logging, and platform-managed encryption at rest/in transit if the dashboard moves beyond localhost.
- Add automated source-register enforcement to the core pipeline, coverage expectations by metric, and reviewer approval/version history.
- Validate the live dashboard demonstration on another clean clone and on a POSIX host.

## 30. Conclusion

The project delivers reviewed source records, five full-text paper summaries, an assignment-aligned feature coverage register, a separate synthetic test dataset, documented security and response procedures, a local trusted/adversarial dashboard, a standalone AES-GCM encryption demonstration, and a tested Power BI import pack. Its evidence demonstrates how a changed value, weakened provenance, or removed feature can alter the apparent story even when each remaining number looks plausible.

The data support transparent reporting of selected disclosed indicators—not a comprehensive semiconductor climate footprint or a company ranking. Reliable conclusions require accurate values plus traceable sources, compatible boundaries, explicit assumptions, complete feature selection, protected transformations, and honest visual design.

## 31. References

### Academic research

1. Kuo, T.-C., Kuo, C.-Y., & Chen, L.-W. (2022). Assessing environmental impacts of nanoscale semi-conductor manufacturing from the life cycle assessment perspective. *Resources, Conservation and Recycling, 182*, 106289. https://doi.org/10.1016/j.resconrec.2022.106289
2. Ruberti, M. (2024). Environmental performance and trends of the world's semiconductor foundry industry. *Journal of Industrial Ecology, 28*(5), 1183-1197. https://doi.org/10.1111/jiec.13529
3. Wang, Q., Huang, N., Chen, Z., Chen, X., Cai, H., & Wu, Y. (2023). Environmental data and facts in the semiconductor manufacturing industry: An unexpected high water and energy consumption situation. *Water Cycle, 4*, 47-54. https://doi.org/10.1016/j.watcyc.2023.01.004
4. Ruberti, M. (2023). The chip manufacturing industry: Environmental impacts and eco-efficiency analysis. *Science of the Total Environment, 858*, 159873. https://doi.org/10.1016/j.scitotenv.2022.159873
5. Frost, K., & Hua, I. (2019). Quantifying spatiotemporal impacts of the interaction of water scarcity and water use by the global semiconductor manufacturing industry. *Water Resources and Industry, 22*, 100115. https://doi.org/10.1016/j.wri.2019.100115
6. Boyd, S. B. (2009). *Life-cycle Assessment of Semiconductors* [Doctoral dissertation, University of California, Berkeley]. UC Berkeley Electronic Theses and Dissertations. https://escholarship.org/uc/item/8bv2s63d

### Data sources

- Taiwan Semiconductor Manufacturing Company. (2025). *2024 Sustainability Report*. https://esg.tsmc.com/en-US/file/public/2024-TSMC-Sustainability-Report-e.pdf
- Intel Corporation. (2026). *2025-26 Corporate Responsibility Report* (registered candidate source; no observation extracted). https://www.intel.com/content/www/us/en/corporate-responsibility/resource-center.html
- Samsung Electronics. (2026). *Sustainability Report 2026*. https://www.samsung.com/global/sustainability/digital-library/facts-figures/
- US Environmental Protection Agency. (2025). *eGRID Summary Tables 2023*. https://www.epa.gov/egrid/summary-data
- US Environmental Protection Agency. (2018). *2011-2017 Greenhouse Gas Reporting Program Industrial Profile: Electronics Manufacturing Sector*. https://www.epa.gov/ghgreporting/ghgrp-electronics-manufacturing

### Threat-reference sources

- MITRE. *ATT&CK Enterprise Technique T1078: Valid Accounts*. https://attack.mitre.org/techniques/T1078/
- MITRE. *ATT&CK Enterprise Technique T1565.001: Stored Data Manipulation*. https://attack.mitre.org/techniques/T1565/001/
- MITRE. *ATT&CK Enterprise Technique T1565.002: Transmitted Data Manipulation*. https://attack.mitre.org/techniques/T1565/002/

### Project evidence

- *Climate-Feature Dashboard for Semiconductor Technology* assignment instructions. [`project_instructions.pdf`](project_instructions.pdf).
- Project source register, observation register, and paper register: `data/intake/sources_template.csv`, `data/intake/observations_template.csv`, and `data/intake/papers_template.csv`.
- Project methods and evidence: [`data_source_plan.md`](data_source_plan.md), [`data_dictionary.md`](data_dictionary.md), [`literature_review.md`](literature_review.md), [`threat_model.md`](threat_model.md), [`incident_response.md`](incident_response.md), [`system_architecture.md`](system_architecture.md), [`manipulation_comparison.md`](manipulation_comparison.md), and [`power_bi_setup.md`](power_bi_setup.md), [`environmental_feature_coverage.md`](environmental_feature_coverage.md), and [`encryption_demo.md`](encryption_demo.md).
