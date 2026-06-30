from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests


SPC_SOUNDING_BASE = "https://www.spc.noaa.gov/exper/soundings"


def _candidate_cycles(now: datetime, cycles_to_try: int = 4) -> list[datetime]:
    now = now.astimezone(timezone.utc)
    base_hour = 12 if now.hour >= 12 else 0
    cycle = now.replace(hour=base_hour, minute=0, second=0, microsecond=0)
    cycles = []
    while len(cycles) < cycles_to_try:
        cycles.append(cycle)
        cycle -= timedelta(hours=12)
    return cycles


def _spc_obs_url(station: str, cycle: datetime) -> str:
    # Example: https://www.spc.noaa.gov/exper/soundings/26063012_OBS/LIX.gif
    stamp = cycle.strftime("%y%m%d%H")
    return f"{SPC_SOUNDING_BASE}/{stamp}_OBS/{station.upper()}.gif"


def _write_sounding_prompt(sounding_dir: Path) -> None:
    text = """# Sounding Context Prompt

Use these sounding images with ai_context.md and analysis_context screenshots.

Tasks:

1. Summarize the observed thermodynamic profile.
2. Summarize the observed wind profile and hodograph clues.
3. Pull out only readable parameters from the image.
4. Explain implications for heat, convection, heavy rain, severe wind, tornado/waterspout risk, aviation, and marine.
5. Clearly flag anything not readable from the image.
6. Do not invent exact values.

Suggested user prompt:

```text
Use ai_context.md, my notes, analysis_context screenshots, and the sounding image to diagnose the environment first. Then draft the AFD. Do not invent missing data.
```
"""
    (sounding_dir / "sounding_prompt.md").write_text(text, encoding="utf-8")


def collect_sounding_images(outdir: Path, config: dict) -> None:
    sounding_dir = outdir / "sounding_images"
    sounding_dir.mkdir(exist_ok=True)

    station = str(config.get("upper_air", {}).get("station_name", "LIX")).upper()
    if station.startswith("K") and len(station) == 4:
        station = station[1:]

    manifest = []
    headers = {"User-Agent": config.get("nws_api", {}).get("user_agent", "lix-afd-assistant")}

    for cycle in _candidate_cycles(datetime.now(timezone.utc)):
        url = _spc_obs_url(station, cycle)
        try:
            resp = requests.get(url, headers=headers, timeout=20)
            content_type = resp.headers.get("content-type", "")
            if resp.status_code == 200 and resp.content.startswith(b"GIF"):
                rel_path = f"sounding_images/spc_observed_{station}_{cycle.strftime('%Y%m%d_%HZ')}.gif"
                out_path = outdir / rel_path
                out_path.write_bytes(resp.content)
                manifest.append({
                    "name": "spc_observed_sounding",
                    "station": station,
                    "cycle_utc": cycle.isoformat(),
                    "source": "SPC observed sounding image",
                    "url": url,
                    "path": rel_path,
                    "status": "ok",
                    "content_type": content_type,
                    "bytes": len(resp.content),
                })
                break
            manifest.append({
                "name": "spc_observed_sounding_attempt",
                "station": station,
                "cycle_utc": cycle.isoformat(),
                "source": "SPC observed sounding image",
                "url": url,
                "status": "error",
                "error": f"HTTP {resp.status_code}, content-type {content_type}, bytes {len(resp.content)}",
            })
        except Exception as e:
            manifest.append({
                "name": "spc_observed_sounding_attempt",
                "station": station,
                "cycle_utc": cycle.isoformat(),
                "source": "SPC observed sounding image",
                "url": url,
                "status": "error",
                "error": str(e),
            })

    if not any(item.get("status") == "ok" for item in manifest):
        (sounding_dir / "spc_observed_sounding_ERROR.txt").write_text(
            "No SPC observed sounding GIF was found for recent cycles. See sounding_images_manifest.json for attempts.\n",
            encoding="utf-8",
        )

    _write_sounding_prompt(sounding_dir)
    (sounding_dir / "sounding_images_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
