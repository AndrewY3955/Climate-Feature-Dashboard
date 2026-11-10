"""SHA-256 integrity helpers. A trusted manifest must be protected separately."""

import hashlib
import json
import re
import sys
from pathlib import Path


_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_manifest(file_path: str | Path, manifest_path: str | Path, purpose: str) -> dict:
    file_path = Path(file_path)
    payload = {
        "file": file_path.name,
        "sha256": sha256_file(file_path),
        "purpose": purpose,
        "warning": (
            "Integrity verification requires this manifest to be protected. "
            "If both the data file and manifest can be changed by the same attacker, "
            "the hash check alone is not sufficient."
        ),
    }
    Path(manifest_path).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def verify_manifest(file_path: str | Path, manifest_path: str | Path) -> tuple[bool, str, str]:
    file_path = Path(file_path)
    manifest_path = Path(manifest_path)
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Unable to read a valid integrity manifest: {manifest_path}") from exc

    if not isinstance(manifest, dict):
        raise ValueError("Integrity manifest must contain a JSON object.")
    if manifest.get("file") != file_path.name:
        raise ValueError("Integrity manifest file name does not match the dataset.")
    expected = manifest.get("sha256")
    if not isinstance(expected, str) or not _SHA256_PATTERN.fullmatch(expected):
        raise ValueError("Integrity manifest must contain a 64-character lowercase SHA-256 digest.")

    actual = sha256_file(file_path)
    return actual == expected, expected, actual


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: python -m climate_dashboard.integrity <data.csv> <manifest.json>")
        return 2

    try:
        ok, expected, actual = verify_manifest(sys.argv[1], sys.argv[2])
    except (OSError, ValueError) as exc:
        print(f"INTEGRITY ERROR: {exc}")
        return 1

    print(f"Expected SHA-256: {expected}")
    print(f"Actual SHA-256:   {actual}")
    print("INTEGRITY OK" if ok else "INTEGRITY FAILURE: file differs from trusted reference")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
