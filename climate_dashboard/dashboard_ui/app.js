"use strict";

const tableColumns = {
  overview: [
    ["record_id", "Record"],
    ["company", "Organization"],
    ["facility", "Facility / scope"],
    ["geography", "Geography"],
    ["value_with_unit", "Reported value"],
    ["data_year", "Year"],
    ["data_status", "Status"],
    ["source_name", "Source"],
    ["lifecycle_boundary", "Reporting boundary"],
    ["limitation", "Limitation"],
  ],
  records: [
    ["record_id", "Record"],
    ["company", "Organization"],
    ["facility", "Facility / scope"],
    ["geography", "Geography"],
    ["metric", "Measure"],
    ["value_with_unit", "Reported value"],
    ["data_year", "Year"],
    ["source_name", "Source"],
    ["source_url", "Source URL"],
    ["source_locator", "Source locator"],
    ["original_value_with_unit", "Original value"],
    ["conversion_method", "Conversion"],
    ["lifecycle_boundary", "Reporting boundary"],
    ["uncertainty", "Uncertainty"],
    ["limitation", "Limitation"],
  ],
  measures: [
    ["metric", "Measure"],
    ["standardized_value", "Standardized value"],
    ["source_value", "Original source value"],
    ["unit", "Unit and meaning"],
    ["geography", "Geography"],
    ["scope", "Reporting boundary"],
    ["comparison_note", "Comparison caution"],
  ],
  sources: [
    ["source_id", "Source ID"],
    ["source_name", "Report / dataset"],
    ["organization", "Publisher"],
    ["publication_year", "Publication year"],
    ["data_year_start", "Data years"],
    ["geography", "Geography"],
    ["feature_coverage", "Features"],
    ["lifecycle_boundary", "Boundary"],
    ["validation_method", "Validation"],
  ],
  papers: [
    ["paper_id", "Paper"],
    ["full_citation", "Citation"],
    ["semiconductor_feature", "Feature"],
    ["main_findings", "Main findings"],
    ["limitations", "Limitations"],
    ["review_status", "Review status"],
  ],
  threats: [
    ["technique_id", "ATT&CK ID"],
    ["technique_name", "Technique"],
    ["coverage_status", "Project status"],
    ["relevance", "Scenario relevance"],
  ],
};

const NO_OBSERVATIONS = "__no_observations__";

const featureCoverage = [
  { feature: "Total energy consumption", status: "Source-reported", metrics: ["Total energy consumption"], evidence: "TSMC 2024 Sustainability Report, p. 120; includes electricity, natural gas, and diesel.", limitation: "Company-reported total energy; not electricity-only." },
  { feature: "Electricity consumption and source mix", status: "Partial", metrics: ["Total energy consumption"], evidence: "Electricity is included within TSMC's total energy figure; the observation does not split electricity by source.", limitation: "No separate electricity-only or renewable/nonrenewable breakdown is in the trusted records." },
  { feature: "Electricity-grid carbon intensity", status: "Source-reported", metrics: ["Electricity-generation CO2-equivalent output emission rate"], evidence: "U.S. EPA eGRID 2023 CAMX subregion output-emissions factor.", limitation: "One rounded regional generation factor; not a company-specific purchased-electricity factor." },
  { feature: "Water use and recycling", status: "Source-reported", metrics: ["Water recycled from recovery systems", "Tap water consumption", "Water consumption per 12-inch equivalent wafer mask layer"], evidence: "Three TSMC 2024 observations covering recycled water, Taiwan-fab tap-water consumption, and wafer-normalized intensity.", limitation: "These are different measures and boundaries; do not sum or substitute them." },
  { feature: "Ultrapure-water use", status: "Research context", metrics: [], evidence: "Discussed in Wang et al. (2023) and the literature review.", limitation: "No UPW value is included in the trusted observation dataset." },
  { feature: "Greenhouse-gas emissions", status: "Partial", metrics: ["Scope 1 and Scope 2 greenhouse-gas emissions", "Reported greenhouse-gas emissions"], evidence: "Samsung Device Solutions combined Scope 1 plus market-based Scope 2; EPA 2017 U.S. electronics-manufacturing sector total.", limitation: "No separate Scope 1/Scope 2 series, no Scope 3 observation, and the EPA sector includes non-semiconductor activity." },
  { feature: "Fluorinated process-gas emissions", status: "Research context", metrics: [], evidence: "Process gases and fluorinated GHGs are discussed in the reviewed semiconductor literature.", limitation: "No comparable source-backed process-gas inventory is included." },
  { feature: "Technology node and mask layers", status: "Research context", metrics: [], evidence: "Kuo et al. (2022) and the Ruberti studies discuss process nodes, mask layers, and manufacturing-index assumptions.", limitation: "No node-level or mask-layer observation is added to the company dataset." },
  { feature: "Manufacturing yield", status: "Not collected", metrics: [], evidence: "No yield observation is registered in the reviewed dataset or selected dashboard source set.", limitation: "No yield comparison or yield-adjusted footprint is supported." },
  { feature: "Chip materials and chemical inputs", status: "Research context", metrics: [], evidence: "Material, chemical, and process-input categories are discussed in the life-cycle literature.", limitation: "No source-backed bill of materials or comparable material inventory is collected." },
  { feature: "Semiconductor packaging materials", status: "Not collected", metrics: [], evidence: "The reviewed source plan identifies packaging as outside the measured dataset; Kuo et al. identify packaging as future work.", limitation: "No packaging composition or packaging life-cycle value is measured." },
  { feature: "Manufacturing location and geography", status: "Partial", metrics: [], evidence: "Geographic scope is retained for each observation, including Taiwan fabs and the CAMX and U.S. regional/sector records.", limitation: "The data do not provide a comparable facility-level location inventory or supply-chain map." },
  { feature: "Waste generation", status: "Research context", metrics: [], evidence: "Waste indicators are discussed in Ruberti (2023, 2024) and other reviewed literature.", limitation: "No waste-generation observation is included in the trusted dataset." },
  { feature: "Water scarcity and watershed context", status: "Research context", metrics: [], evidence: "Frost and Hua (2019) model spatial and seasonal water-scarcity interactions.", limitation: "No scarcity score is joined to the current company observations; modeled withdrawals are not direct measurements." },
  { feature: "Lifecycle impacts and boundaries", status: "Research context", metrics: [], evidence: "Life-cycle assessment and boundary choices are discussed in Kuo et al. (2022) and the literature review.", limitation: "The seven records are operational, regional, or sector indicators, not a harmonized product life-cycle inventory." },
  { feature: "Scope 3, supply-chain, and transportation impacts", status: "Not collected", metrics: [], evidence: "The literature review documents incomplete Scope 3 disclosure and value-chain coverage.", limitation: "No comparable Scope 3, supplier, logistics, or transportation observation is included." },
  { feature: "Chip operating efficiency and data-center energy", status: "Not collected", metrics: [], evidence: "These use-phase topics are outside the selected source-backed dataset.", limitation: "No chip performance-per-watt or data-center use-phase analysis is supported." }
];

