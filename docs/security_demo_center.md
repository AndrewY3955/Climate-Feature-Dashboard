# Security Demo Center

## Run it

1. From the repository root, start the local app with `.\\run.ps1` on Windows or `sh ./run.sh` on macOS/Linux.
2. Open the local dashboard at `http://127.0.0.1:8765/`.
3. Select **Open Security Demo Center**.
4. Press **Run all security tests and scenarios**.
5. Review the test table, scenario cards, six response phases, and pairwise comparability results.

The demo runs through the local-only `POST /api/security-demo/run` endpoint. It accepts only a same-origin local request with a small empty JSON object. It does not expose a general command runner or accept arbitrary scenario instructions.

## What the one-click run executes

### Automated security checks

- Validate the trusted dataset against the project's schema and registered source metadata.
- Verify the trusted CSV against its SHA-256 manifest.
- Encrypt and decrypt a temporary in-memory copy with AES-256-GCM.
- Confirm that two encryptions produce fresh random salt/nonce parameters.
- Reject a wrong passphrase.
- Reject a one-byte ciphertext modification.

### Controlled ATT&CK-related scenarios

| Scenario | ATT&CK reference | Demonstration |
|---|---|---|
| Compromised contributor identity | T1078 – Valid Accounts | Tabletop exercise only. The local prototype has no authentication or account-audit service, so it cannot technically detect account compromise. |
| Altered environmental value | T1565.001 – Stored Data Manipulation | Increase an energy value in a temporary copy; detect the changed digest. |
| Deleted environmental observations | T1565.001 – Stored Data Manipulation | Remove water rows in a temporary copy; preserve the removed record IDs in the exercise result. |
| Removed source attribution | T1565.001 – Stored Data Manipulation | Blank a source label in a temporary copy; detect the artifact change. |
| Changed unit/scope metadata | T1565.001 – Stored Data Manipulation | Change a unit in a temporary copy; compare against the trusted reference and metric-unit rules. |
| Altered transfer payload | T1565.002 – Transmitted Data Manipulation | Change bytes in a simulated payload and compare with the sender-side digest. No network interception is performed. |
| Misleading visualization filter | T1565.001 – Stored Data Manipulation (scenario mapping) | Change a synthetic chart configuration to hide water records. This is not an edit to the deployed dashboard configuration. |

These are the three ATT&CK techniques currently mapped in the project, with multiple concrete variants for stored-data manipulation. This is not coverage of every technique in the MITRE ATT&CK framework.

### Incident-response exercise

Each technical scenario executes the six documented phases:

1. **Preparation:** capture the trusted digest and record inventory.
2. **Detection and analysis:** identify changed bytes or record details.
3. **Containment:** copy the altered artifact into a temporary quarantine.
4. **Eradication:** remove the altered working copy after preserving evidence.
5. **Recovery:** restore from a separate trusted baseline and verify the recovered digest; data scenarios also re-run schema/source validation.
6. **Lessons learned:** show the relevant defensive control and residual limitation.

The Valid Accounts scenario runs all six phases as a tabletop exercise. It is explicitly marked **TABLETOP ONLY**, not a successful technical detection.

All technical scenarios use temporary directories and are removed after each exercise. The trusted dataset, manifest, source files, generated adversarial dataset, and repository files are not modified by the demo.

## Comparability audit

The demo evaluates every pair of trusted observations. A pair is **DIRECTLY COMPARABLE** only when metric, unit, data year, geography, facility/organizational scope, lifecycle boundary, calculation method, and data status match. Company identity may differ. Same metric and unit with other mismatches is **CONDITIONAL** and requires explicit qualification/harmonization. Different metrics or units are **NOT COMPARABLE**. No missing value is converted to zero, and no unlike metric is silently normalized.

The seven reviewed observations are heterogeneous. It is expected that most or all pairs will be not comparable; this is a correct result, not a failed data audit.

## Security and interpretation boundaries

- SHA-256 is a one-way integrity hash, not encryption. It only detects changes relative to a trusted reference.
- The local manifest is stored with project files; this prototype does not establish independent manifest custody or a signed trust anchor.
- AES-256-GCM is a standalone file-encryption demonstration. It does not encrypt dashboard storage, GitHub Pages, or network traffic.
- The local dashboard has no login, MFA, role-based authorization, or central audit service. Valid Accounts is therefore tabletop-only.
- The local Python server binds to loopback and is not intended to be exposed to a network.
- ATT&CK entries are static defensive scenario mappings, not live threat intelligence, observed attacks, indicators of compromise, or actor attribution.
- This is not a penetration test, a production security operations center, or proof that all ATT&CK techniques are covered.
- Production controls such as MFA, least-privilege identity, independently protected backups/manifests, TLS, central audit logging, and managed encryption keys require a real hosting environment.

If any automated check or technical scenario fails, do not present the run as passing. Review the returned evidence and fix the underlying issue first.
