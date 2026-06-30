from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


SPC_SECTOR_URL = "https://www.spc.noaa.gov/exper/mesoanalysis/new/viewsector.php?sector=18"

FIELDS = [
    {
        "name": "spc_se_sector_overview",
        "label": None,
        "purpose": "SPC southeast sector mesoanalysis overview page",
    },
    {
        "name": "spc_500mb_analysis",
        "label": "500mb Analysis",
        "purpose": "midlevel height/wind pattern for synoptic setup",
    },
    {
        "name": "spc_850mb_analysis",
        "label": "850mb Analysis",
        "purpose": "low-level wind/moisture pattern",
    },
    {
        "name": "spc_mixed_layer_cape",
        "label": "CAPE - 100mb Mixed-Layer",
        "purpose": "mixed-layer instability analysis",
    },
    {
        "name": "spc_downdraft_cape",
        "label": "CAPE - Downdraft",
        "purpose": "downdraft instability and gust potential",
    },
    {
        "name": "spc_effective_bulk_shear",
        "label": "Bulk Shear - Effective",
        "purpose": "deep-layer shear / storm organization support",
    },
    {
        "name": "spc_srh_0_1km",
        "label": "SR Helicity - Sfc-1km",
        "purpose": "low-level helicity / rotation support",
    },
    {
        "name": "spc_pwat_moisture_transport",
        "label": "Precipitable Water (w/ 850mb Moisture Transport Vector)",
        "purpose": "deep moisture and low-level moisture transport",
    },
    {
        "name": "spc_850mb_moisture_transport",
        "label": "850mb Moisture Transport",
        "purpose": "low-level moisture transport and heavy-rain support",
    },
]


def _write_analysis_prompt(analysis_dir: Path) -> None:
    text = """# Analysis Context Prompt

Use these analysis-context screenshots with ai_context.md before drafting.

Tasks:

1. Diagnose the synoptic pattern.
2. Diagnose the mesoscale environment.
3. Identify what is observed versus inferred from analysis graphics.
4. Summarize heat, convection, heavy-rain, aviation, and marine implications.
5. Flag missing data or screenshots that failed.
6. Do not invent exact values unless they are readable in the image or supplied elsewhere.

Suggested user prompt:

```text
Use ai_context.md, my notes, and the analysis_context screenshots to diagnose the synoptic and mesoscale setup first. Then draft the AFD. Do not invent missing data.
```
"""
    (analysis_dir / "analysis_prompt.md").write_text(text, encoding="utf-8")


def collect_analysis_context(outdir: Path, config: dict) -> None:
    analysis_dir = outdir / "analysis_context"
    analysis_dir.mkdir(exist_ok=True)

    manifest = []
    now_utc = datetime.now(timezone.utc).isoformat()

    try:
        from playwright.sync_api import sync_playwright
    except Exception as e:
        (analysis_dir / "playwright_IMPORT_ERROR.txt").write_text(str(e), encoding="utf-8")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1600, "height": 1000})

        for field in FIELDS:
            name = field["name"]
            label = field["label"]
            output_path = analysis_dir / f"{name}.png"
            try:
                page.goto(SPC_SECTOR_URL, wait_until="networkidle", timeout=60000)
                if label:
                    page.get_by_text(label, exact=True).first.click(timeout=10000)
                    page.wait_for_timeout(2500)
                page.screenshot(path=str(output_path), full_page=True)
                manifest.append({
                    "name": name,
                    "source": "SPC mesoanalysis southeast sector",
                    "url": SPC_SECTOR_URL,
                    "clicked_label": label,
                    "purpose": field["purpose"],
                    "path": f"analysis_context/{name}.png",
                    "status": "ok",
                    "created_utc": now_utc,
                })
            except Exception as e:
                err_path = analysis_dir / f"{name}_ERROR.txt"
                err_path.write_text(str(e), encoding="utf-8")
                manifest.append({
                    "name": name,
                    "source": "SPC mesoanalysis southeast sector",
                    "url": SPC_SECTOR_URL,
                    "clicked_label": label,
                    "purpose": field["purpose"],
                    "path": f"analysis_context/{name}_ERROR.txt",
                    "status": "error",
                    "error": str(e),
                    "created_utc": now_utc,
                })

        browser.close()

    _write_analysis_prompt(analysis_dir)
    (analysis_dir / "analysis_screenshots_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