const measureGuides = {
  "Total energy consumption": {
    meaning: "Total energy reported by the organization; this includes electricity, natural gas, and diesel for the cited observation.",
    unit: "MWh means megawatt-hours. 1 MWh equals 1,000 kWh.",
    compare: "Compare only with the same reporting period and organizational boundary, and where the same energy carriers are included. This is not electricity-only.",
  },
  "Water recycled from recovery systems": {
    meaning: "Water returned through the reporting organization's recovery systems.",
    unit: "m³ means cubic metres of water; 1 m³ equals 1,000 litres.",
    compare: "This is a recycled-water volume, not water withdrawal or water consumption. Compare only like-for-like recycling definitions and boundaries.",
  },
  "Tap water consumption": {
    meaning: "Tap-water consumption reported for TSMC fabs in Taiwan.",
    unit: "m³ means cubic metres of water; 1 m³ equals 1,000 litres.",
    compare: "The observation covers Taiwan fabs only. Do not treat it as a global total or directly compare it with a global boundary.",
  },
  "Water consumption per 12-inch equivalent wafer mask layer": {
    meaning: "Water-consumption intensity normalized by 12-inch-equivalent wafer mask layers.",
    unit: "L per 12-inch equivalent wafer mask layer is a production-normalized rate, not a total water volume.",
    compare: "Compare only with the same normalization method and production basis. Do not compare this intensity directly with an absolute m³ value.",
  },
  "Scope 1 and Scope 2 greenhouse-gas emissions": {
    meaning: "Direct (Scope 1) plus purchased-energy indirect (Scope 2) greenhouse-gas emissions for Samsung Device Solutions.",
    unit: "t CO₂e means metric tonnes of carbon-dioxide equivalent.",
    compare: "This is a division-level, market-based report, not a single-fab or foundry-only measurement. Compare only with matching scopes and organizational coverage.",
  },
  "Electricity-generation CO2-equivalent output emission rate": {
    meaning: "Average emissions intensity of electricity generation in the EPA eGRID CAMX subregion.",
    unit: "lb CO₂e/MWh means pounds of CO₂-equivalent per megawatt-hour of electricity generated.",
    compare: "This is a regional grid factor, not a company's reported emissions. It cannot be compared directly to total emissions in tonnes CO₂e.",
  },
  "Reported greenhouse-gas emissions": {
    meaning: "Reported greenhouse-gas emissions for the U.S. EPA electronics-manufacturing sector in 2017.",
    unit: "t CO₂e means metric tonnes of carbon-dioxide equivalent.",
    compare: "This sector includes electronics manufacturing beyond semiconductors and is not a company or fab measurement. Reporting thresholds also limit coverage.",
  },
};

let dashboardData;

function make(tag, className, text) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined && text !== null) element.textContent = String(text);
  return element;
}

function displayValue(value) {
  return value === undefined || value === null || value === "" ? "Not supplied" : String(value);
}

function formatNumber(value) {
  const [integer, fraction] = String(value).split(".");
  const sign = integer.startsWith("-") ? "-" : "";
  const digits = sign ? integer.slice(1) : integer;
  const grouped = digits.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  return `${sign}${grouped}${fraction === undefined ? "" : `.${fraction}`}`;
}

function originalValueWithUnit(record) {
  if (record.original_value === undefined || record.original_value === null || record.original_value === "") {
    return "Not supplied";
  }
  return `${formatNumber(record.original_value)} ${displayValue(record.original_unit)}`;
}

function valueForBasis(record, basis, referenceRecord = null) {
  if (
    basis !== "source"
    || record.original_value === undefined
    || record.original_value === null
    || record.original_value === ""
  ) {
    return { value: formatNumber(record.value), unit: displayValue(record.unit), numeric: record.numeric_value };
  }

  let numeric = Number(record.original_value);
  if (!Number.isFinite(numeric)) {
    return { value: formatNumber(record.value), unit: displayValue(record.unit), numeric: record.numeric_value };
  }
  if (referenceRecord && referenceRecord.numeric_value !== 0) {
    numeric *= record.numeric_value / referenceRecord.numeric_value;
  }
  return {
    value: formatNumber(numeric),
    unit: displayValue(record.original_unit),
    numeric,
  };
}

