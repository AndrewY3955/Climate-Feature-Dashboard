"""Load, validate, normalize, and export the trusted dataset."""

import argparse
import json
import math
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd

from climate_dashboard.integrity import write_manifest
from climate_dashboard.schema import (
    ALLOWED_DATA_STATUSES,
    CANONICAL_COLUMNS,
    EXPECTED_UNITS,
    REQUIRED_TEXT_COLUMNS,
    REQUIRED_COLUMNS,
)

ROOT = Path(__file__).resolve().parents[1]
RAW_FILE = ROOT / "data" / "raw" / "environmental_data.csv"
SOURCE_REGISTER_FILE = ROOT / "data" / "intake" / "sources_template.csv"
OUT_DIR = ROOT / "data" / "processed"
TRUSTED_FILE = OUT_DIR / "trusted_data.csv"
VALIDATION_FILE = OUT_DIR / "validation_report.json"
MANIFEST_FILE = OUT_DIR / "trusted_manifest.json"


def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    columns = [str(column).lstrip("\ufeff").strip() for column in df.columns]
    if len(columns) != len(set(columns)):
        raise ValueError("Input dataset contains duplicate column names after trimming whitespace.")
    df = df.copy()
    df.columns = columns
    return df


def order_columns(df: pd.DataFrame) -> pd.DataFrame:
    ordered = [column for column in CANONICAL_COLUMNS if column in df.columns]
    remaining = [column for column in df.columns if column not in CANONICAL_COLUMNS]
    return df.loc[:, ordered + remaining]


def _is_blank(value: object) -> bool:
    return pd.isna(value) or not str(value).strip()


def _is_https_url(value: object) -> bool:
    if _is_blank(value):
        return False
    parsed = urlparse(str(value).strip())
    return parsed.scheme == "https" and bool(parsed.netloc)


def populate_source_urls(
    df: pd.DataFrame,
    source_register: pd.DataFrame | None,
) -> pd.DataFrame:
    """Fill omitted reported-source URLs from the canonical source register.

    Existing non-empty URLs are never silently replaced. Validation rejects a
    value that conflicts with the registered URL.
    """
    result = df.copy()
    if source_register is None or not {"source_id", "source_url"}.issubset(source_register.columns):
        return result

    register = source_register.copy()
    register["source_id"] = register["source_id"].astype("string").str.strip()
    register["source_url"] = register["source_url"].astype("string").str.strip()
    url_by_id = dict(zip(register["source_id"], register["source_url"]))

    if "source_id" not in result.columns or "source_url" not in result.columns:
        return result

    reported = result.get("data_status", pd.Series("", index=result.index)).astype("string").str.strip()
    for index in result.index[reported.ne("synthetic_demo").fillna(True)]:
        source_id = str(result.at[index, "source_id"]).strip() if not _is_blank(result.at[index, "source_id"]) else ""
        current_url = result.at[index, "source_url"]
        if _is_blank(current_url) and source_id in url_by_id:
            result.at[index, "source_url"] = url_by_id[source_id]
    return result


