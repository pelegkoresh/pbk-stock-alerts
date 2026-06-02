import requests
import time
from typing import Optional

from .secrets_loader import TWELVE_KEY as API_KEY
BASE_URL = "https://api.twelvedata.com"

CUSIP_TO_SYMBOL = {
    "037833100": "AAPL",
    "594918104": "MSFT",
    "023135106": "AMZN",
    "02079K305": "GOOGL",
    "67066G104": "NVDA",
    "025816109": "AXP",
    "191216100": "KO",
    "060505104": "BAC",
    "92826C839": "V",
    "78378X107": "SPY",
    "084670702": "BRK-B",
    "46625H100": "JPM",
    "717081103": "PFE",
    "88160R101": "TSLA",
    "594918104": "MSFT",
    "345370860": "F",
    "369604103": "GE",
    "742718109": "PG",
    "931142103": "WMT",
    "166764100": "CVX",
    "20825C104": "COP",
    "02005N100": "ALLY",
    "38141G104": "GS",
    "172967424": "C",
    "459200101": "IBM",
    "713448108": "PEP",
}

def _clean_name_to_symbol(name: str) -> Optional[str]:
    name_upper = name.upper()
    mappings = {
        "APPLE": "AAPL", "MICROSOFT": "MSFT", "AMAZON": "AMZN",
        "ALPHABET": "GOOGL", "GOOGLE": "GOOGL", "NVIDIA": "NVDA",
        "AMERICAN EXPRESS": "AXP", "COCA COLA": "KO", "COCA-COLA": "KO",
        "BANK OF AMERICA": "BAC", "BANK AMERICA": "BAC", "VISA": "V",
        "JPMORGAN": "JPM", "JP MORGAN": "JPM", "CHEVRON": "CVX",
        "BERKSHIRE": "BRK-B", "GOLDMAN": "GS", "CITIGROUP": "C",
        "PFIZER": "PFE", "TESLA": "TSLA", "WALMART": "WMT",
        "PROCTER": "PG", "PEPSI": "PEP", "CONOCOPHILLIPS": "COP",
        "FORD": "F", "GENERAL ELECTRIC": "GE", "ALLY FINL": "ALLY",
        "OCCIDENTAL": "OXY", "KRAFT HEINZ": "KHC", "DAVITA": "DVA",
        "MOODY": "MCO", "VERISIGN": "VRSN", "CHARTER": "CHTR",
        "AON": "AON", "LOUISIANA": "LPX", "CELANESE": "CE",
    }
    for keyword, symbol in mappings.items():
        if keyword in name_upper:
            return symbol
    return None

def get_symbol(cusip: str, name: str) -> Optional[str]:
    if cusip in CUSIP_TO_SYMBOL:
        return CUSIP_TO_SYMBOL[cusip]
    return _clean_name_to_symbol(name)

def get_price_and_rsi(symbol: str) -> dict:
    try:
        url = f"{BASE_URL}/quote"
        params = {"symbol": symbol, "apikey": API_KEY}
        r = requests.get(url, params=params, timeout=8)
        data = r.json()
        price = float(data.get("close", 0) or data.get("previous_close", 0) or 0)
        change_pct = float(data.get("percent_change", 0) or 0)
    except Exception:
        price, change_pct = 0, 0

    time.sleep(0.15)

    try:
        url2 = f"{BASE_URL}/rsi"
        params2 = {"symbol": symbol, "interval": "1day", "time_period": 14, "apikey": API_KEY}
        r2 = requests.get(url2, params=params2, timeout=8)
        rsi_data = r2.json()
        values = rsi_data.get("values", [])
        rsi = float(values[0]["rsi"]) if values else 0
    except Exception:
        rsi = 0

    signal = ""
    if rsi > 0:
        if rsi < 30:
            signal = "OVERSOLD"
        elif rsi > 70:
            signal = "OVERBOUGHT"
        else:
            signal = "נייטרלי"

    return {
        "symbol": symbol,
        "price": round(price, 2),
        "change_pct": round(change_pct, 2),
        "rsi": round(rsi, 1),
        "signal": signal,
    }

def enrich_holdings(holdings: list, max_enrich: int = 15) -> list:
    enriched = []
    calls = 0
    for h in holdings:
        symbol = get_symbol(h.get("cusip", ""), h.get("name", ""))
        if symbol and calls < max_enrich:
            market = get_price_and_rsi(symbol)
            calls += 2
            time.sleep(0.1)
        else:
            market = {"symbol": symbol or "—", "price": 0, "change_pct": 0, "rsi": 0, "signal": "—"}
        enriched.append({**h, **market})
    return enriched
