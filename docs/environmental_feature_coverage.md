# Environmental feature coverage and evidence classification

## Purpose

This register maps the environmental and semiconductor-technology features named in the project assignment to the evidence actually represented by this project. It prevents the dashboard's selected indicators from being mistaken for a complete semiconductor footprint.

The assignment presents examples of relevant features; it does not require every example to become a measured column. The project uses a bounded, source-backed dataset and explicitly identifies what is not measured.

## Status definitions

- **Source-reported:** At least one reviewed observation is transcribed from a named source. This does not mean the project independently measured or audited the publisher's underlying value.
- **Partial:** Some aspect of the feature is represented, but the requested feature is only partly captured, or its geography, organization, period, or definition is limited.
- **Research context:** The selected literature discusses the feature, but no project observation measures it.
- **Not collected:** The current reviewed source set does not provide a suitable project-specific observation or feature-specific evidence.

No estimated or derived environmental observations are included in the seven-record trusted dataset. The values are source-reported, with documented unit conversions where applicable. Assumptions are documented as assumptions, not substituted for measurements. Synthetic fixture data and deliberately altered adversarial values are separate test/demo artifacts and must not be presented as environmental findings.

## Feature-to-evidence register

| Assignment feature | Status | Trusted observation(s) | Evidence basis | Limitation and interpretation rule |
|---|---|---|---|---|
| Total energy consumption | Source-reported | OBS001 | TSMC 2024 Sustainability Report, p. 120 | Includes purchased electricity, natural gas, and diesel; not electricity-only. |
| Electricity consumption and source mix | Partial | OBS001 | Electricity is included within TSMC's total energy figure. | No electricity-only value or renewable/nonrenewable source split is included. |
| Electricity-grid carbon intensity | Source-reported | OBS006 | U.S. EPA eGRID 2023 CAMX subregion output-emissions factor. | One rounded regional generation factor; not a company-specific purchased-electricity factor. |
| Water use and recycling | Source-reported | OBS002, OBS003, OBS004 | TSMC 2024 recycled water, Taiwan-fab tap-water consumption, and wafer-normalized water intensity. | These are different measures and boundaries; do not sum or substitute them. |
| Ultrapure-water use | Research context | None | Discussed in Wang et al. (2023) and the literature review. | No UPW value is included in the trusted observation dataset. |
| Greenhouse-gas emissions | Partial | OBS005, OBS007 | Samsung Device Solutions combined Scope 1 plus market-based Scope 2; EPA 2017 U.S. electronics-manufacturing sector total. | No separate Scope 1/Scope 2 series, no Scope 3 observation, and the EPA sector includes non-semiconductor activity. |
| Fluorinated process-gas emissions | Research context | None | Process gases and fluorinated GHGs are discussed in the reviewed semiconductor literature. | No comparable source-backed process-gas inventory is included. |
| Technology node and mask layers | Research context | None | Kuo et al. (2022) and Ruberti (2023, 2024) discuss process nodes, mask layers, and manufacturing-index assumptions. | No node-level or mask-layer observation is added to the company dataset. |
| Manufacturing yield | Not collected | None | No yield observation is registered in the reviewed dataset or selected dashboard source set. | No yield comparison or yield-adjusted footprint is supported. |
| Chip materials and chemical inputs | Research context | None | Material, chemical, and process-input categories are discussed in the life-cycle literature. | No source-backed bill of materials or comparable material inventory is collected. |
| Semiconductor packaging materials | Not collected | None | Packaging is outside the measured dataset; Kuo et al. identify packaging as future work. | No packaging composition or packaging life-cycle value is measured. |
| Manufacturing location and geography | Partial | OBS001–OBS007 | Taiwan-fab, CAMX regional, U.S. sector, and company/division geography fields are retained. | No comparable facility-level location inventory or supply-chain map is available. |
| Waste generation | Research context | None | Waste indicators are discussed in Ruberti (2023, 2024) and other reviewed literature. | No waste-generation observation is included in the trusted dataset. |
| Water scarcity and watershed context | Research context | None | Frost and Hua (2019) model spatial and seasonal water-scarcity interactions. | No scarcity score is joined to the current company observations; modeled withdrawals are not direct measurements. |
| Lifecycle impacts and boundaries | Research context | None | Life-cycle assessment and boundary choices are discussed in Kuo et al. (2022) and the literature review. | The seven records are operational, regional, or sector indicators, not a harmonized product life-cycle inventory. |
| Scope 3, supply-chain, and transportation impacts | Not collected | None | The literature review documents incomplete Scope 3 disclosure and value-chain coverage. | No comparable Scope 3, supplier, logistics, or transportation observation is included. |
| Chip operating efficiency and data-center energy | Not collected | None | These use-phase topics are outside the selected source-backed dataset. | No chip performance-per-watt or data-center use-phase analysis is supported. |

## Dataset classification

| Data class | Current project treatment |
|---|---|
| Source-reported | Seven trusted observations in data/processed/reviewed/trusted_data.csv, traced to five registered source documents. |
| Derived | No additional derived environmental observation is currently included. Unit conversions retain original values and explicit conversion methods. |
| Estimated | No estimated environmental observation is included. |
| Assumption | Scope and methodology assumptions are documented in the proposal, source plan, and research reviews; they are not displayed as measured values. |
| Synthetic demonstration | Separate pipeline fixture data, clearly identified as synthetic and not research evidence. |
| Manipulated demonstration | Separate adversarial copy with five logged events across three manipulation types; never use as trusted analysis. |

## Maintenance and acceptance rules

1. When adding a feature, identify its exact source, publisher, publication year, data year, unit, geography, organizational scope, lifecycle/reporting boundary, source locator, limitations, and validation method.
2. Retain the original reported value and unit when converting. Do not increase precision beyond the source.
3. Do not infer missing values, combine unlike metrics, or use a literature model output as though it were a company-reported observation.
4. Update this register, the dashboard feature-coverage configuration in climate_dashboard/dashboard_ui/app.js, the data dictionary, source plan, metric guide, and final report together.
5. Regenerate the trusted dataset and context pack, run tests and integrity validation, then confirm the displayed record IDs match the trusted CSV.
6. Update the manipulated comparison and screenshots whenever trusted records change.

## Why the omissions matter

A missing feature can materially change the interpretation even when every remaining number is accurate. For example, excluding process gases, water scarcity, Scope 3, waste, or packaging can narrow the apparent footprint. The feature-coverage view makes those omissions visible; it does not claim to quantify their effects.
