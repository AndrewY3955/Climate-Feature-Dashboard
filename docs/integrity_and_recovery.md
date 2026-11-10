# Data integrity and recovery

This project uses SHA-256 manifests to detect whether a dataset differs from the bytes recorded when its manifest was generated. The check is useful for accidental changes and for the controlled classroom tampering demonstration, but it is not an independent trust system.

## What the current check establishes

- The verifier reads a JSON manifest, checks that it names the dataset being verified, validates the SHA-256 field format, and compares the recorded digest with the current file digest.
- A mismatch means the dataset bytes do not match the reference digest.
- A match does not establish that the source measurement is accurate, that the original data was complete, or that the manifest itself is trustworthy.

If an attacker can replace both the dataset and its manifest, they can generate a matching digest for the altered file. Keep the trusted reference outside the same writable location as the data it protects.

## Recommended protection layers

1. **Preserve source evidence.** Keep original reports, source URLs, page/table locators, access dates, and transformation notes. Do not overwrite original downloads.
2. **Version known-good outputs.** Store reviewed source data and generated outputs in a controlled, versioned location. Use Git commits and release tags as change history, while remembering that repository write access can alter future history.
3. **Separate write permissions.** Limit who can change reviewed datasets and who can change the reference manifest. Avoid giving the same process or account unrestricted write access to both.
4. **Keep an independent reference.** For a stronger deployment, export the manifest digest to a separately controlled location or sign the manifest with an offline/private signing key. Keep the verification key separate from the data writer. Do not commit private keys or tokens.
5. **Review changes.** Require pull-request review for changes to source records, schema rules, and generated trusted data. Preserve validation reports and record-level change logs.
6. **Back up and test recovery.** Maintain a known-good backup with access controls and periodically verify that it can be restored.

## Safe recovery procedure

Do not automatically overwrite a suspect file as soon as a mismatch is detected. Preserve evidence first.

1. Stop dashboard refreshes and mark the affected output as under investigation.
2. Copy the suspect dataset, manifest, validation report, and relevant logs to a separate evidence location. Record SHA-256 hashes of the preserved copies.
3. Compare the suspect dataset with a known-good version stored outside the suspected write path. Review record IDs, values, units, source links, years, reporting boundaries, and limitations.
4. Identify a reviewed known-good version from a protected backup or approved repository commit. Do not treat an unverified manifest beside the suspect file as the recovery authority.
5. Restore into a new working location rather than overwriting the evidence copy.
6. Re-run the data pipeline, tests, and integrity verification against the independently retained reference.
7. Have a second reviewer check the recovered records and dashboard output before publication.
8. Document the incident timeline, affected outputs, evidence, recovery source, validation results, and unresolved uncertainty.

## Project limitations

The current implementation provides digest comparison and validation, not digital signatures, immutable storage, access-control enforcement, automated backup, or an automated restore command. Those capabilities require a separately managed trust anchor and deployment-specific controls. The local dashboard is a classroom proof of concept, not an enterprise incident-response platform.
