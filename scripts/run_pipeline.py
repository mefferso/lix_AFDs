from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import yaml

from collect_observed import collect_observed_package
from collect_text_products import collect_text_products
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
    collect_screenshots(package_dir, config)
    build_ai_context(package_dir, config)

    print("Done.")
    print(f"Package: {package_dir}")
    print(f"AI context: {package_dir / 'ai_context.md'}")


if __name__ == "__main__":
    main()