function currentMeasureGuide(metric, recordCount) {
  const guide = measureGuides[metric];
  const context = dashboardData.metric_guide.find((item) => item.metric === metric);
  const container = make("div", "measure-guide-content");
  if (metric === NO_OBSERVATIONS) {
    container.append(make("strong", "", "No reviewed observation for this report"));
    container.append(make("p", "", "This source is registered, but no value from it has passed review into the trusted dataset."));
  } else if (!guide && !context) {
    container.append(make("strong", "", metric), make("p", "", "Check the source record for the measure definition and unit."));
  } else {
    container.append(
      make("strong", "", `What this measures: ${metric}`),
      make("p", "", guide?.meaning || context.climate_relevance),
      make("p", "", `Unit: ${guide?.unit || context.unit}`),
      make("p", "", `Reporting boundary: ${context?.primary_boundary || "See the selected source record."}`),
      make("p", "", `How to compare: ${guide?.compare || context?.comparison_rule || "Check the cited source and align scope before comparing."}`)
    );
  }
  const coverage = recordCount > 1
    ? `${recordCount} records are available for this measure. Similar units alone do not establish comparable scope.`
    : recordCount === 1
      ? "Only one record is available for this measure in the reviewed dataset; there is no peer record here for a like-for-like comparison."
      : "No reviewed record matches this report and measure selection. Absence is not zero.";
  container.append(make("p", "guide-coverage", coverage));
  return container;
}

function makeCell(value) {
  const cell = document.createElement("td");
  cell.textContent = displayValue(value);
  return cell;
}

function renderTable(table, columns, rows, rowMapper = (row, key) => row[key]) {
  table.replaceChildren();
  const head = document.createElement("thead");
  const headRow = document.createElement("tr");
  for (const [, label] of columns) {
    const cell = make("th", "", label);
    cell.scope = "col";
    headRow.append(cell);
  }
  head.append(headRow);
  table.append(head);
  const body = document.createElement("tbody");
  for (const row of rows) {
    const tr = document.createElement("tr");
    for (const [key] of columns) tr.append(makeCell(rowMapper(row, key)));
    body.append(tr);
  }
  if (!rows.length) {
    const tr = document.createElement("tr");
    const cell = make("td", "muted", "No records match this selection.");
    cell.colSpan = columns.length;
    tr.append(cell);
    body.append(tr);
  }
  table.append(body);
}

function addOptions(select, values, selectedValue) {
  select.replaceChildren();
  for (const value of values) {
    const choice = typeof value === "string"
      ? { value, label: value }
      : value;
    const option = document.createElement("option");
    option.value = choice.value;
    option.textContent = choice.label;
    select.append(option);
  }
  if (selectedValue !== undefined) select.value = selectedValue;
  select.disabled = false;
}

function selectedRecords(
  metricSelect,
  yearSelect,
  dataset = dashboardData.trusted,
  sourceId = "",
  company = ""
) {
  const metric = metricSelect.value;
  const year = yearSelect.value;
  return dataset.filter((record) =>
    record.metric === metric
    && (year === "All years" || record.data_year === year)
    && (!sourceId || record.source_id === sourceId)
    && (!company || record.company === company)
  );
}

function refreshOverviewFilters() {
  const sourceId = document.querySelector("#report-filter").value;
  const scoped = dashboardData.trusted.filter((record) => !sourceId || record.source_id === sourceId);
  const metricSelect = document.querySelector("#metric-filter");
  const metrics = [...new Set(scoped.map((record) => record.metric))].sort();
  if (metrics.length) {
    const selectedMetric = metrics.includes(metricSelect.value) ? metricSelect.value : metrics[0];
    addOptions(metricSelect, metrics, selectedMetric);
  } else {
    addOptions(metricSelect, [{ value: NO_OBSERVATIONS, label: "No reviewed observations for this report" }], NO_OBSERVATIONS);
  }

  const selectedMetric = metricSelect.value;
  const metricRows = scoped.filter((record) => record.metric === selectedMetric);
  const yearSelect = document.querySelector("#year-filter");
  const years = ["All years", ...new Set(metricRows.map((record) => record.data_year))]
    .sort((a, b) => a === "All years" ? -1 : b === "All years" ? 1 : Number(a) - Number(b));
  addOptions(yearSelect, years, years.includes(yearSelect.value) ? yearSelect.value : "All years");

  const organizationSelect = document.querySelector("#organization-filter");
  const organizations = ["All organizations", ...new Set(metricRows.map((record) => record.company))].sort(
    (a, b) => a === "All organizations" ? -1 : b === "All organizations" ? 1 : a.localeCompare(b)
  );
  addOptions(
    organizationSelect,
    organizations,
    organizations.includes(organizationSelect.value) ? organizationSelect.value : "All organizations"
  );
}

function currentOverviewRecords() {
  return selectedRecords(
    document.querySelector("#metric-filter"),
    document.querySelector("#year-filter"),
    dashboardData.trusted,
    document.querySelector("#report-filter").value,
    document.querySelector("#organization-filter").value === "All organizations"
      ? ""
      : document.querySelector("#organization-filter").value
  );
}

