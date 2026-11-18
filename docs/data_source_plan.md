# Data-source plan

## Purpose and selection

This plan defines the evidence currently available for the dashboard. Sources were selected to demonstrate reported semiconductor-company operational measures, a regional grid factor, and a U.S. electronics-manufacturing sector total. The dataset is a small proof of workflow, not a representative sample of semiconductor manufacturers or a consistent comparative panel.

## Resolved feature and dataset scope

The assignment lists possible features rather than requiring every feature or a minimum record count. This project therefore uses a bounded evidence set: reported energy and water measures, wafer-normalized water intensity, reported organizational GHG emissions, and contextual grid and electronics-sector indicators. The five reviewed papers add evidence about process nodes, mask layers, process inputs, manufacturing intensity, and water-scarcity geography, but those study-specific values are not mixed into the seven-record observation table.

Packaging materials, process-gas inventories, water-scarcity scores, facility-level comparisons, and comparable historical company series remain outside the measured dataset because the supplied sources do not provide a sufficiently reviewed, consistently scoped record set for them. This is a documented scope limit, not a claim that those impacts are unimportant. No new values are estimated or inferred to fill these gaps. The seven records are sufficient for the project's provenance, interpretation, and controlled-manipulation demonstration, but not for industry-wide conclusions, trends, or company rankings.

## Assignment feature coverage

The full feature-to-evidence crosswalk is maintained in [environmental_feature_coverage.md](environmental_feature_coverage.md) and displayed in the dashboard's **Environmental feature coverage** view. It classifies assignment topics as source-reported, partial, research context, or not collected. This avoids treating a feature discussed in a paper as though it were measured in a company observation.

The trusted dataset currently contains seven source-reported observations. It contains no estimated or derived environmental observations; unit conversions retain original values and explicit formulas. Synthetic fixtures and adversarial modifications remain separate. The crosswalk identifies electricity-source splits, UPW, process gases, yield, materials, packaging, waste, water scarcity, Scope 3, lifecycle, and use-phase gaps without filling them with unsupported values.

## Source register

| Source ID | Source and local evidence | Measure/use | Coverage and boundary | Review status and limitations |
|---|---|---|---|---|
| `SRC001` | TSMC, *2024 Sustainability Report*; `data/intake/incoming/2024-TSMC-Sustainability-Report-e.pdf` | Total energy; recycled water; Taiwan-fab tap water; water per wafer equivalent | 2024. Company-wide or subsidiary scope for the energy, recycling, and intensity measures; Taiwan fabs only for tap-water consumption. See each observation's specific boundary. | Values and units checked against PDF pp. 120 and 129. Total energy includes electricity, natural gas, and diesel. Water measures have different scopes and meanings. |
| `SRC002` | Intel, *2025-26 Corporate Responsibility Report*; `data/intake/incoming/Intel_Report.pdf` | Context for future energy, water, and GHG observations; no observation extracted yet | Report states calendar and fiscal 2025 unless otherwise specified. | Report identity checked. Extract no values until the table, reporting year, unit, boundary, and page are reviewed for each proposed record. |
| `SRC003` | Samsung Electronics, *Sustainability Report 2026*; `data/intake/incoming/Samsung_Electronics_Sustainability_Report_2026_ENG.pdf` | Device Solutions Scope 1 plus market-based Scope 2 emissions | 2024, DS Division; Korean and global manufacturing sites as described in the report. Division is broader than semiconductor foundry operations. | Value and unit checked against PDF p. 72. Source reports 14,546 thousand tonnes CO2e; intake retains this original unit and records the conversion to tonnes. |
| `SRC004` | U.S. EPA, *eGRID Summary Tables 2023*; `data/intake/incoming/E-Grid_Summary.pdf` | CAMX subregion total-output CO2e rate | 2023 eGRID regional electricity generation; not a company-specific purchased-electricity factor. | PDF p. 2 reports 430.0 lb CO2e/MWh. The summary is rounded and explicitly a subset of the detailed workbook; do not use it to claim precision beyond the displayed value. |
| `SRC005` | U.S. EPA, *2011-2017 Greenhouse Gas Reporting Program Industrial Profile: Electronics Manufacturing Sector*; `data/intake/incoming/electronics_manufacturing_2017_industrial_profile.pdf` | 2017 reported electronics-manufacturing sector emissions | U.S. reporting facilities in an electronics sector that includes semiconductor and non-semiconductor facilities; reporting thresholds apply. | PDF p. 3 reports 6.1 million metric tons CO2e for 2017. This source does not substantiate a 2023 total. |

