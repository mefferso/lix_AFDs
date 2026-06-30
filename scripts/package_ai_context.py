from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "afd_prompt.md"


def _read_text_if_exists(path: Path, max_chars: int = 25000) -> str:
    if not path.exists():
        return f"[missing: {path.name}]"
    text = path.read_text(encoding="utf-8", errors="replace")
    if len(text) > max_chars:
        return text[:max_chars] + "\n\n[truncated]"
    return text


def _load_json_if_exists(path: Path) -> dict | list | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _relative_inventory(package_dir: Path) -> list[dict]:
    items = []
    for path in sorted(package_dir.rglob("*")):
        if path.is_file():
            items.append({
                "path": str(path.relative_to(package_dir)).replace("\\", "/"),
                "bytes": path.stat().st_size,
            })
    return items


def build_ai_context(package_dir: Path, config: dict) -> None:
    office = config["office"]
    now_utc = datetime.now(timezone.utc).isoformat()

    obs_summary_path = package_dir / "observations" / "latest_surface_obs_summary.json"
    text_manifest_path = package_dir / "text_products" / "text_product_manifest.json"
    screenshot_manifest_path = package_dir / "screenshots" / "screenshot_manifest.json"

    manifest = {
        "created_utc": now_utc,
        "office": office,
        "files": _relative_inventory(package_dir),
        "surface_obs_summary": "observations/latest_surface_obs_summary.json",
        "text_product_manifest": "text_products/text_product_manifest.json",
        "screenshot_manifest": "screenshots/screenshot_manifest.json",
        "prompt": "prompts/afd_prompt.md",
    }

    (package_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    prompt_text = _read_text_if_exists(PROMPT_PATH)
    previous_afd = _read_text_if_exists(package_dir / "text_products" / "previous_afd.txt")
    hwo = _read_text_if_exists(package_dir / "text_products" / "hwo.txt")
    obs_summary = _load_json_if_exists(obs_summary_path)
    text_manifest = _load_json_if_exists(text_manifest_path)
    screenshot_manifest = _load_json_if_exists(screenshot_manifest_path)

    md = []
    md.append("# AFD Input Package")
    md.append("")
    md.append(f"Created UTC: {now_utc}")
    md.append(f"Office: {office.get('wfo')} - {office.get('cwa_name')}")
    md.append(f"Forecast area: {office.get('forecast_area')}")
    md.append("")
    md.append("## Drafting instructions")
    md.append("")
    md.append(prompt_text)
    md.append("")
    md.append("## Surface observations summary")
    md.append("")
    md.append("```json")
    md.append(json.dumps(obs_summary, indent=2) if obs_summary is not None else "{}")
    md.append("```")
    md.append("")
    md.append("## Text product manifest")
    md.append("")
    md.append("```json")
    md.append(json.dumps(text_manifest, indent=2) if text_manifest is not None else "{}")
    md.append("```")
    md.append("")
    md.append("## Screenshot manifest")
    md.append("")
    md.append("```json")
    md.append(json.dumps(screenshot_manifest, indent=2) if screenshot_manifest is not None else "[]")
    md.append("```")
    md.append("")
    md.append("## Previous AFD")
    md.append("")
    md.append("```text")
    md.append(previous_afd)
    md.append("```")
    md.append("")
    md.append("## HWO")
    md.append("")
    md.append("```text")
    md.append(hwo)
    md.append("```")
    md.append("")
    md.append("## Human forecaster reminder")
    md.append("")
    md.append("This package is only a starting point. Check radar, satellite, latest obs, AWIPS/local procedures, collaboration notes, and current hazards before using any generated text.")
    md.append("")

    (package_dir / "ai_context.md").write_text("\n".join(md), encoding="utf-8")
