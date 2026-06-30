from __future__ import annotations

import json
from pathlib import Path


def collect_screenshots(outdir: Path, config: dict) -> None:
    screenshot_cfg = config.get("screenshots", {})
    img_dir = outdir / "screenshots"
    img_dir.mkdir(exist_ok=True)

    manifest = []

    if not screenshot_cfg.get("enabled", True):
        with open(img_dir / "screenshots_DISABLED.txt", "w", encoding="utf-8") as f:
            f.write("Screenshot collection disabled in config/config.yaml\n")
        return

    try:
        from playwright.sync_api import sync_playwright
    except Exception as e:
        with open(img_dir / "playwright_IMPORT_ERROR.txt", "w", encoding="utf-8") as f:
            f.write(str(e))
        return

    width = int(screenshot_cfg.get("viewport_width", 1600))
    height = int(screenshot_cfg.get("viewport_height", 1000))
    pages = screenshot_cfg.get("pages", {})

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height})

        for name, item in pages.items():
            url = item["url"]
            output_path = img_dir / f"{name}.png"
            try:
                page.goto(url, wait_until="networkidle", timeout=60000)
                page.screenshot(path=str(output_path), full_page=True)
                manifest.append({
                    "name": name,
                    "url": url,
                    "purpose": item.get("purpose"),
                    "path": f"screenshots/{name}.png",
                    "status": "ok",
                })
            except Exception as e:
                err_path = img_dir / f"{name}_ERROR.txt"
                err_path.write_text(str(e), encoding="utf-8")
                manifest.append({
                    "name": name,
                    "url": url,
                    "purpose": item.get("purpose"),
                    "path": f"screenshots/{name}_ERROR.txt",
                    "status": "error",
                    "error": str(e),
                })

        browser.close()

    with open(img_dir / "screenshot_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
