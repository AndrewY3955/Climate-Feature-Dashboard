# Threat model and data-integrity plan

## Scope and security objectives

The prototype handles user-supplied semiconductor/environmental source records, normalized CSV outputs, integrity manifests, Power BI report settings, and a deliberately manipulated demonstration. The primary security objective is to preserve provenance and detect unauthorized or misleading changes before data inform climate-related conclusions.

The current project is a local classroom prototype. It does not yet implement cloud identity, MFA, enterprise role-based access control, encryption/key management, or centralized audit logging. Those are controls to apply on the hosting platform, not claims about the current code.

## Assets

- Original source files, citations, source URLs, and publication metadata
- Raw and normalized trusted datasets, including units, boundaries, and limitations
- Data dictionary, transformation assumptions, validation rules, and tests
- Integrity manifests or signatures and known-good backups
- Python source code and dependencies
- Power BI model, visuals, filters, labels, and refresh configuration
- Adversarial copy, manipulation register, screenshots, and investigation evidence
- Final report and presentation claims based on the preceding evidence

## Threat actors and motivations

| Actor | Motivation | Relevant capability |
|---|---|---|
| Malicious insider or contributor | Promote a preferred conclusion, conceal an error, or bypass review | Write access to CSVs, scripts, report settings, or shared storage |
| External attacker with a compromised account | Alter evidence, disrupt the project, or misuse access | Stolen credentials or an exposed account/session |
| Vendor or source publisher | Present favorable or incomplete performance information | Control over published scope, assumptions, or reported records |
| Unintentional contributor error | Accidental misstatement or misleading comparison | Incorrect units, conversions, filters, formulas, or edits |

## Threat-intelligence reference mapping

The Power BI import pack includes a small, source-linked mapping to MITRE ATT&CK Enterprise techniques relevant to the documented scenario:

