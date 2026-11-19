from __future__ import annotations

import http.client
import json
from http.server import ThreadingHTTPServer
from threading import Thread

from climate_dashboard.dashboard import DashboardHandler


def _request(port, origin, body=b"{}"):
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
    headers = {
        "Host": f"127.0.0.1:{port}",
        "Content-Type": "application/json",
        "Content-Length": str(len(body)),
    }
    if origin is not None:
        headers["Origin"] = origin
    connection.request("POST", "/api/security-demo/run", body=body, headers=headers)
    response = connection.getresponse()
    status = response.status
    payload = response.read()
    connection.close()
    return status, payload


def test_security_demo_endpoint_accepts_only_local_same_origin(monkeypatch):
    import climate_dashboard.security_demo

    monkeypatch.setattr(
        climate_dashboard.security_demo,
        "run_security_demo",
        lambda: {"status": "PASS", "summary": {"security_test_count": 1}},
    )
    server = ThreadingHTTPServer(("127.0.0.1", 0), DashboardHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_port
    try:
        status, payload = _request(port, f"http://127.0.0.1:{port}")
        assert status == 200
        assert json.loads(payload)["status"] == "PASS"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def test_security_demo_endpoint_rejects_external_or_missing_origin():
    server = ThreadingHTTPServer(("127.0.0.1", 0), DashboardHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_port
    try:
        assert _request(port, f"http://attacker.example:{port}")[0] == 403
        assert _request(port, None)[0] == 403
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def test_security_demo_endpoint_rejects_unexpected_request_fields(monkeypatch):
    import climate_dashboard.security_demo

    monkeypatch.setattr(
        climate_dashboard.security_demo,
        "run_security_demo",
        lambda: {"status": "PASS"},
    )
    server = ThreadingHTTPServer(("127.0.0.1", 0), DashboardHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_port
    try:
        status, _ = _request(port, f"http://127.0.0.1:{port}", b'{"command":"arbitrary"}')
        assert status == 400
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)



def test_security_demo_endpoint_returns_actionable_error_when_dependency_missing(monkeypatch):
    import builtins

    original_import = builtins.__import__

    def fail_security_demo_import(name, *args, **kwargs):
        if name == "climate_dashboard.security_demo":
            raise ModuleNotFoundError("No module named 'cryptography'", name="cryptography")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fail_security_demo_import)
    server = ThreadingHTTPServer(("127.0.0.1", 0), DashboardHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_port
    try:
        status, payload = _request(port, f"http://127.0.0.1:{port}")
        assert status == 503
        result = json.loads(payload)
        assert "cryptography" in result["error"]
        assert "run.ps1" in result["error"]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def test_active_defense_endpoint_runs_live_lab_on_local_same_origin(monkeypatch):
    import climate_dashboard.active_defense_lab

    monkeypatch.setattr(
        climate_dashboard.active_defense_lab,
        "run_active_defense_lab",
        lambda: {"status": "PASS", "outcome": "PREVENTED_AND_DETECTED_ROLLED_BACK"},
    )
    server = ThreadingHTTPServer(("127.0.0.1", 0), DashboardHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_port
    try:
        status, payload = _active_request(port, f"http://127.0.0.1:{port}")
        assert status == 200
        result = json.loads(payload)
        assert result["status"] == "PASS"
        assert result["outcome"] == "PREVENTED_AND_DETECTED_ROLLED_BACK"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def _active_request(port, origin):
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
    body = b"{}"
    connection.request(
        "POST",
        "/api/active-defense-lab/run",
        body=body,
        headers={
            "Host": f"127.0.0.1:{port}",
            "Origin": origin,
            "Content-Type": "application/json",
            "Content-Length": str(len(body)),
        },
    )
    response = connection.getresponse()
    result = response.status, response.read()
    connection.close()
    return result
