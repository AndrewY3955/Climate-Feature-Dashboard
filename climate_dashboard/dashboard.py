"""Serve the local source-backed dashboard on loopback only."""

import argparse
import csv
import json
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from climate_dashboard.integrity import verify_manifest

ROOT = Path(__file__).resolve().parents[1]
REVIEWED_DIR = ROOT / "data" / "processed" / "reviewed"
POWERBI_DIR = ROOT / "data" / "powerbi"
UI_DIR = Path(__file__).with_name("dashboard_ui")
STATIC_FILES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/styles.css": ("styles.css", "text/css; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/security-demo.html": ("security-demo.html", "text/html; charset=utf-8"),
    "/security-demo.js": ("security-demo.js", "text/javascript; charset=utf-8"),
    "/security-demo.css": ("security-demo.css", "text/css; charset=utf-8"),
}
REQUIRED_FILES = (
    "trusted_data.csv",
    "trusted_manifest.json",
    "validation_report.json",
    "adversarial_data.csv",
    "adversarial_change_log.csv",
)
CONTEXT_FILES = {
    "project_summary": "project_summary.csv",
    "metric_guide": "metric_guide.csv",
    "sources": "source_register.csv",
    "papers": "research_papers.csv",
    "threat_intel": "threat_intel_reference.csv",
    "controls": "security_controls.csv",
    "incident_response": "incident_response.csv",
    "integrity_summary": "integrity_summary.csv",
    "pack_validation": "table_validation.csv",
}


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def load_dashboard_data(data_dir: str | Path = REVIEWED_DIR) -> dict:
    """Read reviewed dashboard data and curated project context without modifying them."""
    data_dir = Path(data_dir)
    missing = [name for name in REQUIRED_FILES if not (data_dir / name).is_file()]
    if missing:
        raise FileNotFoundError(
            "Dashboard data is incomplete. Missing: "
            + ", ".join(missing)
            + ". Generate the reviewed pipeline and adversarial outputs first."
        )

    context_dir = POWERBI_DIR if data_dir.resolve() == REVIEWED_DIR.resolve() else data_dir / "powerbi"
    missing_context = [
        filename for filename in CONTEXT_FILES.values()
        if not (context_dir / filename).is_file()
    ]
    if missing_context:
        raise FileNotFoundError(
            "Dashboard context is incomplete. Missing: "
            + ", ".join(missing_context)
            + ". Generate the Power BI context pack with the project launcher."
        )

    trusted = _read_csv(data_dir / "trusted_data.csv")
    adversarial = _read_csv(data_dir / "adversarial_data.csv")
    for record in [*trusted, *adversarial]:
        try:
            record["numeric_value"] = float(record["value"])
        except (KeyError, ValueError) as exc:
            raise ValueError(
                f"Dashboard data has an invalid value for record {record.get('record_id', '(unknown)')}."
            ) from exc

    validation = json.loads((data_dir / "validation_report.json").read_text(encoding="utf-8"))
    verified, expected_hash, actual_hash = verify_manifest(
        data_dir / "trusted_data.csv",
        data_dir / "trusted_manifest.json",
    )
    return {
        "dataset_label": "Reviewed source-backed observations",
        "trusted": trusted,
        "adversarial": adversarial,
        "changes": _read_csv(data_dir / "adversarial_change_log.csv"),
        "validation": validation,
        **{
            key: _read_csv(context_dir / filename)
            for key, filename in CONTEXT_FILES.items()
        },
        "integrity": {
            "verified": verified,
            "expected_sha256": expected_hash,
            "actual_sha256": actual_hash,
            "caveat": (
                "This check compares the CSV with its manifest. The manifest must be protected "
                "independently; a matching hash does not prove source accuracy."
            ),
        },
    }


