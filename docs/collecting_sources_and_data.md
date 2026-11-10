# Collecting sources and entering data

The CSV files in `data/intake/` are populated starter datasets, not blank templates. At the time of writing, they contain reviewed example entries: five sources, five papers, and seven environmental observations. Review their contents before editing; preserve an original copy if you want to retain the supplied examples. Keep original source files unchanged.

If you have source PDFs or CSVs that have not been reviewed or categorized yet, place copies in `data/intake/incoming/`. Keep their original filenames and contents. PDFs can be checked against reported page, table, or figure references; CSV columns and contents can be inspected before mapping records. Do not assume incoming CSVs share a schema or overwrite the supplied sample.

## 1. Collect source documents first

For each paper, report, dataset, or government/industry source:

1. Save the original document or data file in a clearly named source folder, or record its stable DOI/URL if you cannot redistribute the file.
2. Record it once in `data/intake/sources_template.csv`, filling one row per source.
3. Use the publisher/organization's own page to confirm its title, organization/authors, publication year, data year(s), geographic scope, and units.
4. Note the lifecycle/reporting boundary and limitations exactly as the source describes them. If not stated, enter `Not stated` and flag it for review instead of guessing.
5. Record how you checked the source and when you accessed it.

Recommended source identifiers are short and unique, such as `SRC-001`. Use the same ID for the measurements taken from that source.

## 2. Review academic papers

Open `data/intake/papers_template.csv` in a spreadsheet and enter one paper per row. Include a DOI or stable publisher URL and evidence it is peer reviewed. Read the paper's abstract, methods, results, and limitations; write a concise summary in your own words. Do not treat an abstract alone as support for details it does not state. Keep the full citation and connect each summary to the dashboard feature it supports.

## 3. Enter measurements

Open `data/intake/observations_template.csv` and enter one measured metric for one company/facility/geography and one data year per row.

- Copy the reported number and unit as published. Do not convert units silently.
- Include a source URL and a source locator such as a page number, table, figure, spreadsheet tab, or dataset field.
- Use `source_id` to link the observation to the source register.
- Keep the original value/unit and explain any conversion in the corresponding columns. Preserve enough detail to reproduce derived values.
- Distinguish statuses: `reported` for values published by the source (including conversions documented in `conversion_method`), `estimated`, `assumption`, or `derived`. Use `synthetic_demo` only for clearly labeled test data. Do not use workflow notes such as `reviewed_pending_pipeline` as a status.
- Describe the source's boundary and known limitations; enter `Not stated` if the source does not provide them.
- If the source does not report an observation, leave it out and document the gap. Do not fill missing values with zero or invent estimates.

The first 16 fields match the current pipeline input schema. The remaining columns add traceability (`source_id`, `source_locator`, original value/unit, conversion, uncertainty); the pipeline preserves additional columns.

## 4. Check your entries

Before importing:

- Confirm every `record_id` is unique.
- Check decimal separators and ensure `value` is a number, not a formatted string with thousands separators.
- Use a whole-number `data_year`.
- Check that each metric uses a consistent, documented unit. Current unit validation recognizes the four sample metrics in `docs/data_dictionary.md`; new semiconductor metrics need their allowed units added to the schema before pipeline validation.
- Check the `source_id` points to an entry in the source register and that the URL plus locator takes a reviewer back to the reported value.
- Keep one header row; do not merge cells or add title rows. Observation columns may appear in any order. Keep the expected field names from the template; the pipeline trims surrounding header whitespace and a UTF-8 BOM, then exports known fields in canonical order while retaining additional columns after them.

## 5. Prepare the pipeline input

Keep the supplied/intake files as working evidence. Once the data have been reviewed:

1. Save a reviewed copy of the observation table as `data/raw/environmental_data.csv` (CSV UTF-8).
2. Do not replace the provided sample until you have backed it up or explicitly decided it is no longer needed for tests.
3. Run the reviewed intake separately first, so the supplied sample and its generated outputs remain untouched:

   ```powershell
   .\.venv\Scripts\python.exe -m climate_dashboard.pipeline --input data/intake/observations_template.csv --output-dir data/processed/reviewed
   ```

4. Review `data/processed/reviewed/validation_report.json`. A `PASS` means only that implemented checks passed; it does not prove that a source or measurement is true.
5. If validation fails, fix the intake record against its original source, save again, and rerun. Do not weaken a rule just to make a row pass.
6. The default command still processes `data/raw/environmental_data.csv` into `data/processed/`; do not overwrite the sample until a separate backup and test plan are approved.
7. After the trusted dataset is reviewed, generate a separate intentional example. Never use an adversarial file as trusted input.

The pipeline rejects a header-only/empty dataset. The current reviewed intake contains example source-backed records; replace or extend them only after reviewing the original sources and recording any changes.

## Template field guides

### `sources_template.csv`

- `source_id`: Stable short key used by observation records.
- `source_name`, `organization`, `source_url`, `source_type`: Source identity and location.
- `publication_year`: Year the source/report was published.
- `data_year_start`, `data_year_end`: Years represented by its observations.
- `geography`, `feature_coverage`, `lifecycle_boundary`: Scope and subject.
- `reliability_evidence`: Why this source is suitable (for example, a primary company report or peer-reviewed study); avoid unsupported labels such as “100% reliable.”
- `limitations`, `validation_method`, `access_date`: Caveats, review process, and access date.

### `papers_template.csv`

Use one row per paper. Record the citation, DOI/stable URL, peer-review evidence, research objective, semiconductor feature, data/variables, environmental impact, main findings, limitations, and dashboard relevance.

### `observations_template.csv`

One row is one observation. `source_name` and `source_url` remain in the row so the pipeline output and Power BI table have human-readable provenance without needing a join. `source_id` links back to the fuller source register.
