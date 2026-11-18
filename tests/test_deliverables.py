from html.parser import HTMLParser
from pathlib import Path
import re

from climate_dashboard.pipeline import ROOT


class DashboardParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.sections = []
        self.assets = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if "id" in attributes:
            self.ids.append(attributes["id"])
        if tag == "section" and "view-panel" in attributes.get("class", "").split():
            self.sections.append(attributes.get("id"))
        if tag == "link" and attributes.get("rel") == "stylesheet":
            self.assets.append(attributes.get("href"))
        if tag == "script" and attributes.get("src"):
            self.assets.append(attributes["src"])


def test_final_report_covers_all_assignment_sections():
    report = (ROOT / "docs" / "final_report.md").read_text(encoding="utf-8")
    sections = re.findall(r"^## (\d+)\. ", report, re.MULTILINE)

    assert sections == [str(index) for index in range(1, 32)]
    assert "controlled classroom simulation" in report.lower()
    assert "not a representative semiconductor-industry sample" in report.lower()
    assert "no live threat feed" in report.lower()


def test_dashboard_uses_one_screen_dropdown_for_all_views():
    dashboard_dir = ROOT / "climate_dashboard" / "dashboard_ui"
    html = (dashboard_dir / "index.html").read_text(encoding="utf-8")
    parser = DashboardParser()
    parser.feed(html)
    ids = set(parser.ids)

    assert len(parser.ids) == len(ids), "Dashboard element IDs must be unique."
    expected_screens = {
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
    }
    assert len(parser.sections) == len(expected_screens)
    assert set(parser.sections) == expected_screens
    assert 'role="tablist"' not in html
    assert 'role="tab"' not in html

    selector = re.search(r'<select id="screen-selector">(.*?)</select>', html, re.DOTALL)
    assert selector
    options = set(re.findall(r'<option value="([^"]+)"', selector.group(1)))
    assert options == expected_screens

    script = (dashboard_dir / "app.js").read_text(encoding="utf-8")
    queried_ids = set(re.findall(r'document\.querySelector\("#([^"]+)"\)', script))
    assert queried_ids <= ids
    assert all((dashboard_dir / asset.lstrip("/")).is_file() for asset in parser.assets)


def test_demo_runbook_documents_dashboard_not_deleted_slideshow():
    runbook = (ROOT / "docs" / "demo_runbook.md").read_text(encoding="utf-8").lower()

    assert "screen" in runbook and "dropdown" in runbook
    assert "adversarial comparison" in runbook
    assert "power bi" in runbook
    assert "presentation/index.html" not in runbook