class DashboardHandler(BaseHTTPRequestHandler):
    server_version = "LocalClimateDashboard"

    def _is_local_request(self) -> bool:
        port = self.server.server_port
        allowed_hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
        if self.headers.get("Host", "").lower() not in allowed_hosts:
            return False

        origin = self.headers.get("Origin")
        if origin is None:
            return True
        try:
            parsed_origin = urlsplit(origin)
            origin_port = parsed_origin.port
        except ValueError:
            return False
        return (
            parsed_origin.scheme == "http"
            and parsed_origin.hostname in {"127.0.0.1", "localhost"}
            and origin_port == port
            and parsed_origin.username is None
            and parsed_origin.password is None
        )

    def _send(self, status: int, content_type: str, content: bytes, cache: str = "no-store") -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", cache)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "connect-src 'self'; img-src 'self' data:; object-src 'none'; "
            "base-uri 'none'; frame-ancestors 'none'; form-action 'none'",
        )
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self) -> None:
        if not self._is_local_request():
            self._send(403, "text/plain; charset=utf-8", b"Forbidden")
            return

        route = urlsplit(self.path).path
        if route == "/api/data":
            try:
                payload = json.dumps(load_dashboard_data()).encode("utf-8")
            except FileNotFoundError as exc:
                self._send(
                    503,
                    "application/json; charset=utf-8",
                    json.dumps({"error": str(exc)}).encode("utf-8"),
                )
                return
            except ValueError as exc:
                self._send(
                    422,
                    "application/json; charset=utf-8",
                    json.dumps({"error": str(exc)}).encode("utf-8"),
                )
                return
            self._send(200, "application/json; charset=utf-8", payload)
            return

        static_file = STATIC_FILES.get(route)
        if static_file is None:
            self._send(404, "text/plain; charset=utf-8", b"Not found")
            return
        name, content_type = static_file
        content = (UI_DIR / name).read_bytes()
        self._send(200, content_type, content)

    def do_POST(self) -> None:
        route = urlsplit(self.path).path
        if route != "/api/security-demo/run":
            self._send(404, "text/plain; charset=utf-8", b"Not found")
            return
        if not self._is_local_request() or not self.headers.get("Origin"):
            self._send(403, "text/plain; charset=utf-8", b"Forbidden")
            return
        if self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower() != "application/json":
            self._send(415, "text/plain; charset=utf-8", b"Content-Type must be application/json")
            return
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send(400, "text/plain; charset=utf-8", b"Invalid Content-Length")
            return
        if content_length < 2 or content_length > 1024:
            self._send(413, "text/plain; charset=utf-8", b"Request body must be a small JSON object")
            return
        try:
            request_body = json.loads(self.rfile.read(content_length))
            if request_body != {}:
                self._send(400, "text/plain; charset=utf-8", b"Unexpected request fields")
                return
            from climate_dashboard.security_demo import run_security_demo

            result = run_security_demo()
            payload = json.dumps(result).encode("utf-8")
            self._send(200 if result["status"] == "PASS" else 503, "application/json; charset=utf-8", payload)
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._send(400, "text/plain; charset=utf-8", b"Invalid JSON request")
        except FileNotFoundError as exc:
            self._send(503, "application/json; charset=utf-8", json.dumps({"error": str(exc)}).encode("utf-8"))
        except (OSError, ValueError) as exc:
            self._send(422, "application/json; charset=utf-8", json.dumps({"error": str(exc)}).encode("utf-8"))

    def log_message(self, format: str, *args: object) -> None:
        print(f"{self.address_string()} - {format % args}")


def serve(port: int = 8765, open_browser: bool = False) -> None:
    if not 1 <= port <= 65535:
        raise ValueError("port must be between 1 and 65535")

    server = ThreadingHTTPServer(("127.0.0.1", port), DashboardHandler)
    url = f"http://127.0.0.1:{port}/"
    print(f"Dashboard available at {url} (loopback only; Ctrl+C to stop)")
    if open_browser and not webbrowser.open(url):
        print("Could not open a browser automatically; open the URL above manually.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping dashboard.")
    finally:
        server.server_close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve the local climate-feature dashboard.")
    parser.add_argument("--port", type=int, default=8765, help="Local HTTP port (default: 8765)")
    parser.add_argument(
        "--open-browser",
        action="store_true",
        help="Open the dashboard URL in the default browser after the server starts.",
    )
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("--port must be between 1 and 65535")
    serve(args.port, args.open_browser)


if __name__ == "__main__":
    main()
