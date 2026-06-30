from __future__ import annotations

import html
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

from http_helpers import get_text


UWYO_URL = "https://weather.uwyo.edu/cgi-bin/sounding"


def _candidate_cycles(now: datetime, count: int) -> list[datetime]:
    """Return recent standard 00/12Z cycles, newest first."""
    now = now.astimezone(timezone.utc)
    base_hour = 12 if now.hour >= 12 else 0
    cycle = now.replace(hour=base_hour, minute=0, second=0, microsecond=0)
    cycles = []
    while len(cycles) < count:
        cycles.append(cycle)
        cycle -= timedelta(hours=12)
    return cycles


def _strip_html_to_pre_text(raw: str) -> str:
    match = re.search(r"<pre[^>]*>(.*?)</pre>", raw, flags=re.IGNORECASE | re.DOTALL)
    text = match.group(1) if match else raw
    text = re.sub(r"<[^>]+>", "", text)
    return html.unescape(text).strip()


def _build_uwyo_url(cycle: datetime, region: str, station_id: str) -> str:
    from_to = f"{cycle.day:02d}{cycle.hour:02d}"
    return (
        f"{UWYO_URL}?region={region}"
        f"&TYPE=TEXT%3ALIST"
        f"&YEAR={cycle.year:04d}"
        f"&MONTH={cycle.month:02d}"
        f"&FROM={from_to}&TO={from_to}"
        f"&STNM={station_id}"
    )


def _find_float(patterns: list[str], text: str) -> float | None:
    for pattern in patterns:
        m = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        if m:
            try:
                return float(m.group(1))
            except Exception:
                continue
    return None


def _parse_indices(text: str) -> dict:
    """Parse common indices from UWyo sounding text.

    This intentionally stays conservative. If a field is not clearly present,
    it returns None rather than inventing a value.
    """
    return {
        "lifted_index_C": _find_float([r"Lifted index:\s*([-+]?\d+(?:\.\d+)?)"], text),
        "showalter_index_C": _find_float([r"Showalter index:\s*([-+]?\d+(?:\.\d+)?)"], text),
        "k_index_C": _find_float([r"K index:\s*([-+]?\d+(?:\.\d+)?)"], text),
        "total_totals_index_C": _find_float([r"Totals totals index:\s*([-+]?\d+(?:\.\d+)?)", r"Total Totals Index:\s*([-+]?\d+(?:\.\d+)?)"], text),
        "cape_jkg": _find_float([r"Convective Available Potential Energy:\s*([-+]?\d+(?:\.\d+)?)", r"CAPE:\s*([-+]?\d+(?:\.\d+)?)"], text),
        "cin_jkg": _find_float([r"Convective Inhibition:\s*([-+]?\d+(?:\.\d+)?)", r"CINS?:\s*([-+]?\d+(?:\.\d+)?)"], text),
        "precipitable_water_mm": _find_float([r"Precipitable water \[mm\]:\s*([-+]?\d+(?:\.\d+)?)", r"Precipitable water:\s*([-+]?\d+(?:\.\d+)?)"], text),
        "lcl_pressure_hpa": _find_float([r"LCL pressure:\s*([-+]?\d+(?:\.\d+)?)"], text),
        "lcl_temperature_C": _find_float([r"LCL temperature:\s*([-+]?\d+(?:\.\d+)?)"], text),
        "lfc_pressure_hpa": _find_float([r"LFC pressure:\s*([-+]?\d+(?:\.\d+)?)"], text),
        "el_pressure_hpa": _find_float([r"EL pressure:\s*([-+]?\d+(?:\.\d+)?)"], text),
    }


def _mm_to_inches(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value / 25.4, 2)


def _sounding_looks_valid(text: str) -> bool:
    upper = text.upper()
    table_tokens = ["PRES", "HGHT", "TEMP", "DWPT"]
    has_table = all(token in upper for token in table_tokens)
    has_indices = "STATION INFORMATION" in upper or "LIFTED INDEX" in upper or "PRECIPITABLE WATER" in upper
    not_empty_error = "CAN'T GET" not in upper and "NO DATA" not in upper and "ERROR" not in upper[:500]
    return len(text) > 500 and not_empty_error and (has_table or has_indices)


def _preview(text: str, limit: int = 500) -> str:
    cleaned = "\n".join(line.rstrip() for line in text.splitlines()[:20])
    if len(cleaned) > limit:
        return cleaned[:limit] + "..."
    return cleaned