function renderOverview() {
  const records = currentOverviewRecords();
  const metric = document.querySelector("#metric-filter").value;
  const basis = document.querySelector("#overview-value-basis").value;
  const sourceId = document.querySelector("#report-filter").value;
  const guideRecords = dashboardData.trusted.filter((record) =>
    record.metric === metric && (!sourceId || record.source_id === sourceId)
  );
  const years = [...new Set(records.map((record) => record.data_year))];
  const displayed = records.map((record) => valueForBasis(record, basis));
  const unit = displayed[0]?.unit || "";

  document.querySelector("#chart-title").textContent = records.length
    ? `${metric} (${unit})`
    : "No source-backed observations for this selection";
  document.querySelector("#chart-note").textContent = basis === "source"
    ? "Values use the number and unit transcribed from the cited source. Each bar is scaled within this measure only; no aggregation is performed."
    : "Values use the standardized project unit shown. Each bar is scaled within this measure only; no aggregation is performed.";
  const guide = document.querySelector("#overview-measure-guide");
  guide.replaceChildren(currentMeasureGuide(metric, guideRecords.length));
  const summary = document.querySelector("#overview-summary");
  summary.replaceChildren();
  const summaries = [
    ["Records shown", records.length],
    ["Measure", metric],
    ["Year(s)", years.join(", ") || "No matching records"],
    ["Value basis", basis === "source" ? "Original source units" : "Standardized project units"],
  ];
  for (const [label, value] of summaries) {
    const card = make("article", "summary-card");
    card.append(make("span", "summary-label", label), make("span", "summary-value", value));
    summary.append(card);
  }

  const chart = document.querySelector("#bar-chart");
  chart.replaceChildren();
  if (!records.length) {
    chart.append(make("p", "muted", "No reviewed records match these filters. Missing data is not zero."));
  }
  const max = Math.max(0, ...displayed.map((record) => record.numeric));
  for (const [index, record] of records.entries()) {
    const shownValue = displayed[index];
    const row = make("div", "bar-row");
    const label = make("span", "bar-label", `${record.company} · ${record.facility}`);
    const bar = document.createElement("progress");
    bar.className = "bar-progress";
    bar.max = max || 1;
    bar.value = shownValue.numeric;
    bar.setAttribute("aria-label", `${label.textContent}: ${shownValue.value} ${shownValue.unit}`);
    const value = make("span", "bar-value", `${shownValue.value} ${shownValue.unit}`);
    row.append(label, bar, value);
    chart.append(row);
  }

  renderTable(
    document.querySelector("#overview-table"),
    tableColumns.overview,
    records,
    (record, key) => {
      if (key !== "value_with_unit") return record[key];
      const shown = valueForBasis(record, basis);
      return `${shown.value} ${shown.unit}`;
    }
  );
}

function renderRecords() {
  const query = document.querySelector("#record-search").value.trim().toLocaleLowerCase();
  const sourceId = document.querySelector("#records-source-filter").value;
  const records = dashboardData.trusted.filter((record) =>
    (!sourceId || record.source_id === sourceId)
    && (!query || Object.values(record).some((value) => String(value).toLocaleLowerCase().includes(query)))
  );
  renderTable(
    document.querySelector("#records-table"),
    tableColumns.records,
    records,
    (record, key) => {
      if (key === "value_with_unit") return `${formatNumber(record.value)} ${displayValue(record.unit)}`;
      if (key === "original_value_with_unit") return originalValueWithUnit(record);
      return record[key];
    }
  );
}

function addDetail(container, label, value) {
  const item = make("div", "detail-item");
  item.append(make("strong", "", label), make("p", "", displayValue(value)));
  container.append(item);
}

function renderDetails(container, title, fields) {
  container.replaceChildren();
  const card = make("article", "context-card");
  card.append(make("h3", "", title));
  const grid = make("div", "detail-grid");
  for (const [label, value] of fields) addDetail(grid, label, value);
  card.append(grid);
  container.append(card);
}

function addSafeLink(container, url, label) {
  try {
    const parsed = new URL(url);
    if (parsed.protocol !== "https:") throw new Error("Only HTTPS source links are supported.");
    const link = make("a", "", label);
    link.href = parsed.href;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    container.append(link);
  } catch {
    container.append(make("span", "muted", "Source link unavailable."));
  }
}

function refreshContextOptions() {
  const type = document.querySelector("#context-type-filter").value;
  const select = document.querySelector("#context-item-filter");
  const label = document.querySelector("#context-item-label");
  document.querySelector("#context-type-filter").disabled = false;
  if (type === "sources") {
    label.firstChild.textContent = "Select a report";
    addOptions(
      select,
      dashboardData.sources.map((source) => ({
        value: source.source_id,
        label: `${source.source_id} · ${source.source_name}`,
      })),
      select.value
    );
  } else {
    label.firstChild.textContent = "Select a research paper";
    addOptions(
      select,
      dashboardData.papers.map((paper) => ({
        value: paper.paper_id,
        label: `${paper.paper_id} · ${paper.full_citation}`,
      })),
      select.value
    );
  }
  renderDataContext();
}

