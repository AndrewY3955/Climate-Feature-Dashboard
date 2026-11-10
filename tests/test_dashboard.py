import csv
import http.client
import json
import subprocess
import sys
from http.server import ThreadingHTTPServer
from threading import Thread

import pytest

from climate_dashboard.dashboard import DashboardHandler, load_dashboard_data
from climate_dashboard.integrity import write_manifest
from climate_dashboard.launcher import _dashboard_is_running
from climate_dashboard.powerbi_export import build_powerbi_pack


def write_csv(path, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def create_context_pack(data_dir):
    build_powerbi_pack(data_dir, data_dir / "powerbi")


def test_dashboard_loads_source_data_and_verifies_trusted_manifest(tmp_path):
    trusted = [{
        "record_id": "OBS001",
        "company": "TSMC",
        "facility": "Company operations",
        "geography": "Global",
        "metric": "Total energy consumption",
        "value": "27456000.0",
        "unit": "MWh",
        "data_year": "2024",
        "source_name": "Example report",
        "source_url": "https://esg.tsmc.com/en-US/file/public/2024-TSMC-Sustainability-Report-e.pdf",
        "source_id": "SRC001",
        "data_status": "reported",
    }]
    write_csv(tmp_path / "trusted_data.csv", trusted)
    write_manifest(
        tmp_path / "trusted_data.csv",
        tmp_path / "trusted_manifest.json",
        "test trusted data",
    )
    write_csv(tmp_path / "adversarial_data.csv", trusted)
    write_csv(tmp_path / "adversarial_change_log.csv", [{
        "change_id": "ADV-TEST",
        "record_id": "OBS001",
        "manipulation": "test",
    }])
    (tmp_path / "validation_report.json").write_text(
        json.dumps({"status": "PASS", "row_count": 1, "error_count": 0, "warning_count": 0}),
        encoding="utf-8",
    )
    create_context_pack(tmp_path)

    payload = load_dashboard_data(tmp_path)

    assert payload["trusted"][0]["value"] == "27456000.0"
    assert payload["trusted"][0]["numeric_value"] == 27456000.0
    assert payload["integrity"]["verified"] is True
    assert payload["changes"][0]["change_id"] == "ADV-TEST"
    assert len(payload["sources"]) == 5
    assert len(payload["papers"]) == 5
    assert len(payload["threat_intel"]) == 3
    assert len(payload["controls"]) == 8
    assert len(payload["incident_response"]) == 6


def test_dashboard_rejects_incomplete_data_directory(tmp_path):
    with pytest.raises(FileNotFoundError, match="Dashboard data is incomplete"):
        load_dashboard_data(tmp_path)


def test_importing_dashboard_does_not_load_pandas():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; import climate_dashboard.dashboard; "
            "print('pandas' in sys.modules)",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout.strip() == "False"


def test_dashboard_reports_manifest_mismatch(tmp_path):
    trusted = [{
        "record_id": "OBS001",
        "company": "TSMC",
        "facility": "Company operations",
        "geography": "Global",
        "metric": "Total energy consumption",
        "value": "10",
        "unit": "MWh",
        "data_year": "2024",
        "source_name": "Example report",
        "source_url": "https://esg.tsmc.com/en-US/file/public/2024-TSMC-Sustainability-Report-e.pdf",
        "source_id": "SRC001",
        "data_status": "reported",
    }]
    write_csv(tmp_path / "trusted_data.csv", trusted)
    write_manifest(tmp_path / "trusted_data.csv", tmp_path / "trusted_manifest.json", "test")
    write_csv(tmp_path / "adversarial_data.csv", trusted)
    write_csv(tmp_path / "adversarial_change_log.csv", [{
        "change_id": "ADV-TEST",
        "record_id": "OBS001",
        "manipulation": "test",
    }])
    (tmp_path / "validation_report.json").write_text(
        json.dumps({"status": "PASS", "row_count": 1, "error_count": 0, "warning_count": 0}),
        encoding="utf-8",
    )
    create_context_pack(tmp_path)
    with (tmp_path / "trusted_data.csv").open("a", encoding="utf-8") as stream:
        stream.write("\n")

    payload = load_dashboard_data(tmp_path)

    assert payload["integrity"]["verified"] is False
    assert payload["integrity"]["expected_sha256"] != payload["integrity"]["actual_sha256"]


def test_launcher_recognizes_dashboard_page(monkeypatch):
    class Response:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def read(self):
            return b"<title>Semiconductor Climate Data Dashboard</title>"

    monkeypatch.setattr("urllib.request.urlopen", lambda *_args, **_kwargs: Response())

    assert _dashboard_is_running("http://127.0.0.1:8765/")


def test_launcher_rejects_unrelated_page(monkeypatch):
    class Response:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def read(self):
            return b"<title>Unrelated application</title>"

    monkeypatch.setattr("urllib.request.urlopen", lambda *_args, **_kwargs: Response())

    assert not _dashboard_is_running("http://127.0.0.1:8765/")


def test_dashboard_rejects_untrusted_host_and_origin(monkeypatch):
    monkeypatch.setattr(
        "climate_dashboard.dashboard.load_dashboard_data",
        lambda: {"status": "ok"},
    )
    server = ThreadingHTTPServer(("127.0.0.1", 0), DashboardHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_port

    def request(headers):
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
        connection.request("GET", "/api/data", headers=headers)
        response = connection.getresponse()
        status = response.status
        body = response.read()
        connection.close()
        return status, body

    try:
        assert request({"Host": f"attacker.example:{port}"})[0] == 403
        assert request({
            "Host": f"127.0.0.1:{port}",
            "Origin": f"http://attacker.example:{port}",
        })[0] == 403
        assert request({
            "Host": f"127.0.0.1:{port}",
            "Origin": f"http://127.0.0.1:{port}",
        }) == (200, b'{"status": "ok"}')
        assert request({"Host": f"127.0.0.1:{port}"}) == (200, b'{"status": "ok"}')
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