def validate_dataframe(
    df: pd.DataFrame,
    source_register: pd.DataFrame | None = None,
) -> dict:
    errors = []
    warnings = []

    missing_columns = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_columns:
        errors.append({"type": "missing_columns", "columns": missing_columns})
        return {
            "status": "FAIL",
            "row_count": int(len(df)),
            "error_count": len(errors),
            "warning_count": len(warnings),
            "errors": errors,
            "warnings": warnings,
        }

    if df.empty:
        errors.append({"type": "empty_dataset"})
        return {
            "status": "FAIL",
            "row_count": 0,
            "error_count": len(errors),
            "warning_count": len(warnings),
            "errors": errors,
            "warnings": warnings,
        }

    missing_record_ids = (
        df["record_id"].isna()
        | df["record_id"].astype("string").str.strip().eq("").fillna(False)
    )
    if missing_record_ids.any():
        errors.append({
            "type": "missing_record_id",
            "count": int(missing_record_ids.sum()),
        })
    if df["record_id"].duplicated().any():
        errors.append({
            "type": "duplicate_record_id",
            "values": df.loc[df["record_id"].duplicated(), "record_id"].astype(str).tolist(),
        })

    for column in sorted(REQUIRED_TEXT_COLUMNS):
        blank_values = df[column].isna() | df[column].astype("string").str.strip().eq("").fillna(False)
        if blank_values.any():
            errors.append({
                "type": "missing_required_value",
                "column": column,
                "rows": df.index[blank_values].tolist(),
            })

    numeric_values = pd.to_numeric(df["value"], errors="coerce")
    invalid_numeric = numeric_values.isna() | ~numeric_values.map(math.isfinite)
    if invalid_numeric.any():
        errors.append({"type": "invalid_numeric_value", "rows": df.index[invalid_numeric].tolist()})

    negative_values = numeric_values < 0
    if negative_values.any():
        errors.append({"type": "negative_value", "rows": df.index[negative_values].tolist()})

    numeric_years = pd.to_numeric(df["data_year"], errors="coerce")
    invalid_year = numeric_years.isna() | (numeric_years % 1 != 0)
    if invalid_year.any():
        errors.append({"type": "invalid_data_year", "rows": df.index[invalid_year].tolist()})

    real_rows = df["data_status"].astype("string").str.strip().ne("synthetic_demo").fillna(True)
    provenance_columns = ("source_name", "source_url", "source_id", "source_locator")
    for column in provenance_columns:
        if column not in df.columns:
            errors.append({
                "type": "missing_provenance_column",
                "column": column,
                "rows": df.index[real_rows].tolist(),
            })
            continue
        blank_values = df[column].isna() | df[column].astype("string").str.strip().eq("").fillna(False)
        affected = real_rows & blank_values
        if affected.any():
            errors.append({
                "type": "missing_source_provenance",
                "column": column,
                "rows": df.index[affected].tolist(),
            })

    if real_rows.any():
        if source_register is None:
            errors.append({
                "type": "source_register_unavailable",
                "message": "Reported observations require the canonical source register.",
            })
        elif not {"source_id", "source_url"}.issubset(source_register.columns):
            errors.append({
                "type": "invalid_source_register_schema",
                "required_columns": ["source_id", "source_url"],
            })
        else:
            register = source_register.copy()
            register["source_id"] = register["source_id"].astype("string").str.strip()
            register["source_url"] = register["source_url"].astype("string").str.strip()
            if register["source_id"].isna().any() or register["source_id"].eq("").any():
                errors.append({"type": "source_register_missing_id"})
            if register["source_id"].duplicated().any():
                errors.append({
                    "type": "source_register_duplicate_id",
                    "values": register.loc[register["source_id"].duplicated(), "source_id"].astype(str).tolist(),
                })
            invalid_register_urls = [
                str(row["source_id"])
                for _, row in register.iterrows()
                if not _is_https_url(row["source_url"])
            ]
            if invalid_register_urls:
                errors.append({
                    "type": "source_register_invalid_url",
                    "source_ids": invalid_register_urls,
                })
            url_by_id = dict(zip(register["source_id"], register["source_url"]))
            if "source_id" in df.columns and "source_url" in df.columns:
                for index in df.index[real_rows]:
                    source_id = str(df.at[index, "source_id"]).strip() if not _is_blank(df.at[index, "source_id"]) else ""
                    source_url = str(df.at[index, "source_url"]).strip() if not _is_blank(df.at[index, "source_url"]) else ""
                    if source_id not in url_by_id:
                        errors.append({
                            "type": "unknown_source_id",
                            "row": int(index),
                            "source_id": source_id,
                        })
                    elif source_url and source_url != str(url_by_id[source_id]):
                        errors.append({
                            "type": "source_url_mismatch",
                            "row": int(index),
                            "source_id": source_id,
                            "source_url": source_url,
                            "registered_source_url": str(url_by_id[source_id]),
                        })
                    if source_url and not _is_https_url(source_url):
                        errors.append({
                            "type": "invalid_source_url",
                            "row": int(index),
                            "source_url": source_url,
                        })

    for idx, row in df.iterrows():
        metric = row["metric"]
        unit = row["unit"]
        if metric not in EXPECTED_UNITS:
            errors.append({
                "type": "unsupported_metric",
                "row": int(idx),
                "metric": metric,
                "supported_metrics": sorted(EXPECTED_UNITS),
            })
        elif unit not in EXPECTED_UNITS[metric]:
            errors.append({
                "type": "unit_mismatch",
                "row": int(idx),
                "metric": metric,
                "unit": unit,
                "expected": sorted(EXPECTED_UNITS[metric]),
            })
        if row["data_status"] not in ALLOWED_DATA_STATUSES:
            errors.append({
                "type": "invalid_data_status",
                "row": int(idx),
                "data_status": row["data_status"],
            })
        if pd.isna(row["source_name"]) or not str(row["source_name"]).strip():
            warnings.append({"type": "empty_source_name", "row": int(idx)})
        if pd.isna(row["limitation"]) or not str(row["limitation"]).strip():
            warnings.append({"type": "missing_limitation", "row": int(idx)})

    if (df["data_status"] == "synthetic_demo").any():
        warnings.append({
            "type": "synthetic_data_present",
            "message": "Dataset contains synthetic demonstration values; do not treat as real measurements.",
        })

    return {
        "status": "PASS" if not errors else "FAIL",
        "row_count": int(len(df)),
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
    }


