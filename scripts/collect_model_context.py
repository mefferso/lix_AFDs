from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


MODEL_REVIEW_TEMPLATE = {
    "created_utc": None,
    "status": "scaffold_only",
    "note": "This file is a structured placeholder for forecaster-entered or future automated model summaries. It does not contain parsed GRIB/model fields yet.",
    "forecast_problems": {
        "convection_severe": {
            "fields_to_review": ["reflectivity", "updraft helicity", "MLCAPE", "DCAPE", "0-6 km shear", "0-1 km SRH", "low-level convergence/boundaries"],
            "forecaster_notes": ""
        },
        "heavy_rain_hydro": {
            "fields_to_review": ["QPF", "hourly rainfall rates", "PWAT", "850mb moisture transport", "HREF probability-matched mean", "neighborhood exceedance probabilities"],
            "forecaster_notes": ""
        },
        "heat": {
            "fields_to_review": ["NBM temperature", "NBM dewpoint", "heat index", "cloud cover", "convective timing"],
            "forecaster_notes": ""
        },
        "marine": {
            "fields_to_review": ["10m wind", "gusts", "seas", "convective coverage", "waterspout/tropical funnel ingredients"],
            "forecaster_notes": ""
        },
        "aviation": {
            "fields_to_review": ["ceiling", "visibility", "convective timing", "wind shifts", "LLWS/turbulence signals"],
            "forecaster_notes": ""
        },
        "tropical": {
            "fields_to_review": ["surface pressure/vorticity", "850mb vorticity", "deep-layer shear", "moisture", "NHC TWO/TWD context"],
            "forecaster_notes": ""
        }
    }
}


def collect_model_context(outdir: Path, config: dict) -> None:
    model_dir = outdir / "model_context"
    model_dir.mkdir(exist_ok=True)

    cfg = config.get("model_context", {})
    now_utc = datetime.now(timezone.utc).isoformat()

    sources = cfg.get("sources", {})
    source_manifest = []
    for name, item in sources.items():
        source_manifest.append({
            "name": name,
            "url": item.get("url"),
            "purpose": item.get("purpose"),
            "status": "link_only",
        })

    template = MODEL_REVIEW_TEMPLATE.copy()
    template["created_utc"] = now_utc

    (model_dir / "model_source_manifest.json").write_text(
        json.dumps(source_manifest, indent=2),
        encoding="utf-8",
    )
    (model_dir / "model_summary_template.json").write_text(
        json.dumps(template, indent=2),
        encoding="utf-8",
    )

    md = []
    md.append("# Model Context")
    md.append("")
    md.append(f"Created UTC: {now_utc}")
    md.append("")
    md.append("This is a scaffold only. It does not parse GRIB/model fields yet.")
    md.append("")
    md.append("## Model/source links")
    md.append("")
    for item in source_manifest:
        md.append(f"- **{item['name']}**: {item.get('purpose')}")
        md.append(f"  - {item.get('url')}")
    md.append("")
    md.append("## Forecaster model review checklist")
    md.append("")
    md.append("Before using AI to draft an AFD, manually review or add notes for:")
    md.append("")
    for problem, data in template["forecast_problems"].items():
        md.append(f"### {problem}")
        for field in data["fields_to_review"]:
            md.append(f"- {field}")
        md.append("")
    md.append("## Manual notes")
    md.append("")
    md.append("Add model notes here if editing the artifact locally before passing to AI:")
    md.append("")
    md.append("```text")
    md.append("HRRR/RAP/NBM/HREF notes:")
    md.append("- ")
    md.append("```")
    md.append("")

    (model_dir / "model_context.md").write_text("\n".join(md), encoding="utf-8")
