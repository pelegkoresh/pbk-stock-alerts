import requests
import time
from datetime import datetime

from .secrets_loader import TWELVE_KEY

# Top 50 commodities - dynamic list covering all major categories
# Yahoo Finance futures tickers
TOP_COMMODITIES = [
    # Energy
    {"key": "crude_oil",    "yahoo": "CL=F",  "twelve": "WTI/USD",   "name": "נפט גולמי WTI",    "emoji": "🛢️",  "category": "אנרגיה"},
    {"key": "brent_oil",    "yahoo": "BZ=F",  "twelve": "BRENTOIL",  "name": "נפט ברנט",           "emoji": "🛢️",  "category": "אנרגיה"},
    {"key": "natural_gas",  "yahoo": "NG=F",  "twelve": "NGAS/USD",  "name": "גז טבעי",            "emoji": "🔥",  "category": "אנרגיה"},
    {"key": "gasoline",     "yahoo": "RB=F",  "twelve": "GASOLINE",  "name": "בנזין",              "emoji": "⛽",  "category": "אנרגיה"},
    {"key": "heating_oil",  "yahoo": "HO=F",  "twelve": "HEATINGOIL","name": "שמן חימום",          "emoji": "🔥",  "category": "אנרגיה"},
    # Metals
    {"key": "gold",         "yahoo": "GC=F",  "twelve": "XAU/USD",   "name": "זהב",                "emoji": "🥇",  "category": "מתכות"},
    {"key": "silver",       "yahoo": "SI=F",  "twelve": "XAG/USD",   "name": "כסף",                "emoji": "🥈",  "category": "מתכות"},
    {"key": "copper",       "yahoo": "HG=F",  "twelve": "COPPER",    "name": "נחושת",              "emoji": "🔩",  "category": "מתכות"},
    {"key": "platinum",     "yahoo": "PL=F",  "twelve": "XPT/USD",   "name": "פלטינום",            "emoji": "⚪",  "category": "מתכות"},
    {"key": "palladium",    "yahoo": "PA=F",  "twelve": "XPD/USD",   "name": "פלדיום",             "emoji": "⬜",  "category": "מתכות"},
    {"key": "aluminum",     "yahoo": "ALI=F", "twelve": "ALUMINUM",  "name": "אלומיניום",          "emoji": "🔲",  "category": "מתכות"},
    # Grains
    {"key": "corn",         "yahoo": "ZC=F",  "twelve": "CORN",      "name": "תירס",               "emoji": "🌽",  "category": "חקלאות"},
    {"key": "soybeans",     "yahoo": "ZS=F",  "twelve": "SOYBEAN",   "name": "סויה",               "emoji": "🫘",  "category": "חקלאות"},
    {"key": "wheat",        "yahoo": "ZW=F",  "twelve": "WHEAT",     "name": "חיטה",               "emoji": "🌾",  "category": "חקלאות"},
    {"key": "rice",         "yahoo": "ZR=F",  "twelve": "RICE",      "name": "אורז",               "emoji": "🍚",  "category": "חקלאות"},
    {"key": "oats",         "yahoo": "ZO=F",  "twelve": "OATS",      "name": "שיבולת שועל",        "emoji": "🌿",  "category": "חקלאות"},
    {"key": "soybean_oil",  "yahoo": "ZL=F",  "twelve": "SOYBEANOI", "name": "שמן סויה",           "emoji": "🫙",  "category": "חקלאות"},
    {"key": "soybean_meal", "yahoo": "ZM=F",  "twelve": "SOYBEAMEAL","name": "קמח סויה",           "emoji": "🌿",  "category": "חקלאות"},
    # Soft commodities
    {"key": "coffee",       "yahoo": "KC=F",  "twelve": "COFFEE",    "name": "קפה",                "emoji": "☕",  "category": "רכים"},
    {"key": "sugar",        "yahoo": "SB=F",  "twelve": "SUGAR",     "name": "סוכר",               "emoji": "🍬",  "category": "רכים"},
    {"key": "cocoa",        "yahoo": "CC=F",  "twelve": "COCOA",     "name": "קקאו",               "emoji": "🍫",  "category": "רכים"},
    {"key": "cotton",       "yahoo": "CT=F",  "twelve": "COTTON",    "name": "כותנה",              "emoji": "🌸",  "category": "רכים"},
    {"key": "orange_juice", "yahoo": "OJ=F",  "twelve": "OJ",        "name": "מיץ תפוזים",         "emoji": "🍊",  "category": "רכים"},
    {"key": "lumber",       "yahoo": "LBS=F", "twelve": "LUMBER",    "name": "עץ",                 "emoji": "🪵",  "category": "רכים"},
    # Livestock
    {"key": "live_cattle",  "yahoo": "LE=F",  "twelve": "CATTLE",    "name": "בקר חי",             "emoji": "🐄",  "category": "בעלי חיים"},
    {"key": "lean_hogs",    "yahoo": "HE=F",  "twelve": "HOGS",      "name": "חזיר רזה",           "emoji": "🐷",  "category": "בעלי חיים"},
    {"key": "feeder_cattle","yahoo": "GF=F",  "twelve": "FEEDCATTLE","name": "בקר מוזן",           "emoji": "🐮",  "category": "בעלי חיים"},
]

