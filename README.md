# LIX AFD Assistant

Starter repo for collecting observed/model/weather-context inputs and packaging them for an AI-assisted **draft** Area Forecast Discussion for WFO New Orleans/Baton Rouge.

This is a forecaster helper, not an automated product generator. The goal is to build a repeatable data package containing:

- latest surface observations
- recent NWS text products
- active alerts
- SPC/WPC/NHC context links or screenshots
- model/source placeholders ready for expansion
- a structured `manifest.json`
- a structured `ai_context.md`
- an AFD drafting prompt

The AI output should always be reviewed and edited by a human forecaster before operational use.

## Repo layout

```text
.github/workflows/afd_collection.yml   GitHub Actions scheduled/manual run
config/config.yaml                     LIX-specific config
prompts/afd_prompt.md                  reusable AFD drafting prompt
scripts/run_pipeline.py                main pipeline runner
scripts/collect_observed.py            METAR/latest obs collection from api.weather.gov
scripts/collect_text_products.py       previous AFD/HWO/alerts collection
scripts/collect_screenshots.py         Playwright screenshot collector
scripts/package_ai_context.py          builds manifest.json and ai_context.md
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

## Philosophy

1. **Structured data first.** JSON/text is better than screenshots when the AI needs to reason.
2. **Screenshots second.** Use images for context that is hard to get cleanly another way.
3. **AI package last.** The useful part is `ai_context.md` + `manifest.json`, not a random pile of weather PNGs.
4. **Human review always.** The draft is a starting point, not operational truth.

## Next improvements

- Add NOAA/NOMADS model field downloading/subsetting.
- Add HRRR/RAP/NBM/HREF summary extraction.
- Add sounding text/BUFKIT-style summaries.
- Add optional OpenAI/Gemini API draft generation step.
- Add simple HTML dashboard for latest package review.
