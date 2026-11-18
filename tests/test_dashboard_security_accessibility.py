from html.parser import HTMLParser
from pathlib import Path

from climate_dashboard.pipeline import ROOT


UI = ROOT / "climate_dashboard" / "dashboard_ui"


class SecurityMarkupParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.inline_scripts = 0
        self.inline_styles = 0
        self.meta = {}

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "script" and not values.get("src"):
            self.inline_scripts += 1
        if tag == "style":
            self.inline_styles += 1
        if tag == "meta" and values.get("http-equiv", "").lower() == "content-security-policy":
            self.meta["csp"] = values.get("content", "")


def test_static_dashboard_has_restrictive_meta_content_security_policy():
    parser = SecurityMarkupParser()
    parser.feed((UI / "index.html").read_text(encoding="utf-8"))

    policy = parser.meta.get("csp", "")
    assert policy
    assert "default-src 'self'" in policy
    assert "script-src 'self'" in policy
    assert "style-src 'self'" in policy
    assert "connect-src 'self'" in policy
    assert "object-src 'none'" in policy
    assert "base-uri 'none'" in policy
    assert "'unsafe-inline'" not in policy
    assert parser.inline_scripts == 0
    assert parser.inline_styles == 0


def test_dashboard_has_keyboard_focus_and_accessible_live_status_regions():
    html = (UI / "index.html").read_text(encoding="utf-8")
    css = (UI / "styles.css").read_text(encoding="utf-8")
    assert 'href="#main-content"' in html
    assert 'id="main-content"' in html
    assert 'id="context-result-count" class="chart-note" role="status" aria-live="polite"' in html
    assert 'id="records-result-count" class="chart-note" role="status" aria-live="polite"' in html
    assert 'id="control-result-count" class="chart-note" role="status" aria-live="polite"' in html
    assert ":focus-visible" in css
    assert "overflow-x: auto" in css
    assert "@media (max-width: 420px)" in css


def test_reports_and_studies_exposes_all_review_fields_and_safe_doi_links():
    script = (UI / "app.js").read_text(encoding="utf-8")
    assert '["DOI / stable URL", paper.doi_or_stable_url]' in script
    assert 'addSafeLink(linkArea, paper.doi_or_stable_url, "Open DOI / stable publisher record")' in script
    assert 'payload.papers.length < 5' in script
    assert 'paper.peer_review_evidence' in script
    assert 'paper.limitations' in script
    assert 'options[0]?.value' in script


def test_security_controls_enforce_expected_inventory_and_scope_counts():
    script = (UI / "app.js").read_text(encoding="utf-8")
    assert 'payload.controls.length !== 9' in script
    assert 'controlCounts.Implemented !== 6' in script
    assert 'controlCounts["Documented manual"] !== 1' in script
    assert 'controlCounts.Recommended !== 2' in script
    assert 'Showing ${controls.length} of ${dashboardData.controls.length} documented controls' in script


def test_dashboard_avoids_html_string_injection_and_uses_safe_external_links():
    script = (UI / "app.js").read_text(encoding="utf-8")
    assert ".innerHTML" not in script
    assert "insertAdjacentHTML" not in script
    assert "eval(" not in script
    assert "new Function(" not in script
    assert 'link.rel = "noopener noreferrer"' in script
    assert 'parsed.protocol !== "https:"' in script


def test_dashboard_exposes_csv_export_and_print_styles():
    html = (UI / "index.html").read_text(encoding="utf-8")
    css = (UI / "styles.css").read_text(encoding="utf-8")
    script = (UI / "app.js").read_text(encoding="utf-8")
    assert 'id="download-records-csv"' in html
    assert 'id="print-current-view"' in html
    assert "@media print" in css
    assert "overflow: visible !important" in css
    assert "function downloadCsv(filename, rows)" in script
    assert 'replace(/"/g' in script
    assert 'link.download = filename' in script