function renderDataContext() {
  const type = document.querySelector("#context-type-filter").value;
  const selectedId = document.querySelector("#context-item-filter").value;
  const detail = document.querySelector("#context-detail");
  const table = document.querySelector("#context-table");
  const title = document.querySelector("#context-table-title");
  if (type === "sources") {
    const source = dashboardData.sources.find((item) => item.source_id === selectedId);
    const records = dashboardData.trusted.filter((record) => record.source_id === selectedId);
    title.textContent = "Registered source reports";
    renderTable(table, tableColumns.sources, dashboardData.sources, (row, key) => {
      if (key === "data_year_start") return `${row.data_year_start}–${row.data_year_end}`;
      return row[key];
    });
    document.querySelector("#source-observations-title").textContent =
      `Reviewed observations from this report (${records.length})`;
    renderTable(
      document.querySelector("#source-observations"),
      [
        ["record_id", "Record"],
        ["metric", "Measure"],
        ["value_with_unit", "Reported value"],
        ["data_year", "Year"],
        ["geography", "Geography"],
      ],
      records,
      (record, key) => key === "value_with_unit"
        ? `${formatNumber(record.value)} ${displayValue(record.unit)}`
        : record[key]
    );
    if (!source) {
      detail.replaceChildren(make("p", "muted", "Select a registered report."));
      return;
    }
    const linkedText = records.length
      ? `${records.length} reviewed observation(s) link to this report.`
      : "No observation from this registered report is currently included in the trusted dataset.";
    renderDetails(detail, `${source.source_id} · ${source.source_name}`, [
      ["Publisher", source.organization],
      ["Publication year", source.publication_year],
      ["Data years", `${source.data_year_start}–${source.data_year_end}`],
      ["Geography", source.geography],
      ["Feature coverage", source.feature_coverage],
      ["Reporting boundary", source.lifecycle_boundary],
      ["Reliability evidence", source.reliability_evidence],
      ["Limitations", source.limitations],
      ["Validation method", source.validation_method],
      ["Observation coverage", linkedText],
    ]);
    const linkArea = make("p", "source-link");
    addSafeLink(linkArea, source.source_url, "Open publisher source");
    detail.firstChild.append(linkArea);
    return;
  }

  const paper = dashboardData.papers.find((item) => item.paper_id === selectedId);
  title.textContent = "Five selected journal-paper records";
  renderTable(table, tableColumns.papers, dashboardData.papers);
  document.querySelector("#source-observations-title").textContent = "Source observations are managed separately";
  renderTable(
    document.querySelector("#source-observations"),
    [["message", "Observation coverage"]],
    [{ message: "Research-paper summaries are not source observations and are not included in the trusted measurement dataset." }]
  );
  if (!paper) {
    detail.replaceChildren(make("p", "muted", "Select a registered paper."));
    return;
  }
  renderDetails(detail, `${paper.paper_id} · ${paper.full_citation}`, [
    ["Research objective", paper.research_objective],
    ["Semiconductor feature", paper.semiconductor_feature],
    ["Data and variables", paper.data_or_variables],
    ["Environmental impact", paper.environmental_impact],
    ["Main findings", paper.main_findings],
    ["Limitations", paper.limitations],
    ["Dashboard relevance", paper.dashboard_relevance],
    ["Review status", paper.review_status],
    ["Peer-review evidence", paper.peer_review_evidence],
  ]);
}

function renderFeatureCoverage() {
  const counts = new Map(["Source-reported", "Partial", "Research context", "Not collected"].map((status) => [status, 0]));
  const rows = featureCoverage.map((item) => {
    const matching = dashboardData.trusted.filter((record) => item.metrics.includes(record.metric));
    const status = item.status === "Source-reported" && matching.length === 0 ? "Not collected" : item.status;
    counts.set(status, counts.get(status) + 1);
    return {
      feature: item.feature,
      status,
      observations: matching.length ? matching.map((record) => record.record_id).join(", ") : "None",
      evidence: item.evidence,
      limitation: item.limitation,
    };
  });
  const summary = document.querySelector("#feature-coverage-summary");
  summary.replaceChildren();
  for (const [status, count] of counts) {
    const card = make("article", "summary-card");
    card.append(make("span", "summary-label", status), make("span", "summary-value", count));
    summary.append(card);
  }
  renderTable(
    document.querySelector("#feature-coverage-table"),
    [
      ["feature", "Assignment feature"],
      ["status", "Evidence status"],
      ["observations", "Linked records"],
      ["evidence", "Evidence basis"],
      ["limitation", "Coverage limitation"],
    ],
    rows
  );
}

function renderExecutiveSummary() {
  const project = dashboardData.project_summary[0] || {};
  document.querySelector("#project-question").textContent = project.research_question || "";
  const sourceIds = new Set(dashboardData.trusted.map((record) => record.source_id));
  const cards = [
    ["Reviewed observations", dashboardData.trusted.length],
    ["Registered reports", dashboardData.sources.length],
    ["Reports with observations", sourceIds.size],
    ["Full-text-reviewed journal papers", dashboardData.papers.length],
    ["ATT&CK scenario references", dashboardData.threat_intel.length],
    ["Logged simulation events", dashboardData.changes.length],
  ];
  const summary = document.querySelector("#executive-summary");
  summary.replaceChildren();
  for (const [label, value] of cards) {
    const card = make("article", "summary-card");
    card.append(make("span", "summary-label", label), make("span", "summary-value", value));
    summary.append(card);
  }

  const groups = new Map([["Energy", 0], ["Water", 0], ["Emissions and grid context", 0]]);
  for (const record of dashboardData.trusted) {
    const group = /water/i.test(record.metric)
      ? "Water"
      : /energy/i.test(record.metric)
        ? "Energy"
        : "Emissions and grid context";
    groups.set(group, groups.get(group) + 1);
  }
  const coverage = document.querySelector("#coverage-summary");
  coverage.replaceChildren();
  for (const [label, count] of groups) {
    const item = make("article", "coverage-card");
    item.append(make("span", "summary-label", label), make("strong", "", `${count} record(s)`));
    coverage.append(item);
  }

  const readout = document.querySelector("#executive-readout");
  readout.replaceChildren();
  for (const text of [
    project.data_scope,
    project.threat_intelligence_scope,
    project.power_bi_status,
    "The raw synthetic demonstration data remain separate from these reviewed observations.",
  ]) {
    if (text) readout.append(make("p", "", text));
  }
  readout.append(
    make(
      "p",
      "status-line",
      `Pipeline: ${dashboardData.validation.status} · Trusted file hash: ${dashboardData.integrity.verified ? "MATCH" : "MISMATCH"}`
    )
  );
}

function renderThreatIntel() {
  const selected = document.querySelector("#threat-technique-filter").value;
  const item = dashboardData.threat_intel.find((reference) => reference.technique_id === selected);
  const detail = document.querySelector("#threat-detail");
  if (!item) {
    detail.replaceChildren(make("p", "muted", "Select a threat reference."));
  } else {
    renderDetails(detail, `${item.technique_id} · ${item.technique_name}`, [
      ["Framework", item.framework],
      ["Scenario relevance", item.relevance],
      ["Project evidence", item.project_evidence],
      ["Coverage status", item.coverage_status],
      ["Confidence and attribution", item.confidence_note],
    ]);
    const linkArea = make("p", "source-link");
    addSafeLink(linkArea, item.source_url, "Open MITRE ATT&CK technique");
    detail.firstChild.append(linkArea);
  }
  renderTable(document.querySelector("#threat-table"), tableColumns.threats, dashboardData.threat_intel);
}

