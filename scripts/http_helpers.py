from __future__ import annotations

import requests


def get_json(url: str, user_agent: str, timeout: int = 30) -> dict:
    headers = {
        "User-Agent": user_agent,
        "Accept": "application/geo+json, application/json, text/plain",
    }
    r = requests.get(url, headers=headers, timeout=timeout)
    r.raise_for_status()
    return r.json()


def get_text(url: str, user_agent: str, timeout: int = 30) -> str:
    headers = {
        "User-Agent": user_agent,
        "Accept": "text/plain, application/json",
    }
    r = requests.get(url, headers=headers, timeout=timeout)
    r.raise_for_status()
    return r.text
