from __future__ import annotations

import json
from pathlib import Path

from http_helpers import get_json


def _safe_value(feature: dict, key: str):
    value = feature.get("properties", {}).get(key)
    if isinstance(value, dict):
        return value.get("value")
    return value


def _summarize_latest_ob(feature: dict) -> dict:
    props = feature.get("properties", {})
    return {
        "station": props.get("station", "").split("/")[-1],
        "timestamp": props.get("timestamp"),
        "textDescription": props.get("textDescription"),
        "temperature_C": _safe_value(feature, "temperature"),
        "dewpoint_C": _safe_value(feature, "dewpoint"),
        "windDirection_deg": _safe_value(feature, "windDirection"),
        "windSpeed_mps": _safe_value(feature, "windSpeed"),
        "windGust_mps": _safe_value(feature, "windGust"),
        "barometricPressure_Pa": _safe_value(feature, "barometricPressure"),
        "seaLevelPressure_Pa": _safe_value(feature, "seaLevelPressure"),
        "visibility_m": _safe_value(feature, "visibility"),
        "rawMessage": props.get("rawMessage"),
    }


def collect_observed_package(outdir: Path, config: dict) -> None:
    obs_dir = outdir / "observations"
    obs_dir.mkdir(exist_ok=True)

    base_url = config["nws_api"]["base_url"].rstrip("/")
    user_agent = config["nws_api"]["user_agent"]
    stations = config["observations"]["stations"]

    summaries = []
    errors = []

    for station in stations:
        url = f"{base_url}/stations/{station}/observations/latest"
        try:
            data = get_json(url, user_agent=user_agent)
            with open(obs_dir / f"{station}_latest.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            summaries.append(_summarize_latest_ob(data))
        except Exception as e:
            errors.append({"station": station, "error": str(e)})

    with open(obs_dir / "latest_surface_obs_summary.json", "w", encoding="utf-8") as f:
        json.dump({"stations": summaries, "errors": errors}, f, indent=2)
