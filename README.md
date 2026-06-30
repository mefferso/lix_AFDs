# LIX AFD Assistant

Starter repo for collecting observed/model/weather-context inputs and packaging them for an AI-assisted **draft** Area Forecast Discussion for WFO New Orleans/Baton Rouge.

This is a forecaster helper, not an automated product generator. The goal is to build a repeatable data package containing:

- latest surface observations
- latest AFD
- active alerts
- SPC/WPC/NHC external text/web context
- SPC/WPC/NHC screenshots
- observed upper-air sounding text and parsed ingredient summary when available
- model/source placeholders ready for expansion
- a structured `manifest.json`
- a structured `package_review.md`
- a structured `ai_context.md`
- AFD drafting and package-review prompts

The AI output should always be reviewed and edited by a human forecaster before operational use.

## Repo layout

```text
.github/workflows/afd_collection.yml   GitHub Actions scheduled/manual run
config/config.yaml                     LIX-specific config
prompts/afd_prompt.md                  reusable AFD drafting prompt
prompts/review_package_prompt.md       prompt to critique package quality before drafting
scripts/run_pipeline.py                main pipeline runner
scripts/collect_observed.py            METAR/latest obs collection from api.weather.gov
scripts/collect_text_products.py       latest AFD/alerts collection
scripts/collect_external_sources.py    SPC/WPC/NHC web/text source collector
scripts/collect_soundings.py           upper-air sounding text collector/parser
scripts/collect_screenshots.py         Playwright screenshot collector
scripts/package_ai_context.py          builds manifest, review, and AI context files
output/.gitkeep                        placeholder only; generated files are ignored
requirements.txt                       Python dependencies
.gitignore                             keeps generated junk out of git
```

## How to run locally

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m playwright install chromium
python scripts/run_pipeline.py
```

Generated files go under:

```text
output/latest/YYYYMMDD_HHMMZ/
```

## How to run in GitHub

Go to:

```text
Actions → AFD Data Collection → Run workflow
```

The workflow also has a cron schedule. Cron times are UTC, so adjust them in `.github/workflows/afd_collection.yml` for your shift needs.

## What to inspect after a run

Open the downloaded artifact and check:

```text
package_review.md
ai_context.md
manifest.json
soundings/sounding_summary.md
soundings/sounding_manifest.json
```

Start with `package_review.md`. It is the quick sanity check. Then feed `ai_context.md` to an AI for review or drafting.

## Philosophy

1. **Structured data first.** JSON/text is better than screenshots when the AI needs to reason.
2. **Screenshots second.** Use images for context that is hard to get cleanly another way.
3. **Ingredient summaries matter.** Sounding/model fields should be summarized into meteorological parameters the AI can use safely.
4. **AI package last.** The useful part is `ai_context.md` + `manifest.json`, not a random pile of weather PNGs.
5. **Human review always.** The draft is a starting point, not operational truth.

## Next improvements

- Add NOAA/NOMADS model field downloading/subsetting.
- Add HRRR/RAP/NBM/HREF summary extraction.
- Add model sounding or forecast sounding summaries.
- Add optional OpenAI/Gemini API draft generation step.
- Add simple HTML dashboard for latest package review.
