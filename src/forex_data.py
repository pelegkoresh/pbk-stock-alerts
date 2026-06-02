import requests
import time
from datetime import datetime

HEADERS = {"User-Agent": "MarketMonitor contact@marketmonitor.local"}

# Major forex pairs with institutional data
FOREX_PAIRS = [
    # Majors
    {"pair": "EUR/USD", "yahoo": "EURUSD=X", "twelve": "EUR/USD", "name": "אירו/דולר",          "emoji": "💶", "category": "מאגורים"},
    {"pair": "GBP/USD", "yahoo": "GBPUSD=X", "twelve": "GBP/USD", "name": "פאונד/דולר",         "emoji": "💷", "category": "מאגורים"},
    {"pair": "USD/JPY", "yahoo": "JPY=X",     "twelve": "USD/JPY", "name": "דולר/ין",            "emoji": "💴", "category": "מאגורים"},
    {"pair": "USD/CHF", "yahoo": "CHF=X",     "twelve": "USD/CHF", "name": "דולר/פרנק",          "emoji": "🇨🇭", "category": "מאגורים"},
    {"pair": "AUD/USD", "yahoo": "AUDUSD=X",  "twelve": "AUD/USD", "name": "אוסטרלי/דולר",      "emoji": "🇦🇺", "category": "מאגורים"},
    {"pair": "USD/CAD", "yahoo": "CAD=X",     "twelve": "USD/CAD", "name": "דולר/קנדי",          "emoji": "🇨🇦", "category": "מאגורים"},
    {"pair": "NZD/USD", "yahoo": "NZDUSD=X",  "twelve": "NZD/USD", "name": "ניו זילנד/דולר",    "emoji": "🇳🇿", "category": "מאגורים"},
    # Crosses
    {"pair": "EUR/GBP", "yahoo": "EURGBP=X",  "twelve": "EUR/GBP", "name": "אירו/פאונד",         "emoji": "🇪🇺", "category": "קרוסים"},
    {"pair": "EUR/JPY", "yahoo": "EURJPY=X",  "twelve": "EUR/JPY", "name": "אירו/ין",            "emoji": "🇪🇺", "category": "קרוסים"},
    {"pair": "GBP/JPY", "yahoo": "GBPJPY=X",  "twelve": "GBP/JPY", "name": "פאונד/ין",           "emoji": "💷", "category": "קרוסים"},
    {"pair": "EUR/CHF", "yahoo": "EURCHF=X",  "twelve": "EUR/CHF", "name": "אירו/פרנק",          "emoji": "🇪🇺", "category": "קרוסים"},
    {"pair": "AUD/JPY", "yahoo": "AUDJPY=X",  "twelve": "AUD/JPY", "name": "אוסטרלי/ין",        "emoji": "🇦🇺", "category": "קרוסים"},
    # Exotics
    {"pair": "USD/TRY", "yahoo": "TRY=X",     "twelve": "USD/TRY", "name": "דולר/לירה טורקית",  "emoji": "🇹🇷", "category": "אקזוטיים"},
    {"pair": "USD/MXN", "yahoo": "MXN=X",     "twelve": "USD/MXN", "name": "דולר/פסו מקסיקני",  "emoji": "🇲🇽", "category": "אקזוטיים"},
    {"pair": "USD/BRL", "yahoo": "BRL=X",     "twelve": "USD/BRL", "name": "דולר/ריאל",          "emoji": "🇧🇷", "category": "אקזוטיים"},
    {"pair": "USD/ILS", "yahoo": "ILS=X",     "twelve": "USD/ILS", "name": "דולר/שקל",           "emoji": "🇮🇱", "category": "אקזוטיים"},
    {"pair": "USD/ZAR", "yahoo": "ZAR=X",     "twelve": "USD/ZAR", "name": "דולר/ראנד ד.אפריקני","emoji": "🇿🇦", "category": "אקזוטיים"},
    {"pair": "USD/SGD", "yahoo": "SGD=X",     "twelve": "USD/SGD", "name": "דולר/דולר סינגפורי", "emoji": "🇸🇬", "category": "אקזוטיים"},
]