def run_pipeline(
    input_file: str | Path = RAW_FILE,
    output_dir: str | Path = OUT_DIR,
    source_register_file: str | Path = SOURCE_REGISTER_FILE,
) -> dict:
    input_file = Path(input_file)
    output_dir = Path(output_dir)
    source_register_file = Path(source_register_file)
    trusted_file = output_dir / "trusted_data.csv"
    validation_file = output_dir / "validation_report.json"
    manifest_file = output_dir / "trusted_manifest.json"

    output_dir.mkdir(parents=True, exist_ok=True)
    if not input_file.exists():
        raise FileNotFoundError(f"Expected input dataset at {input_file}")

    df = normalize_column_names(pd.read_csv(input_file))
    source_register = None
    if source_register_file.exists():
        source_register = normalize_column_names(pd.read_csv(source_register_file))

    missing_columns = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if not missing_columns:
        for col in ["company", "facility", "geography", "metric", "unit", "source_name"]:
            df[col] = df[col].astype("string").str.strip()
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df["data_year"] = pd.to_numeric(df["data_year"], errors="coerce")
        df = populate_source_urls(df, source_register)

    report = validate_dataframe(df, source_register=source_register)
    validation_file.write_text(json.dumps(report, indent=2), encoding="utf-8")

    if report["status"] != "PASS":
        raise ValueError(
            f"Dataset validation failed with {report['error_count']} error(s). "
            f"Review {validation_file}"
        )

    df["data_year"] = df["data_year"].astype("Int64")
    df = order_columns(df)
    df.to_csv(trusted_file, index=False)
    write_manifest(
        trusted_file,
        manifest_file,
        purpose="Trusted normalized dataset generated by the project pipeline",
    )
    report["trusted_file"] = str(trusted_file)
    report["validation_file"] = str(validation_file)
    report["manifest_file"] = str(manifest_file)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate and normalize an environmental data CSV.")
    parser.add_argument(
        "--input",
        type=Path,
        default=RAW_FILE,
        help=f"Input CSV (default: {RAW_FILE})",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=OUT_DIR,
        help=f"Output directory (default: {OUT_DIR})",
    )
    parser.add_argument(
        "--source-register",
        type=Path,
        default=SOURCE_REGISTER_FILE,
        help=f"Canonical source register (default: {SOURCE_REGISTER_FILE})",
    )
    args = parser.parse_args()
    result = run_pipeline(args.input, args.output_dir, args.source_register)
    print(json.dumps(result, indent=2))
    print(f"\nTrusted dataset: {result['trusted_file']}")
    print(f"Validation report: {result['validation_file']}")
    print(f"Integrity manifest: {result['manifest_file']}")
