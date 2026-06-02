import requests
import csv
import io
import time
from datetime import datetime

# CFTC Commitments of Traders - free weekly report
# Shows NET positions of Commercial (hedgers) vs Non-Commercial (speculators/funds)
CFTC_URL = "https://www.cftc.gov/dcom/styles/commitment_of_traders/deafult/files/dcom/files/newcot.txt"
CFTC_FUTURES_URL = "https://www.cftc.gov/sites/default/files/files/dcom/dea/cotarchives/2024/futures/deacot2024.zip"
CFTC_CURRENT_URL = "https://www.cftc.gov/dcom/styles/commitment_of_traders/deafult/files/dcom/files/newcot.txt"

# Better: use the CFTC legacy format CSV which is always current
CFTC_LEGACY_URL = "https://www.cftc.gov/dcom/styles/commitment_of_traders/deafult/files/dcom/files/newcot.txt"

# Most reliable CFTC endpoint
CFTC_API = "https://publicreporting.cftc.gov/api/explore/dataset/com-disaggregated-fut-only-reports/records/"

COMMODITY_CODES = {
    "CRUDE OIL":     {"code": "067651", "name": "נפט גולמי",   "emoji": "🛢️"},
    "NATURAL GAS":   {"code": "023651", "name": "גז טבעי",     "emoji": "🔥"},
    "GOLD":          {"code": "088691", "name": "זהב",          "emoji": "🥇"},
    "SILVER":        {"code": "084691", "name": "כסף",          "emoji": "🥈"},
    "CORN":          {"code": "002602", "name": "תירס",         "emoji": "🌽"},
    "SOYBEANS":      {"code": "005602", "name": "סויה",         "emoji": "🫘"},
    "WHEAT":         {"code": "001602", "name": "חיטה",         "emoji": "🌾"},
    "COFFEE":        {"code": "083731", "name": "קפה",          "emoji": "☕"},
    "COPPER":        {"code": "085692", "name": "נחושת",        "emoji": "🔩"},
    "EURO":          {"code": "099741", "name": "EUR/USD",      "emoji": "💶"},
    "JAPANESE YEN":  {"code": "097741", "name": "JPY/USD",      "emoji": "💴"},
    "BITCOIN":       {"code": "133741", "name": "Bitcoin",      "emoji": "₿"},
}

def fetch_cftc_positions(commodity_code: str) -> dict:
    """Fetch latest COT report for a commodity from CFTC open data portal."""
    try:
        params = {
            "where": f"cftc_contract_market_code='{commodity_code}'",
            "order_by": "report_date_as_yyyy_mm_dd DESC",
            "limit": 2,
            "timezone": "UTC",
        }
        r = requests.get(CFTC_API, params=params, timeout=12)
        r.raise_for_status()
        data = r.json()
        results = data.get("results", [])
        if not results:
            return {}

        latest = results[0]
        prev   = results[1] if len(results) > 1 else {}

        noncom_long  = int(latest.get("noncomm_positions_long_all", 0))
        noncom_short = int(latest.get("noncomm_positions_short_all", 0))
        com_long     = int(latest.get("comm_positions_long_all", 0))
        com_short    = int(latest.get("comm_positions_short_all", 0))
        net_noncom   = noncom_long - noncom_short
        net_com      = com_long - com_short

        prev_net = 0
        if prev:
            prev_net = int(prev.get("noncomm_positions_long_all", 0)) - int(prev.get("noncomm_positions_short_all", 0))

        change_week = net_noncom - prev_net
        sentiment = "BULLISH" if net_noncom > 0 else "BEARISH"

        return {
            "report_date": latest.get("report_date_as_yyyy_mm_dd", ""),
            "noncom_long": noncom_long,
            "noncom_short": noncom_short,
            "net_noncom": net_noncom,
            "net_com": net_com,
            "change_week": change_week,
            "sentiment": sentiment,
            "open_interest": int(latest.get("open_interest_all", 0)),
        }
    except Exception:
        return {}

def fetch_all_cftc() -> list:
    results = []
    for name, info in COMMODITY_CODES.items():
        data = fetch_cftc_positions(info["code"])
        results.append({
            "name": name,
            "name_he": info["name"],
            "emoji": info["emoji"],
            "code": info["code"],
            **data
        })
        time.sleep(0.3)
    results.sort(key=lambda x: abs(x.get("net_noncom", 0)), reverse=True)
    return results
