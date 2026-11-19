# Live Active-Defense Lab

## Purpose and scope

This exercise runs a real attacker process against a live, short-lived HTTP target bound to `127.0.0.1`. It is deliberately limited to a synthetic in-memory record. It does not touch reviewed CSVs, manifests, credentials, repository files, Power BI exports, or external hosts.

The exercise demonstrates a real request/response sequence and active server-side enforcement. It is a controlled reproduction of unauthorized data modification behavior, not a vulnerability exploit, malware simulation, external penetration test, or production security control.

## Run

Start the local dashboard using `.\\run.ps1` on Windows or `sh ./run.sh` on macOS/Linux. Open the Security Demo Center and select **Run live attack and defense**.

The same lab can be run from the repository root:

```powershell
python -m climate_dashboard.active_defense_lab
```

The command writes a JSON evidence report under `evidence/active-defense-lab/`. Verify a saved report with:

```powershell
python -m climate_dashboard.active_defense_lab --verify evidence/active-defense-lab/<run-id>.json
```

The UI also offers a direct evidence JSON download.

## What actually executes

1. The defender starts a real `ThreadingHTTPServer` bound to loopback on an ephemeral port.
2. The target creates a protected baseline record and a separate mutable working-copy record, then issues two lab-only contributor tokens with read/write scope.
3. A separate Python child process starts with isolated interpreter mode, a temporary working directory, a minimal environment, no shell, and a bounded timeout.
4. The attacker process performs real HTTP requests over loopback TCP. First, it attempts to overwrite the protected baseline record; the target denies the write before mutation, revokes that token, and rejects the retry. Next, it uses a separate write-capable lab identity to modify a working-copy record without an approved change ticket; the target detects the mutation, preserves the changed record in quarantine evidence, restores the known-good baseline, revokes that token, and rejects a retry.
5. The target checks the token and record policy before mutation. A write to the protected baseline record is denied with HTTP 403; the token is revoked immediately.
6. The retry receives HTTP 401 because the credential has been revoked.
7. The runner compares before/after state digests and checks the event log's hash chain. The report is written atomically with restrictive file permissions where supported.

Expected sequence: `200 → 403 → 401 → 200 → 409 → 401`. The first three responses demonstrate pre-mutation prevention and credential revocation. The latter three demonstrate an actual working-copy mutation, detection, quarantine, rollback, credential revocation, and denial of a retry. A successful run requires both paths, unchanged final state, matching process/audit PID, and verifiable evidence.

## Evidence fields

Each run records:

- Unique run ID and UTC timestamps
- Loopback target address, port, and transport
- Attacker process ID, execution state, exit code, standard output, and actual HTTP request results
- The authorization decisions, active credential revocations, and actual HTTP status sequence
- The modified working-copy record preserved in quarantine evidence and its rollback verification
- Before/after target state and SHA-256 digests
- Ordered audit events with timestamps, principal, method, route, HTTP status, process ID, decision, state digest, previous-event digest, and event digest
- Final outcome, audit-chain verification, report digest, and saved evidence-file digest

The evidence bundle is reproducible and self-checking: the verifier recomputes the event chain and report SHA-256. The CI workflow also runs the live scenario after the test matrix passes, verifies the generated report, and uploads the JSON report as a 30-day GitHub Actions artifact for that commit. A plain hash is not a digital signature. If evidence must prove authenticity to an independent third party, preserve the report digest in a separately controlled system or add a separately managed signing key.

## Security boundaries

- The target binds only to loopback and uses a disposable in-memory record. The attacker script makes requests only to the supplied loopback target.
- The child process is constrained by a fixed script, isolated Python mode, a temporary working directory, a reduced environment, and a timeout. **This is not an OS-enforced sandbox.** The operating system does not impose a general network-deny policy or a restricted user token on the child process.
- The token and policy are lab-only. This does not add login, MFA, production RBAC, a production API, or external identity integration to the dashboard.
- The defense prevents writes to the protected baseline before mutation. A separate unapproved working-copy write is allowed to occur, then detected, quarantined, rolled back, and followed by token revocation. It does not claim to terminate arbitrary malicious processes or defend against a host administrator.
- The audit chain detects accidental or post-run modification relative to the saved report digest, but local administrator access can alter local evidence and recompute an unkeyed hash. Store the digest separately for stronger evidence custody.
- The legacy Security Demo Center's file-based attack scenarios remain controlled synthetic-file exercises. This live lab is an additional, distinct execution path.

## Success and failure semantics

- `PREVENTED_AND_DETECTED_ROLLED_BACK`: the protected write was denied before mutation; a separate working-copy mutation was detected, quarantined, rolled back, and its credential revoked; retries were rejected; and evidence verifies.
- `FAIL`: any required execution, enforcement, state-integrity, or evidence-verification condition failed.

A failed attack process is not a successful defense. A detected change after mutation is not reported as prevention. No test or UI label should upgrade a failed condition to `PASS`.