function controlGroup(status) {
  if (status.startsWith("Implemented")) return "Implemented";
  if (status.startsWith("Documented")) return "Documented manual";
  return "Recommended";
}

function renderControls() {
  const filter = document.querySelector("#control-status-filter").value;
  const controls = dashboardData.controls.filter((control) =>
    filter === "All statuses" || controlGroup(control.implementation_status) === filter
  );
  const summary = document.querySelector("#control-summary");
  summary.replaceChildren();
  for (const group of ["Implemented", "Documented manual", "Recommended"]) {
    const count = dashboardData.controls.filter((control) => controlGroup(control.implementation_status) === group).length;
    const card = make("article", "summary-card");
    card.append(make("span", "summary-label", group), make("span", "summary-value", count));
    summary.append(card);
  }
  const container = document.querySelector("#control-cards");
  container.replaceChildren();
  for (const control of controls) {
    const card = make("article", "context-card");
    const header = make("div", "control-card-heading");
    header.append(
      make("h3", "", `${control.control_id} · ${control.control}`),
      make("span", "status-pill status-reported", control.implementation_status)
    );
    card.append(
      header,
      make("p", "", control.purpose),
      make("p", "muted", `Control type: ${control.control_type}`),
      make("p", "", `Evidence: ${control.evidence}`),
      make("p", "warning-copy", `Limitation: ${control.limitation}`)
    );
    container.append(card);
  }
}

function renderIncidentResponse() {
  const selected = document.querySelector("#response-stage-filter").value;
  const stage = dashboardData.incident_response.find((item) => item.phase === selected);
  const detail = document.querySelector("#response-detail");
  if (!stage) {
    detail.replaceChildren(make("p", "muted", "Select an incident-response stage."));
  } else {
    renderDetails(detail, stage.phase, [
      ["Objective", stage.objective],
      ["Actions", stage.actions],
      ["Evidence / exit criteria", stage.evidence_or_exit_criteria],
    ]);
  }
  const stageList = document.querySelector("#response-stage-list");
  stageList.replaceChildren();
  for (const item of dashboardData.incident_response) {
    const card = make("article", "stage-card");
    card.append(
      make("h3", "", item.phase),
      make("p", "", item.objective),
      make("p", "muted", `Exit criteria: ${item.evidence_or_exit_criteria}`)
    );
    stageList.append(card);
  }
}

function renderMeasureGuide() {
  const metric = document.querySelector("#guide-metric").value;
  const guide = document.querySelector("#guide-measure-detail");
  const records = dashboardData.trusted.filter((record) => record.metric === metric);
  guide.replaceChildren(currentMeasureGuide(metric, records.length));

  const metricNames = [...new Set(dashboardData.trusted.map((record) => record.metric))];
  const inventory = metricNames.flatMap((name) => {
    const metricRecords = dashboardData.trusted.filter((record) => record.metric === name);
    const metadata = measureGuides[name];
    return metricRecords.map((record) => ({
      metric: name,
      standardized_value: `${record.data_year}: ${formatNumber(record.value)} ${record.unit}`,
      source_value: `${record.data_year}: ${originalValueWithUnit(record)}`,
      unit: metadata?.unit || record.unit,
      geography: record.geography,
      scope: `${record.facility}; ${record.lifecycle_boundary}`,
      comparison_note: metadata?.compare || "Check the cited source and align scope before comparing.",
    }));
  });
  renderTable(
    document.querySelector("#measure-inventory-table"),
    tableColumns.measures,
    inventory
  );
}

function renderIntegrity() {
  const { validation, integrity } = dashboardData;
  const passingPackChecks = dashboardData.pack_validation.filter(
    (check) => check.validation_status === "PASS"
  ).length;
  const cards = [
    ["Pipeline validation", `${validation.status} · ${validation.row_count} records`],
    ["Trusted-file hash", integrity.verified ? "MATCH" : "MISMATCH"],
    ["Power BI context checks", `${passingPackChecks} / ${dashboardData.pack_validation.length} PASS`],
    ["Expected SHA-256", integrity.expected_sha256],
    ["Actual SHA-256", integrity.actual_sha256],
  ];
  const container = document.querySelector("#integrity-summary");
  container.replaceChildren();
  for (const [label, value] of cards) {
    const card = make("article", "integrity-card");
    card.append(
      make("span", "integrity-label", label),
      make("span", `integrity-value${label.includes("SHA-256") ? " hash-value" : ""}`, value)
    );
    container.append(card);
  }

  const details = document.querySelector("#validation-details");
  details.replaceChildren();
  details.append(make("p", "", `Validation result: ${validation.error_count} error(s), ${validation.warning_count} warning(s).`));
  for (const issue of [...(validation.errors || []), ...(validation.warnings || [])]) {
    details.append(make("p", "muted", JSON.stringify(issue)));
  }
  details.append(make("p", "muted", integrity.caveat));
  renderTable(
    document.querySelector("#pack-validation-table"),
    [
      ["check_id", "Check"],
      ["check", "Validation"],
      ["actual", "Actual"],
      ["expected", "Expected"],
      ["validation_status", "Status"],
    ],
    dashboardData.pack_validation
  );
}

