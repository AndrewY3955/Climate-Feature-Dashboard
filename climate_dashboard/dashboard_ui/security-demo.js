"use strict";

const runButton = document.querySelector("#run-all");
const statusLine = document.querySelector("#run-status");
const results = document.querySelector("#results");

const isLocalDemo = ["127.0.0.1", "localhost"].includes(window.location.hostname);
if (!isLocalDemo || document.documentElement.dataset.demoMode === "read-only") {
  runButton.disabled = true;
  statusLine.textContent = "This GitHub Pages copy is read-only. Start the local dashboard with .\\\\run.ps1 (Windows) or sh ./run.sh, then open the Security Demo Center on 127.0.0.1 to execute the tests.";
}

function cell(row, value, className = "") {
  const element = document.createElement("td");
  element.textContent = value === null || value === undefined ? "" : String(value);
  if (className) element.className = className;
  row.append(element);
}

function statusClass(status) {
  if (status === "PASS" || status === "COMPLETE" || status === "VERIFIED" || status === "DETECTED" || status === "EXERCISED") return "pass";
  if (status === "TABLETOP ONLY" || status === "NOT APPLICABLE") return "limited";
  return "fail";
}

function addSummary(container, label, value) {
  const card = document.createElement("article");
  card.className = "summary-card";
  const heading = document.createElement("span");
  heading.className = "summary-label";
  heading.textContent = label;
  const result = document.createElement("strong");
  result.textContent = String(value);
  card.append(heading, result);
  container.append(card);
}

function renderTests(items) {
  const body = document.querySelector("#tests-table tbody");
  body.replaceChildren();
  for (const item of items) {
    const row = document.createElement("tr");
    cell(row, item.name);
    cell(row, item.status, statusClass(item.status));
    cell(row, item.detail);
    body.append(row);
  }
}

function renderScenarios(items) {
  const list = document.querySelector("#scenario-list");
  list.replaceChildren();
  for (const scenario of items) {
    const card = document.createElement("article");
    card.className = "scenario-card";
    const heading = document.createElement("div");
    heading.className = "scenario-heading";
    const title = document.createElement("h4");
    title.textContent = scenario.title;
    const badge = document.createElement("span");
    badge.className = "status " + statusClass(scenario.status);
    badge.textContent = scenario.status;
    heading.append(title, badge);
    card.append(heading);
    const mapping = document.createElement("p");
    mapping.className = "muted";
    mapping.textContent = scenario.technique_id + " · " + scenario.technique_name;
    const description = document.createElement("p");
    description.textContent = scenario.description;
    const vector = document.createElement("p");
    vector.className = "scenario-evidence";
    vector.textContent = "ATTACK VECTOR: " + (scenario.attack_vector || "Not specified");
    const changed = document.createElement("p");
    changed.className = "scenario-evidence";
    changed.textContent = "WHAT CHANGED: " + (scenario.simulated_change || "No technical change; tabletop assumption.");
    const detail = document.createElement("p");
    detail.textContent = "OBSERVED DEMO EVIDENCE: " + (scenario.detail || scenario.detection || "No technical detection was performed.");
    const defense = document.createElement("p");
    defense.className = "control-note";
    defense.textContent = "DEFENSE USED / CONTROL: " + (scenario.defense_used || scenario.control);
    const outcome = document.createElement("p");
    outcome.className = "scenario-result";
    outcome.textContent = "RESULT: " + (scenario.result || scenario.result_basis || scenario.status);
    card.append(mapping, description, vector, changed, detail, defense, outcome);
    if (scenario.phases?.length) {
      const phaseTitle = document.createElement("h5");
      phaseTitle.textContent = "Incident-response phases";
      card.append(phaseTitle);
      const phases = document.createElement("ol");
      phases.className = "phase-list";
      for (const phase of scenario.phases) {
        const item = document.createElement("li");
        const strong = document.createElement("strong");
        strong.textContent = phase.phase + " — " + phase.status;
        const note = document.createElement("span");
        note.textContent = phase.action;
        item.append(strong, note);
        phases.append(item);
      }
      card.append(phases);
    }
    const control = document.createElement("p");
    control.className = "control-note";
    control.textContent = "Defensive control: " + scenario.control;
    card.append(control);
    list.append(card);
  }
}

function renderComparability(data) {
  const summary = document.querySelector("#comparison-summary");
  summary.replaceChildren();
  for (const [label, value] of Object.entries(data.counts)) addSummary(summary, label, value);
  const body = document.querySelector("#comparison-table tbody");
  body.replaceChildren();
  for (const pair of data.pairs) {
    const row = document.createElement("tr");
    cell(row, pair.left_record);
    cell(row, pair.right_record);
    cell(row, pair.status, pair.status === "DIRECTLY COMPARABLE" ? "pass" : "limited");
    cell(row, pair.reasons.join(" "));
    body.append(row);
  }
}

function render(payload) {
  results.hidden = false;
  const summary = document.querySelector("#summary");
  summary.replaceChildren();
  const values = [
    ["Overall result", payload.status],
    ["Trusted records", payload.summary.trusted_records],
    ["Security tests", payload.summary.security_tests_passed + " / " + payload.summary.security_test_count],
    ["Scenarios", payload.summary.attack_scenarios_exercised],
    ["Technical scenarios passed", payload.summary.technical_scenarios_passed],
    ["Tabletop-only scenarios", payload.summary.tabletop_scenarios],
    ["Response phases per scenario", payload.summary.response_phases_per_scenario],
  ];
  for (const [label, value] of values) addSummary(summary, label, value);
  renderTests(payload.tests);
  renderScenarios(payload.scenarios);
  renderComparability(payload.comparability);
  const limitations = document.querySelector("#limitations");
  limitations.replaceChildren();
  for (const note of payload.security_boundary) {
    const item = document.createElement("li");
    item.textContent = note;
    limitations.append(item);
  }
  statusLine.textContent = payload.status === "PASS"
    ? "Complete: all automated checks and technical scenarios passed. Review the tabletop-only and deployment limitations below."
    : "The run completed with one or more failures. Review the evidence and do not present the demo as passing.";
}

runButton.addEventListener("click", async () => {
  runButton.disabled = true;
  results.hidden = true;
  statusLine.textContent = "Running validation, cryptographic checks, scenario simulations, and recovery exercises…";
  try {
    const response = await fetch("/api/security-demo/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: "{}",
      cache: "no-store",
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || "Security demonstration failed with HTTP " + response.status);
    render(payload);
  } catch (error) {
    statusLine.textContent = "Unable to complete the demonstration: " + error.message;
  } finally {
    runButton.disabled = false;
  }
});