def collect_soundings(outdir: Path, config: dict) -> None:
    cfg = config.get("upper_air", {})
    sound_dir = outdir / "soundings"
    sound_dir.mkdir(exist_ok=True)

    station_ids = cfg.get("station_ids_to_try") or [cfg.get("station_wmo", "72233"), cfg.get("station_name", "KLIX")]
    station_ids = [str(s) for s in station_ids if s]

    manifest: dict = {
        "enabled": cfg.get("enabled", True),
        "source": cfg.get("source"),
        "station_name": cfg.get("station_name"),
        "station_wmo": cfg.get("station_wmo"),
        "station_ids_to_try": station_ids,
        "attempts": [],
        "selected": None,
        "status": "not_run",
    }

    if not cfg.get("enabled", True):
        manifest["status"] = "disabled"
        (sound_dir / "sounding_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return

    user_agent = config["nws_api"]["user_agent"]
    region = cfg.get("region", "naconf")
    cycles_to_try = int(cfg.get("cycles_to_try", 4))
    request_timeout = int(cfg.get("request_timeout_seconds", 8))

    selected_text = None
    selected_cycle = None
    selected_url = None
    selected_station_id = None

    for cycle in _candidate_cycles(datetime.now(timezone.utc), cycles_to_try):
        for station_id in station_ids:
            url = _build_uwyo_url(cycle, region=region, station_id=station_id)
            attempt = {
                "cycle_utc": cycle.strftime("%Y-%m-%d %HZ"),
                "station_id": station_id,
                "url": url,
                "timeout_seconds": request_timeout,
            }
            try:
                raw = get_text(url, user_agent=user_agent, timeout=request_timeout)
                text = _strip_html_to_pre_text(raw)
                valid = _sounding_looks_valid(text)
                attempt["bytes"] = len(text.encode("utf-8"))
                attempt["valid"] = valid
                attempt["preview"] = _preview(text)
                if valid and selected_text is None:
                    selected_text = text
                    selected_cycle = cycle
                    selected_url = url
                    selected_station_id = station_id
                    manifest["attempts"].append(attempt)
                    break
            except Exception as e:
                attempt["error"] = str(e)
                attempt["valid"] = False
            manifest["attempts"].append(attempt)
        if selected_text is not None:
            break

    if selected_text is None:
        manifest["status"] = "error"
        (sound_dir / "sounding_ERROR.txt").write_text(
            "No valid sounding found from configured source/cycles. See sounding_manifest.json for attempts and source previews.\n",
            encoding="utf-8",
        )
        (sound_dir / "sounding_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return

    raw_path = sound_dir / f"{cfg.get('station_name', 'sounding')}_{selected_cycle.strftime('%Y%m%d_%HZ')}.txt"
    raw_path.write_text(selected_text, encoding="utf-8", errors="replace")

    indices = _parse_indices(selected_text)
    indices["precipitable_water_in"] = _mm_to_inches(indices.get("precipitable_water_mm"))

    summary = {
        "status": "ok",
        "station_name": cfg.get("station_name"),
        "station_wmo": cfg.get("station_wmo"),
        "station_id_used": selected_station_id,
        "cycle_utc": selected_cycle.strftime("%Y-%m-%d %HZ"),
        "source_url": selected_url,
        "raw_text_path": f"soundings/{raw_path.name}",
        "indices": indices,
        "notes": [
            "Parsed values are conservative regex extractions from sounding text.",
            "Missing/null fields mean the field was not clearly present in the source text.",
            "Human forecaster should still inspect full sounding/skew-T for vertical structure, capping, lapse rates, and storm-mode details.",
        ],
    }

    manifest["status"] = "ok"
    manifest["selected"] = summary

    (sound_dir / "sounding_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    md = []
    md.append("# Upper-Air Sounding Summary")
    md.append("")
    md.append(f"Station: {summary['station_name']} / {summary['station_wmo']}")
    md.append(f"Station ID used: {summary['station_id_used']}")
    md.append(f"Cycle: {summary['cycle_utc']}")
    md.append(f"Source: {summary['source_url']}")
    md.append("")
    md.append("## Parsed ingredient values")
    md.append("")
    for key, value in indices.items():
        md.append(f"- {key}: {value}")
    md.append("")
    md.append("## Notes")
    md.append("")
    for note in summary["notes"]:
        md.append(f"- {note}")
    md.append("")
    md.append("## Raw sounding excerpt")
    md.append("")
    md.append("```text")
    md.append(selected_text[:12000])
    if len(selected_text) > 12000:
        md.append("\n[truncated]")
    md.append("```")
    md.append("")

    (sound_dir / "sounding_summary.md").write_text("\n".join(md), encoding="utf-8")
    (sound_dir / "sounding_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
