from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import yaml

from collect_observed import collect_observed_package
from collect_text_products import collect_text_products
from collect_external_sources import collect_external_text_sources
from collect_soundings import collect_soundings
from collect_model_context import collect_model_context
from collect_current_trends_context import collect_current_trends_context
from collect_notes_form import collect_notes_form
from collect_analysis_context import collect_analysis_context
from collect_screenshots import collect_screenshots
from package_ai_context import build_ai_context

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "config.yaml"
OUTPUT_ROOT = ROOT / "output" / "latest"


def load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main() -> None:
    config = load_config()
    run_time = datetime.now(timezone.utc).strftime("%Y%m%d_%H%MZ")
    package_dir = OUTPUT_ROOT / run_time
    package_dir.mkdir(parents=True, exist_ok=True)

    print(f"Creating AFD input package: {package_dir}")

    collect_observed_package(package_dir, config)
    collect_text_products(package_dir, config)
    collect_external_text_sources(package_dir, config)
    collect_soundings(package_dir, config)
    collect_model_context(package_dir, config)
    collect_current_trends_context(package_dir, config)
    collect_notes_form(package_dir, config)
    collect_analysis_context(package_dir, config)
    collect_screenshots(package_dir, config)
    build_ai_context(package_dir, config)

    print("Done.")
    print(f"Package: {package_dir}")
    print(f"Review file: {package_dir / 'package_review.md'}")
    print(f"Model context: {package_dir / 'model_context' / 'model_context.md'}")
    print(f"Notes form: {package_dir / 'forecast_notes_form.html'}")
    print(f"Analysis context: {package_dir / 'analysis_context' / 'analysis_screenshots_manifest.json'}")
    print(f"AI context: {package_dir / 'ai_context.md'}")


if __name__ == "__main__":
    main()