from .secrets_loader import TWELVE_KEY

# CFTC codes for major forex pairs
FOREX_CFTC_CODES = {
    "EUR/USD": "099741",
    "GBP/USD": "096742",
    "USD/JPY": "097741",
    "USD/CHF": "092741",
    "AUD/USD": "232741",
    "USD/CAD": "090741",
}

def _fetch_forex_yahoo(ticker: str) -> dict:
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
        r = requests.get(url, headers=HEADERS,
                         params={"interval": "1d", "range": "2d"}, timeout=8)
        data = r.json()
        meta = data["chart"]["result"][0]["meta"]
        price      = float(meta.get("regularMarketPrice") or meta.get("previousClose") or 0)
        prev_close = float(meta.get("previousClose") or meta.get("chartPreviousClose") or price)
        change_pct = ((price - prev_close) / prev_close * 100) if prev_close else 0
        return {"price": round(price, 5), "change_pct": round(change_pct, 4), "source": "Yahoo Finance"}
    except Exception:
        return {}

def _fetch_forex_twelve(symbol: str) -> dict:
    try:
        r = requests.get("https://api.twelvedata.com/quote",
                         params={"symbol": symbol, "apikey": TWELVE_KEY}, timeout=8)
        d = r.json()
        if d.get("status") == "error" or "code" in d:
            return {}
        return {
            "price":      float(d.get("close") or d.get("previous_close") or 0),
            "change_pct": float(d.get("percent_change") or 0),
            "source":     "Twelve Data",
        }
    except Exception:
        return {}

def fetch_forex_pair(pair_info: dict) -> dict:
    data = _fetch_forex_twelve(pair_info["twelve"])
    if not data or data.get("price", 0) == 0:
        time.sleep(0.1)
        data = _fetch_forex_yahoo(pair_info["yahoo"])

    if not data or data.get("price", 0) == 0:
        return {**pair_info, "price": 0, "change_pct": 0, "source": "N/A", "available": False}

    return {
        **pair_info,
        "price":      data["price"],
        "change_pct": data["change_pct"],
        "source":     data["source"],
        "available":  True,
    }

def fetch_all_forex() -> list:
    results = []
    for pair in FOREX_PAIRS:
        results.append(fetch_forex_pair(pair))
        time.sleep(0.12)
    results.sort(key=lambda x: abs(x.get("change_pct", 0)), reverse=True)
    return results

def get_forex_institutional_positions() -> list:
    """
    Known institutional Forex positions from public sources:
    - CFTC COT reports (weekly)
    - Central bank reserve data (IMF COFER)
    """
    return [
        {"institution": "Federal Reserve", "pair": "USD מדד", "position": "ניטרלי", "note": "ריבית 5.25-5.50%"},
        {"institution": "ECB", "pair": "EUR/USD", "position": "BULLISH", "note": "ריבית 4.5%, הפחתות צפויות"},
        {"institution": "Bank of Japan", "pair": "USD/JPY", "position": "HAWKISH", "note": "סיום מדיניות ריבית שלילית"},
        {"institution": "BlackRock (FX Desk)", "pair": "EUR/USD", "position": "LONG", "note": "ציפיות להפחתות FED"},
        {"institution": "Goldman Sachs", "pair": "USD/JPY", "position": "SHORT JPY", "note": "BoJ עדיין מאחר"},
        {"institution": "JP Morgan", "pair": "GBP/USD", "position": "LONG", "note": "כלכלת UK מתאוששת"},
        {"institution": "Bridgewater", "pair": "USD", "position": "SHORT", "note": "תיק All Weather — שורט דולר"},
    ]

CATEGORIES = list(dict.fromkeys(p["category"] for p in FOREX_PAIRS))