The source register is maintained in [`data/intake/sources_template.csv`](../data/intake/sources_template.csv). Record-level source links, locations, conversions, and caveats are in [`data/intake/observations_template.csv`](../data/intake/observations_template.csv).

## Observations currently included

| Record | Reported value used | Original value/unit | Data year | Comparability warning |
|---|---:|---|---:|---|
| `OBS001` | 27,456,000 MWh total energy | 27,456 GWh | 2024 | Total energy, not electricity-only |
| `OBS002` | 284,600,000 m3 recycled water | 284.6 million m3 | 2024 | Recycled water, not withdrawal or consumption |
| `OBS003` | 94,600,000 m3 Taiwan-fab tap-water consumption | 94.6 million m3 | 2024 | Taiwan fabs only |
| `OBS004` | 161.0 L per 12-inch equivalent wafer mask layer | 161.0 L per 12-inch equivalent wafer mask layer | 2024 | Production-normalized intensity; photomask-count basis |
| `OBS005` | 14,546,000 t CO2e | 14,546 thousand tonnes CO2e | 2024 | Samsung DS division, Scope 1 plus market-based Scope 2 |
| `OBS006` | 430.0 lb CO2e/MWh | 430.0 lb CO2e/MWh | 2023 | Rounded regional generation factor |
| `OBS007` | 6,100,000 t CO2e | 6.1 million metric tons CO2e | 2017 | EPA electronics sector, not semiconductor-only |

The `reported` status indicates that the source reports the observation; a documented unit conversion does not turn the source measurement into an independently measured or audited value. No estimate is invented to fill absent records.

## Collection and validation procedure

1. Preserve each original PDF and CSV. Do not edit a source document.
2. Verify the publisher/agency, report title, relevant year, geography, unit, definition, and reporting boundary.
3. Transcribe the value as shown and cite the PDF page/table in `source_locator`.
4. If converting units, retain the original value/unit and the reproducible formula. Do not increase precision beyond the source's precision.
5. Record limitations and uncertainty as described by the source. Use `Not stated` where information is absent; do not infer a confidence interval.
6. Confirm unique record IDs, required columns, numeric values, whole-number years, allowed status, registered metric/unit, complete source links, and consistent CSV row widths. The Power BI export also checks that every observation's `source_id` resolves to the source register, each record ID is unique, and every metric has comparison guidance.
7. Run the pipeline to a separate output directory, review the validation report, and verify the trusted output against its generated manifest.
8. Keep the supplied synthetic input unchanged. A passing schema check proves only that implemented checks passed; it does not prove source accuracy, completeness, comparability, or scientific validity.

## Known limitations and future acquisition

- No source-backed Intel observations have been added; the Intel report is registered for context only.
- The EPA electronics-manufacturing PDF covers through 2017 only. Any newer sector value requires the actual 2023 EPA workbook/table and its aggregation definition; it must not be interpolated from this profile.
- Greater precision for eGRID CAMX requires the detailed eGRID 2023 workbook and the exact field definition. Until then, retain the rounded 430.0 value.
- A future expansion could add source-checked process-gas, water-stress, packaging, lifecycle, or facility-level records, but only when the source definition, period, geography, unit, and boundary can be verified. Expansion is not required to describe the current bounded dataset accurately.
- Papers 1-5 have full-text reviews documented in [`docs/literature_review.md`](literature_review.md); Paper 2 was reviewed from rendered pages because its PDF contains no embedded text. The project owner certified the five papers' eligibility for the assignment on October 20, 2026. This is owner confirmation, not an independent audit of every journal's review process. Paper 6 is supplemental dissertation background and is not counted among the five journal papers.

## Analytical safeguards

Do not sum or directly compare total energy with electricity, recycled water with tap-water consumption, absolute volumes with product-normalized intensity, a grid-average factor with company emissions, or the EPA electronics-sector total with semiconductor-company totals. The dashboard should make these distinctions visible in labels, source details, and limitations. The seven-record collection is deliberately bounded and appropriate for demonstrating provenance and validation, not for estimating a global semiconductor footprint.
