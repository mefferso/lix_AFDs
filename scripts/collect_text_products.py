from __future__ import annotations

import json
from pathlib import Path

from http_helpers import get_json


def _fetch_latest_product(base_url: str, user_agent: str, product_type: str, location: str) -> dict:
    list_url = f"{base_url}/products/types/{product_type}/locations/{location}"
    listing = get_json(list_url, user_agent=user_agent)
    products = listing.get("@graph", [])
    if not products:
        return {"error": f"No {product_type} products found for {location}"}

    latest = products[0]
    product_url = latest.get("@id")
    if not product_url:
        return {"error": f"No @id found for latest {product_type} product", "latest": latest}

    detail = get_json(product_url, user_agent=user_agent)
    return detail


def collect_text_products(outdir: Path, config: dict) -> None:
    product_dir = outdir / "text_products"
    product_dir.mkdir(exist_ok=True)

    base_url = config["nws_api"]["base_url"].rstrip("/")
    user_agent = config["nws_api"]["user_agent"]

    product_results = {}

    for name, item in config.get("text_products", {}).items():
        try:
            detail = _fetch_latest_product(
                base_url=base_url,
                user_agent=user_agent,
                product_type=item["type"],
                location=item["location"],
            )
            product_results[name] = {
                "id": detail.get("id"),
                "type": detail.get("productCode"),
                "location": detail.get("issuingOffice"),
                "issueTime": detail.get("issuanceTime"),
                "path": f"text_products/{name}.txt",
            }
            with open(product_dir / f"{name}.json", "w", encoding="utf-8") as f:
                json.dump(detail, f, indent=2)
            with open(product_dir / f"{name}.txt", "w", encoding="utf-8") as f:
                f.write(detail.get("productText", ""))
        except Exception as e:
            product_results[name] = {"error": str(e)}
            with open(product_dir / f"{name}_ERROR.txt", "w", encoding="utf-8") as f:
                f.write(str(e))

    alert_results = {}
    for area in config.get("alerts", {}).get("areas", []):
        url = f"{base_url}/alerts/active?area={area}"
        try:
            data = get_json(url, user_agent=user_agent)
            alert_results[area] = {
                "count": len(data.get("features", [])),
                "path": f"text_products/active_alerts_{area}.json",
            }
            with open(product_dir / f"active_alerts_{area}.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            alert_results[area] = {"error": str(e)}

    with open(product_dir / "text_product_manifest.json", "w", encoding="utf-8") as f:
        json.dump({"products": product_results, "alerts": alert_results}, f, indent=2)