| Technique | Scenario relevance | Project evidence and status |
|---|---|---|
| [T1078 - Valid Accounts](https://attack.mitre.org/techniques/T1078/) | A compromised contributor account could be used to change trusted files or report settings. | Threat-model scenario only. No account compromise or unauthorized activity was observed. |
| [T1565.001 - Stored Data Manipulation](https://attack.mitre.org/techniques/T1565/001/) | Changing stored CSV values, source labels, or feature coverage could alter climate conclusions. | The separate adversarial copy is a controlled classroom simulation, not a real incident. |
| [T1565.002 - Transmitted Data Manipulation](https://attack.mitre.org/techniques/T1565/002/) | Data altered in transit between a source, pipeline, storage location, or report could mislead users. | Reference scenario only; the local prototype does not test a network or Power BI transfer path. |

This is a defensive reference mapping to ATT&CK technique descriptions, not a live threat-intelligence feed. The project has no threat indicators, actor attribution, or evidence that a real adversary targeted this dataset. See [`docs/power_bi_setup.md`](power_bi_setup.md) and `data/powerbi/threat_intel_reference.csv` for the import model.

## Attacker-versus-defender scenario

A contributor account with write access to the shared project folder is compromised. In the controlled demonstration, the adversarial copy increases a reported energy value, removes a human-readable source label (while retaining its URL and source ID), and removes water records. A separate visual manipulation such as changing a Power BI filter or axis is a scenario to test during the dashboard build, not an implemented control or captured event. A simple re-hash performed after an edit would not help if the attacker can replace both the CSV and manifest.

Defenders preserve a known-good version in a separately protected repository/backup, use least privilege and MFA for shared services, review approved changes, validate record IDs/units/provenance/feature coverage, compare output with the protected reference, inspect report filters and model changes, and keep the manipulated training copy on a separate path. During response, they quarantine the changed copy and use platform audit logs and version history to investigate; they do not claim attribution without evidence.

## Attacker and defender profiles

**Attacker profile (scenario assumption):** A contributor's account or workstation is compromised, giving the attacker the same write access as that contributor to project files. The attacker seeks to influence climate conclusions or reduce confidence in inconvenient indicators by changing values, removing rows or context, or editing report filters/labels. The scenario assumes access to files and report settings, not a vulnerability exploit, administrator access, or the ability to falsify a separately protected reference. If the reference is stored under the same writable permissions, the attacker may be able to replace it too; integrity checks then require an external trusted copy to detect the change.

**Defender profile (planned operating roles):** A data steward preserves source originals, reviews citations/conversions, and runs the validation pipeline. A report reviewer checks that measures, units, boundaries, filters, and labels match the validated dataset before publication. A response lead preserves evidence, compares it with protected versions, coordinates credential/access changes with the platform administrator, and approves restoration. These are responsibility assignments for the project workflow, not configured identities or role-based access controls in the current local prototype.

## Qualitative risk assessment

Ratings are planning judgments for this classroom prototype, not measured probabilities. Impact is the potential effect on data validity, climate conclusions, and user trust.

| Scenario | Likelihood | Impact | Existing evidence/control | Residual risk |
|---|---|---|---|---|
| A writer changes a value, unit, year, or row in a trusted CSV | Medium | High | Pipeline checks required fields, numeric values, years, allowed metrics/units; SHA-256 detects differences against a trusted reference; tamper test exists | High if the attacker can replace both data and reference manifest; source truth still needs review |
| A report or source omits a relevant metric, facility, or lifecycle stage without changing file bytes | Medium | High | Source limitations, coverage, and boundaries are recorded; adversarial omission is logged and row-count/feature coverage can be compared | High until feature completeness and report filters are independently reviewed; a hash cannot detect truthful-but-incomplete reporting |
| A report filter, axis, label, or refresh setting is changed | Medium | High | Local dashboard views are implemented and exercised; Power BI review guidance requires checking report/model settings, but no native Power BI report or workspace has been deployed | High for any shared report until workspace permissions, version history, and visual review are configured |
| A contributor account is compromised and used to alter code, data, or report files | Low to medium | High | Versioned local files and tests provide some change evidence; MFA, least privilege, and audit logging are recommended for shared hosting | High in any shared environment until identity controls, protected backups, and audit logs are enabled |

## Attack vectors, weaknesses, and consequences

| Attack vector / weakness | Example manipulation | Potential consequence |
|---|---|---|
| Writable raw CSV or spreadsheet | Change a value, unit, year, location, or source | Invalid or incomparable climate result |
| Incomplete or selectively reported vendor data | Omit process gases, facilities, water stress, or lifecycle stages | Understated environmental impact despite an untampered file |
| Shared credentials or excessive write access | Replace files, pipeline code, or report | Unauthorized changes and loss of trustworthy baseline |
| Dataset and manifest stored under the same writer permissions | Replace both after changing data | Hash check appears valid against an attacker-chosen reference |
| Missing validation or test coverage | Duplicate IDs, non-finite values, absent features, or invalid units pass through | Silent data corruption or misleading comparisons |
| Power BI model/filter/visual edits | Cherry-pick years, change axis scale/labels, hide a metric | Misleading result without changing source measurements |
| Unsupported conversion or changed lifecycle boundary | Compare inconsistent units or system boundaries | False company/technology ranking |
| Loss of source report or lack of audit service | Evidence cannot establish who changed what or when | Delayed response; unsupported attribution |

## Defensive controls

### Data and software controls

- Preserve source originals; keep raw input, trusted normalized output, and adversarial copies separate.
- Validate identifiers, required metadata, numeric values, allowed statuses, units, years, and selected-feature completeness. Reject failures visibly.
- Record source, data/publication year, geography, lifecycle boundary, assumptions, limitations, uncertainty, and every conversion.
- Run automated tests and review code/report changes before accepting outputs.
- Generate a cryptographic digest and compare it with a known-good reference protected separately from the data. Use a digital signature or HMAC with separately controlled keys if writers can replace the manifest.
- Keep versioned, access-controlled backups; enable platform audit logs and change alerts where available.

### Data-integrity workflow

1. Preserve each supplied source document and intake CSV unchanged; record its citation, URL/identifier, publication and data years, page/table locator, units, scope, assumptions, and limitations in the registers.
2. Treat the intake CSV as untrusted input. Run the pipeline into a designated output directory; retain its validation report, normalized trusted CSV, and SHA-256 manifest.
3. Review the pipeline result and any warnings. The current validator rejects missing required columns/values, duplicate or missing record IDs, invalid numeric values/years, unsupported metrics/units, negative values, and invalid statuses. It warns on blank human-readable source labels and missing limitations. It does not automatically prove that each `source_id` exists in or matches `sources_template.csv`; that cross-check remains a documented/manual review step.
4. Compare the generated output with a known-good version whose hash/reference is protected outside the data writer's control. The manifest generated by this local prototype is stored beside its output, so it is not an independent trust anchor by itself.
5. Keep a separate, clearly labeled adversarial copy and a record-level change log. Never treat its manifest as evidence that the manipulated values are true or as a substitute for the trusted reference.
6. Before dashboard publication, reconcile displayed measures, source records, units, time/geography, filters, lifecycle boundaries, caveats, and record coverage against the validated trusted dataset.

### Access and operational controls

- Use MFA, least-privilege roles, separate read/write permissions, and remove access when no longer needed.
- Encrypt files in transit and at rest using the hosting platform's controls; protect signing keys/secrets independently.
- Require a second-person review for trusted-data, code, and report changes where practical.
- Review Power BI source lineage, refresh status, filters, axes, labels, units, and lifecycle boundaries before release.
- Label synthetic/adversarial examples prominently and prevent them from being mixed with trusted analysis.

### Encryption demonstration

A standalone utility at `scripts/encryption_demo.py` demonstrates AES-256-GCM authenticated file encryption. It derives a 256-bit key from a user-entered passphrase using scrypt, generates a fresh random salt and nonce, authenticates its file header, and rejects modified ciphertext or an incorrect passphrase. Automated tests cover round-trip recovery and authentication failures.

This is an educational file-level demonstration only. It is not wired into the dashboard, does not encrypt dashboard data at rest or in transit, and does not configure GitHub Pages, TLS, encrypted backups, or enterprise key management. Production encryption and key custody remain hosting/deployment responsibilities. See [encryption_demo.md](encryption_demo.md).

## Control status

The Python validation, separate adversarial generator, SHA-256 manifests, record-level manipulation log, standalone AES-256-GCM encryption demonstration, and automated tests are implemented as local prototype controls. Tests cover trusted-manifest verification, detection of a changed file, separation of the adversarial copy from trusted input, and logging of the controlled changes. The source-backed dataset and its adversarial copy are written to separate output files. The project has not established independent manifest custody, MFA, organizational access controls, dashboard-integrated encryption or key custody, central audit logs, protected remote backups, automated source-register cross-checking, or Power BI workspace controls; these require host/workspace configuration or further implementation.

## Indicators of compromise

- Trusted hash does not match a separately protected known-good reference
- Unexpected row-count or record-ID changes; required metrics/features missing
- Blank/changed source, unit, year, geography, boundary, status, or limitation
- Unexpected value, pipeline, dependency, manifest, report-model, filter, or axis change
- Validation warnings/errors or unexplained changes in refresh results
- A trusted dataset and its manifest both changed without an approved record

## Severity and response triggers

Quarantine the affected output when an unexplained data/hash/report change could change conclusions. Escalate if trusted references or credentials may also be compromised. An intact hash does not clear a source that is incomplete, biased, or scientifically inaccurate; provenance review is separate from file-integrity review.

## Limitations

A hash detects byte changes only relative to a trusted, independently protected reference. It does not prove source truthfulness, completeness, scientific validity, or who made a change. Attribution and precise timing require trustworthy identity/audit evidence from the relevant platform; local metadata and Git history alone may be insufficient.
