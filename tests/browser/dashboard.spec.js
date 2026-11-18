const { test, expect } = require("@playwright/test");
const fs = require("node:fs");
const AxeBuilder = require("@axe-core/playwright").default;

const viewIds = [
  "view-summary",
  "view-overview",
  "view-measures",
  "view-feature-coverage",
  "view-records",
  "view-context",
  "view-threats",
  "view-controls",
  "view-response",
  "view-integrity",
  "view-comparison",
];

test.beforeEach(async ({ page }) => {
  await page.goto("/");
  await expect(page.locator("#loading-message")).toBeHidden();
});

test("all eleven dashboard views render and route correctly", async ({ page }) => {
  for (const viewId of viewIds) {
    await page.locator("#screen-selector").selectOption(viewId);
    await expect(page.locator(`#${viewId}`)).toBeVisible();
    await expect(page.locator(`#${viewId} h2`)).toBeVisible();
    expect(new URL(page.url()).hash).toBe(`#${viewId}`);
  }
});

test("Reports and Studies supports every research paper and report selection", async ({ page }) => {
  await page.locator("#screen-selector").selectOption("view-context");
  await page.locator("#context-type-filter").selectOption("papers");
  const paperSelect = page.locator("#context-item-filter");
  await expect(paperSelect.locator("option")).toHaveCount(5);
  await expect(paperSelect).toHaveValue("PAP001");
  await expect(page.locator("#context-table tbody tr")).toHaveCount(5);

  for (const paperId of ["PAP001", "PAP002", "PAP003", "PAP004", "PAP005"]) {
    await paperSelect.selectOption(paperId);
    await expect(page.locator("#context-detail h3")).toContainText(paperId);
    await expect(page.locator("#context-detail a[href^='https://doi.org/']")).toHaveCount(1);
    for (const label of [
      "Research objective",
      "Semiconductor feature",
      "Data and variables",
      "Environmental impact",
      "Main findings",
      "Limitations",
      "Dashboard relevance",
      "Review status",
      "Peer-review evidence",
    ]) {
      await expect(page.locator("#context-detail")).toContainText(label);
    }
  }

  await page.locator("#context-type-filter").selectOption("sources");
  await expect(page.locator("#context-item-filter option")).toHaveCount(5);
  await expect(page.locator("#context-item-filter")).toHaveValue("SRC001");
  await expect(page.locator("#context-detail h3")).toContainText("SRC001");
  await expect(page.locator("#context-detail a[href^='https://']")).toHaveCount(1);
});

test("security controls show exact status totals and filter correctly", async ({ page }) => {
  await page.locator("#screen-selector").selectOption("view-controls");
  await expect(page.locator("#control-cards .context-card")).toHaveCount(9);
  await expect(page.locator("#control-summary .summary-value").nth(0)).toHaveText("6");
  await expect(page.locator("#control-summary .summary-value").nth(1)).toHaveText("1");
  await expect(page.locator("#control-summary .summary-value").nth(2)).toHaveText("2");
  await expect(page.locator("#control-cards")).toContainText("CTRL-09");
  await expect(page.locator("#control-cards")).toContainText("standalone demo utility");

  for (const [status, count] of [
    ["Implemented", 6],
    ["Documented manual", 1],
    ["Recommended", 2],
  ]) {
    await page.locator("#control-status-filter").selectOption(status);
    await expect(page.locator("#control-cards .context-card")).toHaveCount(count);
  }
  await page.locator("#control-status-filter").selectOption("All statuses");
  await expect(page.locator("#control-cards .context-card")).toHaveCount(9);
});

test("records search and source filters return correct result counts", async ({ page }) => {
  await page.locator("#screen-selector").selectOption("view-records");
  await expect(page.locator("#records-table tbody tr")).toHaveCount(7);
  await page.locator("#record-search").fill("OBS005");
  await expect(page.locator("#records-table tbody tr")).toHaveCount(1);
  await expect(page.locator("#records-table")).toContainText("OBS005");
  await expect(page.locator("#records-result-count")).toContainText("1 of 7");
  await page.locator("#record-search").fill("no-such-record");
  await expect(page.locator("#records-table tbody tr")).toHaveCount(1);
  await expect(page.locator("#records-table tbody tr")).toContainText("No records match");
  await expect(page.locator("#records-result-count")).toContainText("0 of 7");
  await page.locator("#record-search").fill("");
  await page.locator("#records-source-filter").selectOption("SRC001");
  await expect(page.locator("#records-table tbody tr")).toHaveCount(4);
});

test("filtered trusted records export to a valid UTF-8 CSV download", async ({ page }) => {
  await page.locator("#screen-selector").selectOption("view-records");
  await page.locator("#record-search").fill("OBS005");
  const [download] = await Promise.all([
    page.waitForEvent("download"),
    page.locator("#download-records-csv").click(),
  ]);
  expect(download.suggestedFilename()).toBe("trusted-records-filtered.csv");
  const filePath = await download.path();
  const csv = fs.readFileSync(filePath, "utf8");
  expect(csv.startsWith("\\uFEFF")).toBe(true);
  expect(csv).toContain("OBS005");
  expect(csv).not.toContain("OBS001");
});

test("print layout hides controls and expands wide tables", async ({ page }) => {
  await page.locator("#screen-selector").selectOption("view-records");
  await page.emulateMedia({ media: "print" });
  const printStyles = await page.evaluate(() => ({
    overflow: getComputedStyle(document.querySelector(".table-scroll")).overflow,
    picker: getComputedStyle(document.querySelector(".screen-picker")).display,
    activeView: getComputedStyle(document.querySelector("#view-records")).display,
    inactiveView: getComputedStyle(document.querySelector("#view-overview")).display,
  }));
  expect(printStyles.overflow).toBe("visible");
  expect(printStyles.picker).toBe("none");
  expect(printStyles.activeView).not.toBe("none");
  expect(printStyles.inactiveView).toBe("none");
});

