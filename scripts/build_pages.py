"""Build a static, GitHub Pages-compatible copy of the reviewed dashboard."""

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

from climate_dashboard.adversarial import create_adversarial_copy
from climate_dashboard.dashboard import load_dashboard_data
from climate_dashboard.pipeline import run_pipeline
from climate_dashboard.powerbi_export import build_powerbi_pack

UI_DIR = ROOT / "climate_dashboard" / "dashboard_ui"
REVIEWED_DIR = ROOT / "data" / "processed" / "reviewed"


OUTPUT_DIR = ROOT / "site"


def build_site() -> dict:
    """Regenerate reviewed outputs and assemble the static dashboard directory."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    pipeline = run_pipeline(
        input_file=ROOT / "data" / "intake" / "observations_template.csv",
        output_dir=REVIEWED_DIR,
    )
    if pipeline["status"] != "PASS":
        raise RuntimeError(
            "Refusing to publish: reviewed-data validation failed "
            f"with {pipeline['error_count']} errors."
        )

    create_adversarial_copy(
        trusted_file=REVIEWED_DIR / "trusted_data.csv",
        output_dir=REVIEWED_DIR,
    )
    build_powerbi_pack(
        reviewed_dir=REVIEWED_DIR,
        output_dir=ROOT / "data" / "powerbi",
    )

    payload = load_dashboard_data(REVIEWED_DIR)
    if payload["validation"]["status"] != "PASS":
        raise RuntimeError("Refusing to publish a dataset that did not pass validation.")
    if not payload["integrity"]["verified"]:
        raise RuntimeError("Refusing to publish: trusted-data SHA-256 verification failed.")

    html = (UI_DIR / "index.html").read_text(encoding="utf-8")
    html = html.replace('content="/api/data"', 'content="./data.json"')
    html = html.replace('href="/styles.css"', 'href="./styles.css"')
    html = html.replace('src="/app.js"', 'src="./app.js"')
    if 'content="./data.json"' not in html:
        raise RuntimeError("Dashboard HTML is missing its data-source metadata.")
    if 'href="./styles.css"' not in html or 'src="./app.js"' not in html:
        raise RuntimeError("Dashboard HTML asset paths could not be made Pages-compatible.")

    (OUTPUT_DIR / "index.html").write_text(html, encoding="utf-8")
    for asset in ("styles.css", "app.js"):
        shutil.copy2(UI_DIR / asset, OUTPUT_DIR / asset)

    (OUTPUT_DIR / "data.json").write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    (OUTPUT_DIR / ".nojekyll").write_text("", encoding="utf-8")

    required = ("index.html", "styles.css", "app.js", "data.json", ".nojekyll")
    missing = [name for name in required if not (OUTPUT_DIR / name).is_file()]
    if missing:
        raise RuntimeError(f"Static dashboard build is incomplete: {', '.join(missing)}")

    return {
        "output_dir": str(OUTPUT_DIR),
        "record_count": len(payload["trusted"]),
        "validation": payload["validation"]["status"],
        "integrity_verified": payload["integrity"]["verified"],
        "files": list(required),
    }


def main() -> None:
    result = build_site()
    print(
        "Static dashboard build complete: "
        f"{result['record_count']} reviewed records; "
        f"validation {result['validation']}; "
        f"integrity {'verified' if result['integrity_verified'] else 'FAILED'}."
    )
    print(f"Pages files: {', '.join(result['files'])}")
    print(f"Output: {result['output_dir']}")


if __name__ == "__main__":
    main()
