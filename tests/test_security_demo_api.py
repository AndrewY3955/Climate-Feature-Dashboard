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
