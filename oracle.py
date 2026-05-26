import os
import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta

CACHE_TTL_SECONDS = 300
_cache = {
    "data": None,
    "expires_at": datetime.min
}

DEFAULT_ORACLE_ENDPOINT = "https://api.exchangerate.host/latest?base=USD&symbols=NGN"


def _fetch_json(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Paylink-Oracle/1.0",
        "Accept": "application/json"
    })
    with urllib.request.urlopen(req, timeout=10) as response:
        payload = response.read().decode("utf-8")
        return json.loads(payload)


def _build_fallback_data():
    return {
        "source": "mock-oracle",
        "timestamp": datetime.utcnow().isoformat() + 'Z',
        "usd_ngn": 745.00,
        "message": "Using fallback oracle data",
        "is_fallback": True
    }


def fetch_oracle_rates():
    global _cache
    now = datetime.utcnow()
    if _cache["data"] and now < _cache["expires_at"]:
        return _cache["data"]

    endpoint = os.environ.get("ORACLE_ENDPOINT", DEFAULT_ORACLE_ENDPOINT)
    result = None

    try:
        payload = _fetch_json(endpoint)
        usd_ngn = None
        if isinstance(payload, dict):
            if "rates" in payload and isinstance(payload["rates"], dict):
                usd_ngn = payload["rates"].get("NGN")
            if usd_ngn is None and "ngn" in payload:
                usd_ngn = float(payload.get("ngn"))
            if usd_ngn is None and "price" in payload:
                usd_ngn = float(payload.get("price"))

        if usd_ngn is not None:
            result = {
                "source": endpoint,
                "timestamp": datetime.utcnow().isoformat() + 'Z',
                "usd_ngn": float(usd_ngn),
                "is_fallback": False
            }
        else:
            result = _build_fallback_data()
    except (urllib.error.URLError, ValueError, json.JSONDecodeError, Exception):
        result = _build_fallback_data()

    _cache["data"] = result
    _cache["expires_at"] = now + timedelta(seconds=CACHE_TTL_SECONDS)
    return result