function renderComparison() {
  const metric = document.querySelector("#comparison-metric").value;
  const basis = document.querySelector("#comparison-value-basis").value;
  const sourceId = document.querySelector("#comparison-source-filter").value;
  const trusted = selectedRecords(
    document.querySelector("#comparison-metric"),
    document.querySelector("#comparison-year"),
    dashboardData.trusted,
    sourceId
  );
  const guideRecords = dashboardData.trusted.filter((record) =>
    record.metric === metric && (!sourceId || record.source_id === sourceId)
  );
  const guide = document.querySelector("#comparison-measure-guide");
  guide.replaceChildren(currentMeasureGuide(metric, guideRecords.length));
  const adversarialById = new Map(dashboardData.adversarial.map((record) => [record.record_id, record]));
  const rows = trusted.map((record) => {
    const altered = adversarialById.get(record.record_id);
    const trustedValue = valueForBasis(record, basis);
    let state = "Unchanged";
    let manipulatedValue = `${trustedValue.value} ${trustedValue.unit}`;
    if (!altered) {
      state = "Removed — not zero";
      manipulatedValue = "Record removed";
    } else if (altered.value !== record.value) {
      state = "Value changed";
      const alteredValue = valueForBasis(altered, basis, record);
      manipulatedValue = `${alteredValue.value} ${alteredValue.unit}`;
    } else if (altered.source_name !== record.source_name) {
      state = altered.source_name ? "Source label changed" : "Source label removed";
    }
    return {
      record_id: record.record_id,
      company: record.company,
      metric: record.metric,
      data_year: record.data_year,
      geography: record.geography,
      facility: record.facility,
      lifecycle_boundary: record.lifecycle_boundary,
      trusted_source: record.source_name,
      simulated_source: altered ? altered.source_name : "",
      trusted_value: `${trustedValue.value} ${trustedValue.unit}`,
      simulated_value: manipulatedValue,
      state,
    };
  });
  const comparisonRecords = document.querySelector("#comparison-records");
  comparisonRecords.replaceChildren();
  if (!rows.length) {
    comparisonRecords.append(make("p", "muted", "No trusted records match this measure and year."));
  }
  for (const row of rows) {
    const card = make("article", "comparison-card");
    const heading = make("h4", "", `${row.record_id} · ${row.company}`);
    const state = make(
      "span",
      `status-pill${row.state.startsWith("Removed") ? " status-warning" : " status-reported"}`,
      row.state
    );
    const header = make("div", "comparison-head");
    header.append(heading, state);
    const context = make(
      "p",
      "comparison-context",
      `${row.data_year} · ${row.geography} · ${row.facility}. Boundary: ${row.lifecycle_boundary}`
    );
    const values = make("div", "comparison-values");
    for (const [label, value] of [
      ["Trusted value", row.trusted_value],
      ["Simulated value", row.simulated_value],
    ]) {
      const item = make("div", "comparison-value");
      item.append(make("span", "summary-label", label), make("span", "summary-value", value));
      values.append(item);
    }
    const sources = make(
      "p",
      "comparison-context",
      `Trusted source: ${displayValue(row.trusted_source)} · Simulated source: ${displayValue(row.simulated_source)}`
    );
    card.append(header, context, values, sources);
    comparisonRecords.append(card);
  }
  const changeLog = document.querySelector("#change-log");
  changeLog.replaceChildren();
  const visibleRecordIds = new Set(trusted.map((record) => record.record_id));
  const visibleChanges = dashboardData.changes.filter((item) => visibleRecordIds.has(item.record_id));
  if (!visibleChanges.length) {
    changeLog.append(make("p", "muted", "No manipulation events match the current report, measure, and year."));
  }
  for (const change of visibleChanges) {
    const card = make("article", "change-card");
    const heading = make("h4", "", `${change.change_id} · ${change.record_id}`);
    const details = document.createElement("dl");
    const sourceRecord = dashboardData.trusted.find((record) => record.record_id === change.record_id);
    let originalEventValue = sourceRecord && change.field === "value"
      ? `${valueForBasis(sourceRecord, basis).value} ${valueForBasis(sourceRecord, basis).unit}`
      : change.original_value;
    let simulatedEventValue = change.manipulated_value;
    if (sourceRecord && change.field === "value") {
      if (basis === "source" && sourceRecord.numeric_value !== 0) {
        const sourceAmount = Number(sourceRecord.original_value)
          * Number(change.manipulated_value) / sourceRecord.numeric_value;
        simulatedEventValue = `${formatNumber(sourceAmount)} ${displayValue(sourceRecord.original_unit)}`;
      } else {
        simulatedEventValue = `${formatNumber(change.manipulated_value)} ${displayValue(sourceRecord.unit)}`;
      }
    } else if (sourceRecord && change.field === "entire row") {
      const sourceAmount = valueForBasis(sourceRecord, basis);
      originalEventValue = `${sourceRecord.metric} = ${sourceAmount.value} ${sourceAmount.unit}`;
    }
    const originalLabel = change.field === "source_name"
      ? "Original source label"
      : change.field === "entire row"
        ? "Original record"
        : `Original value (${basis === "source" ? "source units" : "standardized units"})`;
    const simulatedLabel = change.field === "source_name"
      ? "Simulated source label"
      : change.field === "entire row"
        ? "Simulated record"
        : `Simulated value (${basis === "source" ? "source units" : "standardized units"})`;
    for (const [label, field] of [
      ["Manipulation", "manipulation"],
      ["Field", "field"],
      [originalLabel, "original_value"],
      [simulatedLabel, "manipulated_value"],
      ["Detection evidence", "detection_evidence"],
      ["Defensive control", "defensive_control"],
    ]) {
      const item = document.createElement("div");
      const value = field === "original_value"
        ? originalEventValue
        : field === "manipulated_value"
          ? simulatedEventValue
          : change[field];
      item.append(make("dt", "", label), make("dd", "", displayValue(value)));
      details.append(item);
    }
    card.append(heading, details);
    changeLog.append(card);
  }
}

