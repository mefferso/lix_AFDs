from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROMPT_PATH = ROOT / "prompts" / "afd_prompt.md"
REVIEW_PROMPT_PATH = ROOT / "prompts" / "review_package_prompt.md"
MODEL_REVIEW_PROMPT_PATH = ROOT / "prompts" / "model_review_prompt.md"


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


def _status_counts(items: list[dict] | None) -> dict:
    counts = {"ok": 0, "error": 0, "other": 0}
    if not isinstance(items, list):
        return counts
    for item in items:
        status = item.get("status")
        if status == "ok":
            counts["ok"] += 1
        elif status == "error":
            counts["error"] += 1
        else:
            counts["other"] += 1
    return counts


def _first_lines_from_external(package_dir: Path, external_manifest: list[dict] | None, max_chars_each: int = 4000) -> str:
    if not isinstance(external_manifest, list):
        return "[no external source manifest found]"

    chunks = []
    for item in external_manifest:
        if item.get("status") != "ok":
            chunks.append(f"## {item.get('name')}\nERROR: {item.get('error', 'unknown error')}\n")
            continue
        rel = item.get("path")
        if not rel:
            continue
        text = _read_text_if_exists(package_dir / rel, max_chars=max_chars_each)
        chunks.append(f"## {item.get('name')}\nPurpose: {item.get('purpose')}\nSource: {item.get('url')}\n\n```text\n{text}\n```\n")
    return "\n".join(chunks)


def _sounding_status(sounding_manifest: dict | None) -> str:
    if not isinstance(sounding_manifest, dict):
        return "missing"
    return str(sounding_manifest.get("status", "unknown"))


def _sounding_markdown(sounding_state: str, sounding_summary_md_path: Path) -> str:
    if sounding_state == "disabled":
        return "Observed upper-air sounding collection is disabled for this GitHub workflow because the configured source was unreliable from GitHub Actions. Add observed/model sounding context manually if needed."
    return _read_text_if_exists(sounding_summary_md_path, max_chars=18000)


def _write_start_here(
    package_dir: Path,
    now_utc: str,
    obs_count: int,
    obs_error_count: int,
    external_counts: dict,
    screenshot_counts: dict,
    model_source_count: int,
    sounding_state: str,
) -> None:
    lines = []
    lines.append("# START HERE")
    lines.append("")
    lines.append(f"Created UTC: {now_utc}")
    lines.append("")
    lines.append("## Package status")
    lines.append("")
    lines.append(f"- Surface obs stations collected: {obs_count}")
    lines.append(f"- Surface obs station errors: {obs_error_count}")
    lines.append(f"- External text sources OK/errors: {external_counts['ok']}/{external_counts['error']}")
    lines.append(f"- Screenshots OK/errors: {screenshot_counts['ok']}/{screenshot_counts['error']}")
    lines.append(f"- Model context sources: {model_source_count}")
    lines.append(f"- Sounding status: {sounding_state}")
    lines.append("")
    lines.append("## Fast workflow")
    lines.append("")
    lines.append("1. Open `package_review.md` first and make sure the quick counts look clean.")
    lines.append("2. Open `model_context/model_notes_template.md` and add quick HRRR/RAP/NBM/HREF/WPC notes if model guidance matters for this AFD.")
    lines.append("3. Upload `ai_context.md` to ChatGPT.")
    lines.append("4. Also upload or paste the filled model notes when you have them.")
    lines.append("5. Ask for either a package review or a first-pass AFD draft.")
    lines.append("")
    lines.append("## What to upload to ChatGPT")
    lines.append("")
    lines.append("For package review:")
    lines.append("")
    lines.append("```text")
    lines.append("package_review.md")
    lines.append("ai_context.md")
    lines.append("model_context/model_notes_template.md  # if filled out")
    lines.append("```")
    lines.append("")
    lines.append("For AFD drafting:")
    lines.append("")
    lines.append("```text")
    lines.append("ai_context.md")
    lines.append("model_context/model_notes_template.md  # filled out if possible")
    lines.append("any radar/satellite/model screenshots you want the AI to see")
    lines.append("```")
    lines.append("")
    lines.append("## Suggested prompts")
    lines.append("")
    lines.append("Review only:")
    lines.append("")
    lines.append("```text")
    lines.append("Review this AFD package. Do not draft yet. Tell me what is strong, what is missing, and what I need to manually check before using AI text.")
    lines.append("```")
    lines.append("")
    lines.append("Draft:")
    lines.append("")
    lines.append("```text")
    lines.append("Using this package and my model notes, draft a first-pass LIX AFD. Do not invent missing data. Clearly flag assumptions and items needing human review.")
    lines.append("```")
    lines.append("")
    lines.append("## Human reminders")
    lines.append("")
    lines.append("- This package is a starting point, not an official forecast decision engine.")
    lines.append("- Check radar, satellite, AWIPS/local procedures, collaboration notes, current hazards, and latest model guidance before using any generated text.")
    lines.append("- Sounding collection is currently disabled in GitHub Actions, so add observed or model sounding context manually when it matters.")
    lines.append("")
    (package_dir / "START_HERE.md").write_text("\n".join(lines), encoding="utf-8")