def _fetch_yahoo(ticker: str) -> dict:
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"},
                         params={"interval": "1d", "range": "2d"}, timeout=8)
        data = r.json()
        meta = data["chart"]["result"][0]["meta"]
        price      = float(meta.get("regularMarketPrice") or meta.get("previousClose") or 0)
        prev_close = float(meta.get("previousClose") or meta.get("chartPreviousClose") or price)
        volume     = int(meta.get("regularMarketVolume") or 0)
        change_pct = ((price - prev_close) / prev_close * 100) if prev_close else 0
        return {
            "price":      round(price, 4),
            "change_pct": round(change_pct, 2),
            "volume":     volume,
            "source":     "Yahoo Finance",
        }
    except Exception:
        return {}

def _fetch_twelve(symbol: str) -> dict:
    try:
        r = requests.get("https://api.twelvedata.com/quote",
                         params={"symbol": symbol, "apikey": TWELVE_KEY}, timeout=8)
        d = r.json()
        if d.get("status") == "error" or "code" in d:
            return {}
        return {
            "price":      float(d.get("close") or d.get("previous_close") or 0),
            "change_pct": float(d.get("percent_change") or 0),
            "volume":     int(float(d.get("volume") or 0)),
            "source":     "Twelve Data",
        }
    except Exception:
        return {}

def fetch_commodity(c: dict) -> dict:
    data = _fetch_twelve(c["twelve"])
    if not data or data.get("price", 0) == 0:
        time.sleep(0.1)
        data = _fetch_yahoo(c["yahoo"])

    if not data or data.get("price", 0) == 0:
        return {**c, "price": 0, "change_pct": 0, "volume": 0, "source": "N/A", "available": False}

    return {
        **c,
        "price":      data["price"],
        "change_pct": data["change_pct"],
        "volume":     data["volume"],
        "source":     data["source"],
        "available":  True,
    }

def fetch_top_commodities(limit: int = 50) -> list:
    """Fetch all commodities, sort by absolute % change (hottest first)."""
    results = []
    for c in TOP_COMMODITIES[:limit]:
        results.append(fetch_commodity(c))
        time.sleep(0.12)
    # Sort by absolute % change — hottest on top
    results.sort(key=lambda x: abs(x.get("change_pct", 0)), reverse=True)
    return results

def fetch_by_category(category: str) -> list:
    cats = [c for c in TOP_COMMODITIES if c["category"] == category]
    results = [fetch_commodity(c) for c in cats]
    results.sort(key=lambda x: abs(x.get("change_pct", 0)), reverse=True)
    return results

CATEGORIES = list(dict.fromkeys(c["category"] for c in TOP_COMMODITIES))