function refreshComparisonFilters() {
  const sourceId = document.querySelector("#comparison-source-filter").value;
  const scoped = dashboardData.trusted.filter((record) => !sourceId || record.source_id === sourceId);
  const metric = document.querySelector("#comparison-metric").value;
  const metrics = [...new Set(scoped.map((record) => record.metric))].sort();
  const metricSelect = document.querySelector("#comparison-metric");
  if (metrics.length) {
    addOptions(metricSelect, metrics, metrics.includes(metric) ? metric : metrics[0]);
  } else {
    addOptions(metricSelect, [{ value: NO_OBSERVATIONS, label: "No reviewed observations for this report" }], NO_OBSERVATIONS);
  }
  const selectedMetric = metricSelect.value;
  const rows = scoped.filter((record) => record.metric === selectedMetric);
  const years = ["All years", ...new Set(rows.map((record) => record.data_year))]
    .sort((a, b) => a === "All years" ? -1 : b === "All years" ? 1 : Number(a) - Number(b));
  const yearSelect = document.querySelector("#comparison-year");
  addOptions(yearSelect, years, years.includes(yearSelect.value) ? yearSelect.value : "All years");
}

function setView(viewId) {
  for (const panel of document.querySelectorAll(".view-panel")) {
    panel.hidden = panel.id !== viewId;
  }
  const screenSelector = document.querySelector("#screen-selector");
  if (screenSelector.value !== viewId) screenSelector.value = viewId;
}

async function initialize() {
  document.querySelector("#screen-selector").addEventListener("change", (event) => {
    setView(event.currentTarget.value);
  });

  try {
    const dataUrl = document.querySelector('meta[name="dashboard-data"]').content;
    const response = await fetch(dataUrl, { cache: "no-store" });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || `Dashboard data request failed (${response.status}).`);
    dashboardData = payload;
    if (payload.validation.status !== "PASS" || !payload.integrity.verified) {
      const alert = document.querySelector("#integrity-alert");
      const reasons = [];
      if (payload.validation.status !== "PASS") reasons.push("pipeline validation did not pass");
      if (!payload.integrity.verified) reasons.push("trusted-file hash does not match its manifest");
      alert.textContent = `Integrity warning: ${reasons.join(" and ")}. Do not interpret the trusted view until this is investigated.`;
      alert.hidden = false;
    }
    const sourceOptions = [
      { value: "", label: "All registered reports" },
      ...payload.sources.map((source) => ({
        value: source.source_id,
        label: `${source.source_id} · ${source.source_name}`,
      })),
    ];
    for (const selector of ["#report-filter", "#records-source-filter", "#comparison-source-filter"]) {
      addOptions(document.querySelector(selector), sourceOptions, "");
    }
    const metrics = [...new Set(payload.trusted.map((record) => record.metric))].sort();
    addOptions(document.querySelector("#guide-metric"), metrics);
    addOptions(
      document.querySelector("#threat-technique-filter"),
      payload.threat_intel.map((item) => ({
        value: item.technique_id,
        label: `${item.technique_id} · ${item.technique_name}`,
      }))
    );
    addOptions(
      document.querySelector("#control-status-filter"),
      ["All statuses", "Implemented", "Documented manual", "Recommended"]
    );
    addOptions(
      document.querySelector("#response-stage-filter"),
      payload.incident_response.map((item) => item.phase)
    );
    refreshOverviewFilters();
    refreshComparisonFilters();
    refreshContextOptions();
    document.querySelector("#report-filter").addEventListener("change", () => {
      refreshOverviewFilters();
      renderOverview();
    });
    document.querySelector("#metric-filter").addEventListener("change", () => {
      refreshOverviewFilters();
      renderOverview();
    });
    document.querySelector("#year-filter").addEventListener("change", renderOverview);
    document.querySelector("#organization-filter").addEventListener("change", renderOverview);
    document.querySelector("#overview-value-basis").disabled = false;
    document.querySelector("#comparison-value-basis").disabled = false;
    document.querySelector("#overview-value-basis").addEventListener("change", renderOverview);
    document.querySelector("#comparison-source-filter").addEventListener("change", () => {
      refreshComparisonFilters();
      renderComparison();
    });
    document.querySelector("#comparison-metric").addEventListener("change", () => {
      refreshComparisonFilters();
      renderComparison();
    });
    document.querySelector("#comparison-year").addEventListener("change", renderComparison);
    document.querySelector("#comparison-value-basis").addEventListener("change", renderComparison);
    document.querySelector("#record-search").addEventListener("input", renderRecords);
    document.querySelector("#records-source-filter").addEventListener("change", renderRecords);
    document.querySelector("#guide-metric").addEventListener("change", renderMeasureGuide);
    document.querySelector("#context-type-filter").addEventListener("change", refreshContextOptions);
    document.querySelector("#context-item-filter").addEventListener("change", renderDataContext);
    document.querySelector("#threat-technique-filter").addEventListener("change", renderThreatIntel);
    document.querySelector("#control-status-filter").addEventListener("change", renderControls);
    document.querySelector("#response-stage-filter").addEventListener("change", renderIncidentResponse);
    renderExecutiveSummary();
    renderFeatureCoverage();
    renderOverview();
    renderMeasureGuide();
    renderRecords();
    renderThreatIntel();
    renderControls();
    renderIncidentResponse();
    renderIntegrity();
    renderComparison();
  } catch (error) {
    const message = document.querySelector("#load-error");
    message.textContent = `Dashboard data could not be loaded: ${error.message}`;
    message.hidden = false;
  } finally {
    document.querySelector("#loading-message").hidden = true;
  }
}

initialize();