def build_ai_context(package_dir: Path, config: dict) -> None:
    office = config["office"]
    now_utc = datetime.now(timezone.utc).isoformat()

    obs_summary_path = package_dir / "observations" / "latest_surface_obs_summary.json"
    text_manifest_path = package_dir / "text_products" / "text_product_manifest.json"
    screenshot_manifest_path = package_dir / "screenshots" / "screenshot_manifest.json"
    external_manifest_path = package_dir / "external_sources" / "external_sources_manifest.json"
    sounding_manifest_path = package_dir / "soundings" / "sounding_manifest.json"
    sounding_summary_path = package_dir / "soundings" / "sounding_summary.json"
    sounding_summary_md_path = package_dir / "soundings" / "sounding_summary.md"
    model_manifest_path = package_dir / "model_context" / "model_source_manifest.json"
    model_context_md_path = package_dir / "model_context" / "model_context.md"

    obs_summary = _load_json_if_exists(obs_summary_path)
    text_manifest = _load_json_if_exists(text_manifest_path)
    screenshot_manifest = _load_json_if_exists(screenshot_manifest_path)
    external_manifest = _load_json_if_exists(external_manifest_path)
    sounding_manifest = _load_json_if_exists(sounding_manifest_path)
    sounding_summary = _load_json_if_exists(sounding_summary_path)
    model_manifest = _load_json_if_exists(model_manifest_path)

    prompt_text = _read_text_if_exists(PROMPT_PATH)
    review_prompt_text = _read_text_if_exists(REVIEW_PROMPT_PATH)
    model_review_prompt_text = _read_text_if_exists(MODEL_REVIEW_PROMPT_PATH)
    previous_afd = _read_text_if_exists(package_dir / "text_products" / "previous_afd.txt")
    external_excerpt = _first_lines_from_external(package_dir, external_manifest)
    model_context_md = _read_text_if_exists(model_context_md_path, max_chars=18000)

    obs_count = len(obs_summary.get("stations", [])) if isinstance(obs_summary, dict) else 0
    obs_error_count = len(obs_summary.get("errors", [])) if isinstance(obs_summary, dict) else 0
    screenshot_counts = _status_counts(screenshot_manifest)
    external_counts = _status_counts(external_manifest)
    model_source_count = len(model_manifest) if isinstance(model_manifest, list) else 0
    sounding_state = _sounding_status(sounding_manifest)
    sounding_md = _sounding_markdown(sounding_state, sounding_summary_md_path)

    _write_start_here(
        package_dir,
        now_utc,
        obs_count,
        obs_error_count,
        external_counts,
        screenshot_counts,
        model_source_count,
        sounding_state,
    )

    manifest = {
        "created_utc": now_utc,
        "office": office,
        "files": _relative_inventory(package_dir),
        "start_here": "START_HERE.md",
        "surface_obs_summary": "observations/latest_surface_obs_summary.json",
        "text_product_manifest": "text_products/text_product_manifest.json",
        "external_sources_manifest": "external_sources/external_sources_manifest.json",
        "model_source_manifest": "model_context/model_source_manifest.json",
        "model_context": "model_context/model_context.md",
        "sounding_manifest": "soundings/sounding_manifest.json",
        "sounding_summary": "soundings/sounding_summary.json",
        "screenshot_manifest": "screenshots/screenshot_manifest.json",
        "prompt": "prompts/afd_prompt.md",
        "review_prompt": "prompts/review_package_prompt.md",
        "model_review_prompt": "prompts/model_review_prompt.md",
    }

    (package_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    review_lines = []
    review_lines.append("# AFD Package Review")
    review_lines.append("")
    review_lines.append(f"Created UTC: {now_utc}")
    review_lines.append(f"Office: {office.get('wfo')} - {office.get('cwa_name')}")
    review_lines.append("")
    review_lines.append("## Quick counts")
    review_lines.append("")
    review_lines.append(f"- Surface obs stations collected: {obs_count}")
    review_lines.append(f"- Surface obs station errors: {obs_error_count}")
    review_lines.append(f"- External text sources OK/errors: {external_counts['ok']}/{external_counts['error']}")
    review_lines.append(f"- Screenshots OK/errors: {screenshot_counts['ok']}/{screenshot_counts['error']}")
    review_lines.append(f"- Model context sources: {model_source_count}")
    review_lines.append(f"- Sounding status: {sounding_state}")
    review_lines.append("")
    review_lines.append("## Start here")
    review_lines.append("")
    review_lines.append("Open `START_HERE.md` for the recommended review/drafting workflow.")
    review_lines.append("")
    review_lines.append("## Sounding summary")
    review_lines.append("")
    review_lines.append("```json")
    review_lines.append(json.dumps(sounding_summary, indent=2) if sounding_summary is not None else "{}")
    review_lines.append("```")
    review_lines.append("")
    review_lines.append("## Model context review prompt")
    review_lines.append("")
    review_lines.append(model_review_prompt_text)
    review_lines.append("")
    review_lines.append("## Suggested AI review prompt")
    review_lines.append("")
    review_lines.append(review_prompt_text)
    review_lines.append("")
    review_lines.append("## Human note")
    review_lines.append("")
    review_lines.append("If this package is missing radar/satellite/model/sounding context, do not let the AI write with fake confidence. Use it as a starting point only.")
    review_lines.append("")
    (package_dir / "package_review.md").write_text("\n".join(review_lines), encoding="utf-8")

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
    md.append("## Package quick counts")
    md.append("")
    md.append(f"- Surface obs stations collected: {obs_count}")
    md.append(f"- Surface obs station errors: {obs_error_count}")
    md.append(f"- External text sources OK/errors: {external_counts['ok']}/{external_counts['error']}")
    md.append(f"- Screenshots OK/errors: {screenshot_counts['ok']}/{screenshot_counts['error']}")
    md.append(f"- Model context sources: {model_source_count}")
    md.append(f"- Sounding status: {sounding_state}")
    md.append("")
    md.append("## Surface observations summary")
    md.append("")
    md.append("```json")
    md.append(json.dumps(obs_summary, indent=2) if obs_summary is not None else "{}")
    md.append("```")
    md.append("")
    md.append("## Sounding summary")
    md.append("")
    md.append(sounding_md)
    md.append("")
    md.append("## Model context")
    md.append("")
    md.append(model_context_md)
    md.append("")
    md.append("## Text product manifest")
    md.append("")
    md.append("```json")
    md.append(json.dumps(text_manifest, indent=2) if text_manifest is not None else "{}")
    md.append("```")
    md.append("")
    md.append("## External source manifest")
    md.append("")
    md.append("```json")
    md.append(json.dumps(external_manifest, indent=2) if external_manifest is not None else "[]")
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
    md.append("## External source excerpts")
    md.append("")
    md.append(external_excerpt)
    md.append("")
    md.append("## Human forecaster reminder")
    md.append("")
    md.append("This package is only a starting point. Check radar, satellite, latest obs, AWIPS/local procedures, collaboration notes, and current hazards before using any generated text.")
    md.append("")

    (package_dir / "ai_context.md").write_text("\n".join(md), encoding="utf-8")