test("deep links select a valid view and invalid hashes fall back safely", async ({ page, baseURL }) => {
  await page.goto(`${baseURL}/#view-overview`);
  await expect(page.locator("#view-overview")).toBeVisible();
  await page.goto(`${baseURL}/#not-a-dashboard-view`);
  await expect(page.locator("#view-summary")).toBeVisible();
  expect(new URL(page.url()).hash).toBe("#view-summary");
});

test("records search treats hostile-looking input as inert text", async ({ page }) => {
  await page.locator("#screen-selector").selectOption("view-records");
  const probe = "<img src=x onerror=window.__xssProbe=1>";
  await page.locator("#record-search").fill(probe);
  await expect(page.locator("#records-table img")).toHaveCount(0);
  expect(await page.evaluate(() => window.__xssProbe)).toBeUndefined();
  await expect(page.locator("#records-result-count")).toContainText("0 of 7");
});

test("security policy blocks inline script execution", async ({ page }) => {
  await page.addScriptTag({ content: "window.__inlineCspProbe = true;" }).catch(() => {});
  expect(await page.evaluate(() => window.__inlineCspProbe)).toBeUndefined();
});

test("security policy is present and no runtime or console errors occur", async ({ page }) => {
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
  });
  await page.reload();
  await expect(page.locator("#loading-message")).toBeHidden();
  const policy = await page.locator('meta[http-equiv="Content-Security-Policy"]').getAttribute("content");
  expect(policy).toContain("default-src 'self'");
  expect(policy).toContain("script-src 'self'");
  expect(policy).toContain("object-src 'none'");
  for (const viewId of viewIds) {
    await page.locator("#screen-selector").selectOption(viewId);
    await expect(page.locator(`#${viewId}`)).toBeVisible();
  }
  expect(errors).toEqual([]);
});

test("mobile, tablet, and desktop layouts do not overflow the viewport", async ({ page }) => {
  for (const viewport of [
    { width: 375, height: 812 },
    { width: 390, height: 844 },
    { width: 768, height: 1024 },
    { width: 1024, height: 768 },
    { width: 1440, height: 900 },
  ]) {
    await page.setViewportSize(viewport);
    for (const viewId of viewIds) {
      await page.locator("#screen-selector").selectOption(viewId);
      const dimensions = await page.evaluate(() => ({
        viewport: window.innerWidth,
        document: document.documentElement.scrollWidth,
        body: document.body.scrollWidth,
      }));
      expect(dimensions.document, `${viewId} at ${viewport.width}px`).toBeLessThanOrEqual(dimensions.viewport);
      expect(dimensions.body, `${viewId} at ${viewport.width}px`).toBeLessThanOrEqual(dimensions.viewport);
    }
  }
});

test("keyboard users can skip navigation and reach labeled dashboard controls", async ({ page }) => {
  await page.evaluate(() => document.activeElement.blur());
  await page.keyboard.press("Tab");
  await expect(page.locator(".skip-link")).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.locator("#main-content")).toBeFocused();
  await page.keyboard.press("Tab");
  await expect(page.locator("#screen-selector")).toBeFocused();
  const outline = await page.locator("#screen-selector").evaluate((element) => getComputedStyle(element).outlineStyle);
  expect(outline).not.toBe("none");
  await page.getByLabel("Dashboard screen").selectOption("view-context");
  await expect(page.locator("#view-context")).toBeVisible();
  await expect(page.getByLabel("Information type")).toBeEnabled();
});

test("keyboard tab order reaches every visible control in every dashboard view", async ({ page }) => {
  for (const viewId of viewIds) {
    await page.locator("#screen-selector").selectOption(viewId);
    const expected = await page.evaluate(() => {
      const candidates = Array.from(document.querySelectorAll(
        'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
      )).filter((element) => !element.closest("[hidden]") && element.getClientRects().length > 0);
      candidates.forEach((element, index) => element.setAttribute("data-qa-tab-index", String(index)));
      return candidates.length;
    });
    expect(expected, `Focusable controls in ${viewId}`).toBeGreaterThan(0);
    await page.evaluate(() => document.activeElement.blur());
    const visited = new Set();
    for (let step = 0; step < expected + 1; step += 1) {
      await page.keyboard.press("Tab");
      const index = await page.evaluate(() => document.activeElement.getAttribute("data-qa-tab-index"));
      if (index !== null) visited.add(index);
    }
    expect(visited.size, `Keyboard traversal coverage in ${viewId}`).toBe(expected);
  }
});

test("visible views pass automated WCAG 2.1 AA accessibility checks", async ({ browser, baseURL }) => {
  // Axe injects its own script. Use a separate test-only context with CSP bypass;
  // the normal application context is independently tested for CSP enforcement above.
  const context = await browser.newContext({ bypassCSP: true, baseURL });
  const page = await context.newPage();
  try {
    await page.goto("/");
    await expect(page.locator("#loading-message")).toBeHidden();
    for (const viewId of viewIds) {
      await page.locator("#screen-selector").selectOption(viewId);
      await expect(page.locator(`#${viewId}`)).toBeVisible();
      const results = await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
        .analyze();
      expect(
        results.violations.map((violation) => ({
          id: violation.id,
          impact: violation.impact,
          description: violation.description,
          nodes: violation.nodes.map((node) => node.target),
        })),
        `Accessibility violations in ${viewId}`
      ).toEqual([]);
    }
  } finally {
    await context.close();
  }
});
