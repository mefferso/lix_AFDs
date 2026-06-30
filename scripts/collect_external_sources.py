from __future__ import annotations

import html
import json
import re
from pathlib import Path

from http_helpers import get_text


def _slugify(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", name).strip("_")


def _clean_external_text(raw: str) -> str:
    """Make web/text products less awful for AI context.

    SPC .txt products are already clean. NHC ?text pages and some WPC pages
    still return lightweight HTML, so strip tags and collapse excessive blanks.
    """
    text = raw
    if "<html" in raw.lower() or "<body" in raw.lower() or "<!doctype" in raw.lower():
        text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
        text = re.sub(r"</p>|</div>|</li>|</tr>|</h\d>", "\n", text, flags=re.IGNORECASE)
        text = re.sub(r"<[^>]+>", "", text)
        text = html.unescape(text)

    lines = [line.rstrip() for line in text.splitlines()]
    cleaned = []
    blank_count = 0
    for line in lines:
        if line.strip():
            cleaned.append(line)
            blank_count = 0
        else:
            blank_count += 1
            if blank_count <= 1:
                cleaned.append("")
    return "\n".join(cleaned).strip() + "\n"


def collect_external_text_sources(outdir: Path, config: dict) -> None:
    cfg = config.get("external_text_sources", {})
    external_dir = outdir / "external_sources"
    external_dir.mkdir(exist_ok=True)

    manifest = []

    if not cfg.get("enabled", True):
        (external_dir / "external_sources_DISABLED.txt").write_text(
            "External text source collection disabled in config/config.yaml\n",
            encoding="utf-8",
        )
        return

    user_agent = config["nws_api"]["user_agent"]

    for name, item in cfg.get("sources", {}).items():
        safe_name = _slugify(name)
        url = item["url"]
        purpose = item.get("purpose", "")
        out_path = external_dir / f"{safe_name}.txt"

        try:
            raw_text = get_text(url, user_agent=user_agent, timeout=45)
            text = _clean_external_text(raw_text)
            out_path.write_text(text, encoding="utf-8", errors="replace")
            manifest.append({
                "name": name,
                "url": url,
                "purpose": purpose,
                "path": f"external_sources/{safe_name}.txt",
                "status": "ok",
                "bytes": out_path.stat().st_size,
            })
        except Exception as e:
            err_path = external_dir / f"{safe_name}_ERROR.txt"
            err_path.write_text(str(e), encoding="utf-8")
            manifest.append({
                "name": name,
                "url": url,
                "purpose": purpose,
                "path": f"external_sources/{safe_name}_ERROR.txt",
                "status": "error",
                "error": str(e),
            })

    (external_dir / "external_sources_manifest.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )
