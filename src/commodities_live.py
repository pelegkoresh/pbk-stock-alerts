import requests
import time
from datetime import datetime

from .secrets_loader import TWELVE_KEY

# Commodity symbols for Twelve Data and Yahoo Finance
COMMODITY_SYMBOLS = {
    "crude_oil":    {"twelve": "WTI/USD",  "yahoo": "CL=F",  "name": "נפט גולמי",  "emoji": "🛢️"},
    "natural_gas":  {"twelve": "NGAS/USD", "yahoo": "NG=F",  "name": "גז טבעי",    "emoji": "🔥"},
    "coffee":       {"twelve": "COFFEE",   "yahoo": "KC=F",  "name": "קפה",         "emoji": "☕"},
    "corn":         {"twelve": "CORN",     "yahoo": "ZC=F",  "name": "תירס",        "emoji": "🌽"},
    "soybeans":     {"twelve": "SOYBEAN",  "yahoo": "ZS=F",  "name": "סויה",        "emoji": "🫘"},
    "gold":         {"twelve": "XAU/USD",  "yahoo": "GC=F",  "name": "זהב",         "emoji": "🥇"},
    "silver":       {"twelve": "XAG/USD",  "yahoo": "SI=F",  "name": "כסף",         "emoji": "🥈"},
    "wheat":        {"twelve": "WHEAT",    "yahoo": "ZW=F",  "name": "חיטה",        "emoji": "🌾"},
}

def _fetch_twelve(symbol: str) -> dict:
    try:
        url = "https://api.twelvedata.com/quote"
        r = requests.get(url, params={"symbol": symbol, "apikey": TWELVE_KEY}, timeout=8)
        d = r.json()
        if d.get("status") == "error" or "code" in d:
            return {}
        return {
            "price":       float(d.get("close") or d.get("previous_close") or 0),
            "open":        float(d.get("open") or 0),
            "high":        float(d.get("high") or 0),
            "low":         float(d.get("low") or 0),
            "change_pct":  float(d.get("percent_change") or 0),
            "volume":      int(float(d.get("volume") or 0)),
            "source":      "Twelve Data",
        }
    except Exception:
        return {}

def _fetch_yahoo(ticker: str) -> dict:
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, params={"interval": "1d", "range": "2d"}, timeout=8)
        data = r.json()
        meta = data["chart"]["result"][0]["meta"]
        price      = float(meta.get("regularMarketPrice") or meta.get("previousClose") or 0)
        prev_close = float(meta.get("previousClose") or meta.get("chartPreviousClose") or price)
        volume     = int(meta.get("regularMarketVolume") or 0)
        change_pct = ((price - prev_close) / prev_close * 100) if prev_close else 0
        indicators = data["chart"]["result"][0].get("indicators", {}).get("quote", [{}])[0]
        highs = [x for x in (indicators.get("high") or []) if x]
        lows  = [x for x in (indicators.get("low")  or []) if x]
        opens = [x for x in (indicators.get("open") or []) if x]
        return {
            "price":      round(price, 4),
            "open":       round(opens[-1], 4)  if opens  else 0,
            "high":       round(highs[-1], 4)  if highs  else 0,
            "low":        round(lows[-1], 4)   if lows   else 0,
            "change_pct": round(change_pct, 2),
            "volume":     volume,
            "source":     "Yahoo Finance",
        }
    except Exception:
        return {}

def fetch_commodity_live(key: str) -> dict:
    sym = COMMODITY_SYMBOLS.get(key, {})
    if not sym:
        return {"error": "לא נמצא"}

    data = _fetch_twelve(sym["twelve"])
    if not data or data.get("price", 0) == 0:
        time.sleep(0.1)
        data = _fetch_yahoo(sym["yahoo"])

    if not data or data.get("price", 0) == 0:
        return {
            "key": key, "name": sym["name"], "emoji": sym["emoji"],
            "price": 0, "change_pct": 0, "volume": 0,
            "open": 0, "high": 0, "low": 0,
            "source": "N/A", "error": "לא זמין"
        }

    return {
        "key":        key,
        "name":       sym["name"],
        "emoji":      sym["emoji"],
        "price":      data["price"],
        "change_pct": data["change_pct"],
        "volume":     data["volume"],
        "open":       data["open"],
        "high":       data["high"],
        "low":        data["low"],
        "source":     data["source"],
        "error":      None,
    }

def fetch_all_commodities_live() -> list:
    results = []
    for key in COMMODITY_SYMBOLS:
        results.append(fetch_commodity_live(key))
        time.sleep(0.15)
    results.sort(key=lambda x: abs(x.get("change_pct", 0)), reverse=True)
    return results
