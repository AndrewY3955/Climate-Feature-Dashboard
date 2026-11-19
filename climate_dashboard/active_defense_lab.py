"""Live, loopback-only active-defense lab with real HTTP attacker traffic.

The lab uses disposable in-memory records and a short-lived local HTTP service.
The attacker is a separate Python process. The target enforces authorization and
record-protection policy before mutation, revokes the offending lab token, and
emits a hash-chained audit trail. No production files or external hosts are used.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import subprocess
import sys
import tempfile
import threading
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "evidence" / "active-defense-lab"
LAB_RECORD_ID = "OBS-LAB-001"
LAB_WORKING_RECORD_ID = "OBS-LAB-WORKING-001"
LAB_BASELINE = {
    LAB_RECORD_ID: {
        "record_id": LAB_RECORD_ID,
        "metric": "Total energy consumption",
        "value": 100.0,
        "unit": "MWh",
        "source_name": "Synthetic isolated-lab fixture",
        "protected": True,
    },
    LAB_WORKING_RECORD_ID: {
        "record_id": LAB_WORKING_RECORD_ID,
        "metric": "Water recycled from recovery systems",
        "value": 50.0,
        "unit": "m3",
        "source_name": "Synthetic isolated working-copy fixture",
        "protected": False,
    },
}

ATTACKER_SCRIPT = r'''
import json, os, sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError

base, protected_token, editor_token = sys.argv[1], sys.argv[2], sys.argv[3]
pid = os.getpid()
results = []

def call(method, path, token, body=None):
    data = None if body is None else json.dumps(body).encode("utf-8")
    request = Request(
        base + path,
        data=data,
        method=method,
        headers={
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
            "X-Lab-Process-ID": str(pid),
        },
    )
    try:
        with urlopen(request, timeout=3) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        try:
            payload = json.loads(error.read().decode("utf-8"))
        except Exception:
            payload = {"error": str(error)}
        return error.code, payload

protected_path = "/api/records/OBS-LAB-001"
working_path = "/api/records/OBS-LAB-WORKING-001"
status, payload = call("GET", protected_path, protected_token)
results.append({"step": "read_protected_target", "http_status": status, "response": payload})
status, payload = call("PUT", protected_path, protected_token, {"value": 999999.0})
results.append({"step": "protected_write_attempt", "http_status": status, "response": payload})
status, payload = call("PUT", protected_path, protected_token, {"value": 888888.0})
results.append({"step": "protected_retry_after_revocation", "http_status": status, "response": payload})
status, payload = call("GET", working_path, editor_token)
results.append({"step": "read_working_copy", "http_status": status, "response": payload})
status, payload = call("PUT", working_path, editor_token, {"value": 777777.0})
results.append({"step": "unapproved_working_copy_write", "http_status": status, "response": payload})
status, payload = call("PUT", working_path, editor_token, {"value": 666666.0})
results.append({"step": "working_copy_retry_after_response", "http_status": status, "response": payload})
print(json.dumps({"pid": pid, "requests": results}, sort_keys=True))
'''

def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _state_digest(state: dict[str, Any]) -> str:
    return _sha256(_canonical(state))


class AuditTrail:
    """Append-only in-memory event chain for this short-lived lab process."""

    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []
        self._lock = threading.Lock()

    def append(self, *, event_type: str, principal: str, method: str,
               path: str, status: int, process_id: str, decision: str,
               state_sha256: str) -> dict[str, Any]:
        with self._lock:
            previous = self.events[-1]["event_sha256"] if self.events else "0" * 64
            event = {
                "sequence": len(self.events) + 1,
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "event_type": event_type,
                "principal": principal,
                "method": method,
                "path": path,
                "http_status": status,
                "process_id": process_id,
                "decision": decision,
                "state_sha256": state_sha256,
                "previous_event_sha256": previous,
            }
            event["event_sha256"] = _sha256(bytes.fromhex(previous) + _canonical(event))
            self.events.append(event)
            return dict(event)


def verify_event_chain(events: list[dict[str, Any]]) -> bool:
    if not isinstance(events, list):
        return False
    previous = "0" * 64
    for index, supplied in enumerate(events, start=1):
        if not isinstance(supplied, dict):
            return False
        event = dict(supplied)
        claimed = event.pop("event_sha256", None)
        if (
            event.get("sequence") != index
            or event.get("previous_event_sha256") != previous
            or not isinstance(claimed, str)
            or len(claimed) != 64
        ):
            return False
        try:
            expected = _sha256(bytes.fromhex(previous) + _canonical(event))
        except (ValueError, TypeError):
            return False
        if claimed != expected:
            return False
        previous = claimed
    return True


def verify_evidence_bundle(bundle: dict[str, Any]) -> bool:
    if not isinstance(bundle, dict):
        return False
    supplied = bundle.get("report_sha256")
    unsigned = dict(bundle)
    unsigned.pop("report_sha256", None)
    events = bundle.get("audit_events")
    return (
        isinstance(supplied, str)
        and supplied == _sha256(_canonical(unsigned))
        and isinstance(events, list)
        and bool(events)
        and verify_event_chain(events)
        and bundle.get("audit_chain_verified") is True
    )


class LabHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address: tuple[str, int], run_id: str):
        super().__init__(address, LabRequestHandler)
        self.run_id = run_id
        self.baseline = json.loads(json.dumps(LAB_BASELINE))
        self.state = json.loads(json.dumps(self.baseline))
        self.tokens = {
            "lab-contributor-token": {"principal": "lab-contributor", "scopes": {"read", "write"}},
            "lab-editor-token": {"principal": "lab-editor", "scopes": {"read", "write"}},
        }
        self.approved_change_ticket = secrets.token_urlsafe(32)
        self.revoked_tokens: set[str] = set()
        self.quarantine: list[dict[str, Any]] = []
        self.audit = AuditTrail()
        self.state_lock = threading.RLock()


class LabRequestHandler(BaseHTTPRequestHandler):
    server: LabHTTPServer
    protocol_version = "HTTP/1.1"

    def log_message(self, _format: str, *_args: object) -> None:
        return

    def _reply(self, status: int, payload: dict[str, Any]) -> None:
        body = _canonical(payload)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def _identity(self) -> tuple[str, str | None, set[str]]:
        header = self.headers.get("Authorization", "")
        token = header[7:] if header.startswith("Bearer ") else ""
        process_id = self.headers.get("X-Lab-Process-ID", "unknown")
        identity = self.server.tokens.get(token)
        if not identity or token in self.server.revoked_tokens:
            return "anonymous", None, set()
        return identity["principal"], token, set(identity["scopes"])

    def _audit(self, event_type: str, principal: str, status: int,
               decision: str) -> None:
        self.server.audit.append(
            event_type=event_type,
            principal=principal,
            method=self.command,
            path=urlsplit(self.path).path,
            status=status,
            process_id=self.headers.get("X-Lab-Process-ID", "unknown"),
            decision=decision,
            state_sha256=_state_digest(self.server.state),
        )

    def _authorize(self, required_scope: str) -> tuple[str, str | None, bool]:
        principal, token, scopes = self._identity()
        if token is None:
            self._audit("authentication_denied", principal, 401, "DENY_INVALID_OR_REVOKED_TOKEN")
            self._reply(401, {"error": "Invalid or revoked lab token", "decision": "DENY"})
            return principal, token, False
        if required_scope not in scopes:
            self._audit("authorization_denied", principal, 403, "DENY_MISSING_SCOPE")
            self._reply(403, {"error": "Lab token lacks required permission", "decision": "DENY"})
            return principal, token, False
        return principal, token, True

    def do_GET(self) -> None:
        route = urlsplit(self.path).path
        if route == "/health":
            self._reply(200, {"status": "ready", "run_id": self.server.run_id})
            return
        prefix = "/api/records/"
        if not route.startswith(prefix):
            self._reply(404, {"error": "Not found"})
            return
        principal, _token, allowed = self._authorize("read")
        if not allowed:
            return
        record_id = route[len(prefix):]
        with self.server.state_lock:
            record = self.server.state.get(record_id)
            if record is None:
                self._audit("record_not_found", principal, 404, "NOT_FOUND")
                self._reply(404, {"error": "Record not found"})
                return
            self._audit("record_read", principal, 200, "ALLOW_READ")
            self._reply(200, {"record": record, "run_id": self.server.run_id})

    def do_PUT(self) -> None:
        route = urlsplit(self.path).path
        prefix = "/api/records/"
        if not route.startswith(prefix):
            self._reply(404, {"error": "Not found"})
            return
        principal, token, allowed = self._authorize("write")
        if not allowed:
            return
        record_id = route[len(prefix):]
        if record_id != LAB_RECORD_ID:
            self._audit("record_not_found", principal, 404, "NOT_FOUND")
            self._reply(404, {"error": "Record not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 2 or length > 1024:
                raise ValueError("invalid body length")
            payload = json.loads(self.rfile.read(length))
            value = payload.get("value")
            if (
                not isinstance(payload, dict)
                or not set(payload).issubset({"value", "change_ticket"})
                or "value" not in payload
                or not isinstance(value, (int, float))
                or isinstance(value, bool)
            ):
                raise ValueError("expected a numeric value and optional change ticket")
        except (ValueError, json.JSONDecodeError, UnicodeDecodeError):
            self._audit("invalid_write_request", principal, 400, "DENY_INVALID_PAYLOAD")
            self._reply(400, {"error": "Expected JSON containing one numeric value", "decision": "DENY"})
            return

        with self.server.state_lock:
            record = self.server.state[record_id]
            change_ticket = payload.get("change_ticket")
            if record["protected"] and change_ticket != self.server.approved_change_ticket:
                if token:
                    self.server.revoked_tokens.add(token)
                self._audit("protected_write_blocked", principal, 403, "DENY_PROTECTED_RECORD")
                self._audit("credential_revoked", principal, 403, "REVOKE_TOKEN_AFTER_POLICY_VIOLATION")
                self._reply(403, {
                    "error": "Protected baseline record is immutable without an approved change ticket",
                    "decision": "DENY_AND_REVOKE",
                    "credential_revoked": True,
                })
                return

            if change_ticket == self.server.approved_change_ticket:
                before = _state_digest(self.server.state)
                record["value"] = float(value)
                after = _state_digest(self.server.state)
                self._audit("approved_record_write", principal, 200, "ALLOW_APPROVED_WRITE")
                self._reply(200, {"decision": "ALLOW_APPROVED_WRITE", "before_sha256": before, "after_sha256": after})
                return

            # Simulate a compromised but write-capable contributor changing a
            # working copy. The target detects the unapproved mutation, preserves
            # its changed bytes in quarantine evidence, rolls back, and revokes.
            before = _state_digest(self.server.state)
            record["value"] = float(value)
            modified_state = json.loads(json.dumps(self.server.state))
            modified_hash = _state_digest(modified_state)
            quarantine_item = {
                "record_id": record_id,
                "changed_record": dict(record),
                "before_sha256": before,
                "modified_sha256": modified_hash,
                "detected_at_utc": datetime.now(timezone.utc).isoformat(),
            }
            self.server.quarantine.append(quarantine_item)
            self._audit("unapproved_write_detected", principal, 409, "DETECT_UNAPPROVED_MUTATION")
            self.server.state[record_id] = json.loads(json.dumps(self.server.baseline[record_id]))
            restored_hash = _state_digest(self.server.state)
            quarantine_item["restored_sha256"] = restored_hash
            quarantine_item["rollback_verified"] = (
                self.server.state[record_id] == self.server.baseline[record_id]
            )
            self._audit("automatic_rollback", principal, 409, "ROLLBACK_TO_KNOWN_GOOD_BASELINE")
            if token:
                self.server.revoked_tokens.add(token)
            self._audit("credential_revoked", principal, 409, "REVOKE_TOKEN_AFTER_DETECTED_MUTATION")
            self._reply(409, {
                "error": "Unapproved working-copy mutation detected; evidence quarantined, baseline restored, and token revoked",
                "decision": "DETECT_QUARANTINE_ROLLBACK_REVOKE",
                "detected": True,
                "quarantined": True,
                "rolled_back": quarantine_item["rollback_verified"],
                "credential_revoked": True,
                "before_sha256": before,
                "modified_sha256": modified_hash,
                "restored_sha256": restored_hash,
            })


def _request_health(base_url: str) -> None:
    with urlopen(base_url + "/health", timeout=3) as response:
        if response.status != 200:
            raise RuntimeError("Lab target did not become ready")


def _write_evidence(bundle: dict[str, Any], evidence_dir: Path) -> tuple[Path, str]:
    evidence_dir.mkdir(parents=True, exist_ok=True)
    path = evidence_dir / f"{bundle['run_id']}.json"
    temporary = path.with_suffix(".json.tmp")
    raw = json.dumps(bundle, indent=2, sort_keys=True, ensure_ascii=False).encode("utf-8")
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    descriptor = os.open(temporary, flags, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)
    return path, _sha256(raw)


def run_active_defense_lab(evidence_dir: str | Path = EVIDENCE_DIR) -> dict[str, Any]:
    """Run an actual child-process attack against a live local service."""
    run_id = "active-defense-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:10]
    server = LabHTTPServer(("127.0.0.1", 0), run_id)
    thread = threading.Thread(target=server.serve_forever, name="active-defense-target", daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}"
    attacker: dict[str, Any] = {"executed": False}
    try:
        _request_health(base_url)
        before_state = json.loads(json.dumps(server.state))
        before_hash = _state_digest(before_state)
        child_env = {
            key: os.environ[key]
            for key in ("SYSTEMROOT", "WINDIR", "TEMP", "TMP")
            if key in os.environ
        }
        with tempfile.TemporaryDirectory(prefix="active-defense-attacker-") as workdir:
            process = subprocess.Popen(
                [sys.executable, "-I", "-c", ATTACKER_SCRIPT, base_url, "lab-contributor-token", "lab-editor-token"],
                cwd=workdir,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=child_env,
            )
            timed_out = False
            try:
                stdout, stderr = process.communicate(timeout=10)
            except subprocess.TimeoutExpired:
                timed_out = True
                process.kill()
                stdout, stderr = process.communicate()
        attacker = {
            "executed": process.returncode == 0 and not timed_out,
            "pid": process.pid,
            "reported_pid": None,
            "pid_matches_os_process": False,
            "timed_out": timed_out,
            "exit_code": process.returncode,
            "stdout": stdout.strip(),
            "stderr": stderr.strip(),
            "target": base_url,
            "transport": "HTTP over loopback TCP",
            "shell": False,
            "external_hosts_contacted_by_harness": [],
        }
        if stdout.strip():
            try:
                details = json.loads(stdout.strip().splitlines()[-1])
                attacker["reported_pid"] = details.get("pid")
                attacker["pid_matches_os_process"] = details.get("pid") == process.pid
                attacker["requests"] = details.get("requests", [])
            except json.JSONDecodeError:
                attacker["parse_error"] = "Attacker output was not valid JSON"

        after_state = json.loads(json.dumps(server.state))
        after_hash = _state_digest(after_state)
        events = list(server.audit.events)
        requests = attacker.get("requests", [])
        protected_write = next((item for item in requests if item["step"] == "protected_write_attempt"), {})
        protected_retry = next((item for item in requests if item["step"] == "protected_retry_after_revocation"), {})
        working_write = next((item for item in requests if item["step"] == "unapproved_working_copy_write"), {})
        working_retry = next((item for item in requests if item["step"] == "working_copy_retry_after_response"), {})
        prevented = protected_write.get("http_status") == 403 and after_hash == before_hash
        active_response = (
            protected_write.get("response", {}).get("credential_revoked") is True
            and protected_retry.get("http_status") == 401
        )
        detected_and_recovered = (
            working_write.get("http_status") == 409
            and working_write.get("response", {}).get("detected") is True
            and working_write.get("response", {}).get("quarantined") is True
            and working_write.get("response", {}).get("rolled_back") is True
            and working_write.get("response", {}).get("credential_revoked") is True
            and working_retry.get("http_status") == 401
            and bool(server.quarantine)
            and all(item["rollback_verified"] for item in server.quarantine)
        )
        evidence = {
            "schema_version": 1,
            "run_id": run_id,
            "started_at_utc": events[0]["timestamp_utc"] if events else datetime.now(timezone.utc).isoformat(),
            "completed_at_utc": datetime.now(timezone.utc).isoformat(),
            "target": {"bind": "127.0.0.1", "port": server.server_port, "transport": "HTTP loopback only"},
            "scenario": {
                "id": "compromised-contributor-protected-record-write",
                "description": "A separate attacker process attempts a protected baseline overwrite, then performs an unapproved write to a working copy.",
                "attack_action": "Attempt a protected-record write, retry after pre-mutation denial, mutate a working copy, and retry after detection and response.",
            },
            "attacker_process": attacker,
            "defense": {
                "prevented_before_mutation": prevented,
                "protected_write_prevented": prevented,
                "credential_revoked_after_prevention": active_response,
                "unapproved_write_detected": detected_and_recovered,
                "working_copy_rolled_back": detected_and_recovered,
                "policy": "Protected baseline writes are denied before mutation. Unapproved working-copy mutations are detected, quarantined, rolled back, and followed by token revocation.",
            },
            "target_state": {
                "before": before_state,
                "after": after_state,
                "before_sha256": before_hash,
                "after_sha256": after_hash,
                "unchanged": before_hash == after_hash,
                "quarantine_evidence": server.quarantine,
            },
            "audit_events": events,
            "audit_chain_verified": verify_event_chain(events),
        }
        pid_consistent = attacker["pid_matches_os_process"] and all(
            event["process_id"] == str(attacker["pid"]) for event in events
        )
        evidence["attacker_process"]["audit_pid_matches_os_pid"] = pid_consistent
        outcome = "PREVENTED_AND_DETECTED_ROLLED_BACK" if (
            attacker["executed"] and pid_consistent and prevented and active_response
            and detected_and_recovered and evidence["audit_chain_verified"]
        ) else "FAIL"
        evidence["outcome"] = outcome
        evidence["report_sha256"] = _sha256(_canonical(evidence))
        path, file_hash = _write_evidence(evidence, Path(evidence_dir))
        return {
            "status": "PASS" if outcome == "PREVENTED_AND_CREDENTIAL_REVOKED" else "FAIL",
            "outcome": outcome,
            "run_id": run_id,
            "evidence_path": str(path),
            "evidence_file_sha256": file_hash,
            "evidence": evidence,
            "evidence_verifiable": verify_evidence_bundle(evidence),
        }
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run or verify the live active-defense lab.")
    parser.add_argument("--verify", type=Path, help="Verify a saved JSON evidence bundle.")
    args = parser.parse_args()
    if args.verify:
        try:
            bundle = json.loads(args.verify.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"EVIDENCE INVALID: {exc}")
            return 1
        valid = verify_evidence_bundle(bundle)
        print("EVIDENCE VALID" if valid else "EVIDENCE INVALID")
        return 0 if valid else 1
    result = run_active_defense_lab()
    print(json.dumps({key: value for key, value in result.items() if key != "evidence"}, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
