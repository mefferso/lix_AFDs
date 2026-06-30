from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path


def collect_current_trends_context(outdir: Path, config: dict) -> None:
    trends_dir = outdir / "current_trends_context"
    trends_dir.mkdir(exist_ok=True)

    now_utc = datetime.now(timezone.utc).isoformat()

    lines = []
    lines.append("# Current Trends Notes Template")
    lines.append("")
    lines.append(f"Created UTC: {now_utc}")
    lines.append("")
    lines.append("Fill this out when live observational trends matter. Paste it into ChatGPT with ai_context.md and any images you want reviewed.")
    lines.append("")
    lines.append("## One-line summary")
    lines.append("")
    lines.append("- Current story:")
    lines.append("- Main concern:")
    lines.append("- Confidence:")
    lines.append("")
    lines.append("## Live imagery / observations")
    lines.append("")
    lines.append("- Where activity is located:")
    lines.append("- How it is moving:")
    lines.append("- Where new activity may form:")
    lines.append("- Boundaries or local focus areas:")
    lines.append("- Areas of repeated activity:")
    lines.append("- Short-term trend for next 1 to 3 hours:")
    lines.append("")
    lines.append("## Cloud and heating trends")
    lines.append("")
    lines.append("- Clearing/cloud cover trend:")
    lines.append("- Differential heating signal:")
    lines.append("- Growing cumulus/tower trend:")
    lines.append("- Cloud-top trend:")
    lines.append("- Low cloud/fog/stratus concern:")
    lines.append("")
    lines.append("## Local impacts")
    lines.append("")
    lines.append("- Heavy rain/flooding concern:")
    lines.append("- Strong storm concern:")
    lines.append("- Heat impact from cloud/timing:")
    lines.append("- Marine impact:")
    lines.append("- Aviation impact:")
    lines.append("")
    lines.append("## AFD wording notes")
    lines.append("")
    lines.append("- What needs to be updated from previous AFD:")
    lines.append("- Timing/location wording to use:")
    lines.append("- Uncertainty wording:")
    lines.append("- Avoid saying:")
    lines.append("")

    (trends_dir / "current_trends_notes_template.md").write_text("\n".join(lines), encoding="utf-8")
