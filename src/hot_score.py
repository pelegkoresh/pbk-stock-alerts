"""
hot_score.py
============
Scores each commodity 0-100 based on 4 criteria:
1. Institutional volume (30%)
2. Live price movement + volume (25%)
3. Supply deficit signals (25%)
4. Institutional consistency / recurring buys (20%)
"""
import time
from datetime import datetime
from .commodities_live import fetch_commodity_live, COMMODITY_SYMBOLS
from .commodities_data import SEASONAL_MOVES, MONTHS_HE
from .sec_edgar import get_recent_13f_filings, get_holdings_from_filing, KNOWN_INSTITUTIONS
from .institutional_overlay import COMMODITY_INSTITUTION_MAP

# ── Supply deficit catalog ────────────────────────────────
# Updated manually / can be extended with news feed later
SUPPLY_SIGNALS = {
    "crude_oil": [
        {"signal": "OPEC+ קיצוץ ייצור של 1.66 מיליון חביות/יום", "severity": 9, "country": "סעודיה + רוסיה"},
        {"signal": "מלאי ארה\"ב נמוך מהממוצע העונתי", "severity": 7, "country": "ארה\"ב"},
        {"signal": "מתיחות גיאופוליטית במפרץ הפרסי", "severity": 6, "country": "איראן / עיראק"},
    ],
    "natural_gas": [
        {"signal": "מאגרי אירופה ב-60% מהתפוקה לאחר מלחמת אוקראינה", "severity": 8, "country": "אירופה"},
        {"signal": "ביקוש LNG בסין עולה +18% שנה-על-שנה", "severity": 7, "country": "סין"},
    ],
    "coffee": [
        {"signal": "בצורת קשה בדרום ברזיל — יבול 2025 נמוך ב-12%", "severity": 9, "country": "ברזיל"},
        {"signal": "El Niño פוגע בוייטנאם — יבול רובוסטה נמוך", "severity": 7, "country": "וייטנאם"},
    ],
    "corn": [
        {"signal": "בצורת במערב ארה\"ב — Iowa ו-Illinois", "severity": 6, "country": "ארה\"ב"},
        {"signal": "מלחמה באוקראינה מפריעה לייצוא", "severity": 8, "country": "אוקראינה"},
    ],
    "soybeans": [
        {"signal": "La Niña גורמת לעודף גשמים בברזיל — עיכוב קציר", "severity": 6, "country": "ברזיל"},
        {"signal": "סין הגדילה רכישות — ביקוש שיא", "severity": 8, "country": "סין"},
    ],
    "gold": [
        {"signal": "רכישות בנקים מרכזיים בשיא של 55 שנה", "severity": 9, "country": "גלובלי"},
        {"signal": "ריבית FED יורדת — זהב מתחזק", "severity": 8, "country": "ארה\"ב"},
    ],
    "silver": [
        {"signal": "ביקוש תעשייתי — פאנלים סולאריים עולה 30%", "severity": 8, "country": "סין / הודו"},
        {"signal": "מחסור בכרייה — South America פחות תפוקה", "severity": 6, "country": "פרו / מקסיקו"},
    ],
    "wheat": [
        {"signal": "מלחמת רוסיה-אוקראינה מקטינה ייצוא ב-25%", "severity": 9, "country": "אוקראינה"},
        {"signal": "גל חום בהודו פוגע ביבול — הודו אסרה ייצוא", "severity": 7, "country": "הודו"},
    ],
}

def _score_institutional_volume(commodity_key: str, holdings_cache: dict) -> tuple:
    """Score 0-30 based on total institutional $ in related stocks."""
    keywords = COMMODITY_INSTITUTION_MAP.get(commodity_key, {}).get("keywords", [])
    total_val = 0
    institutions_involved = []
    for cik, info in holdings_cache.items():
        for h in info.get("holdings", []):
            name_up = h.get("name", "").upper()
            for kw in keywords:
                if kw in name_up:
                    total_val += h["value_thousands"] / 1000
                    inst = KNOWN_INSTITUTIONS.get(cik, cik)
                    if inst not in institutions_involved:
                        institutions_involved.append(inst)
                    break
    # Scale: >$50B = 30pts, >$20B = 20pts, >$5B = 12pts, >$1B = 6pts
    if total_val > 50000: score = 30
    elif total_val > 20000: score = 22
    elif total_val > 5000: score = 14
    elif total_val > 1000: score = 8
    else: score = 3
    return score, round(total_val, 0), institutions_involved

def _score_live_movement(live_data: dict) -> tuple:
    """Score 0-25 based on % change and volume."""
    pct = abs(live_data.get("change_pct", 0))
    vol = live_data.get("volume", 0)
    if pct > 4:   move_score = 15
    elif pct > 2: move_score = 11
    elif pct > 1: move_score = 7
    elif pct > 0.3: move_score = 4
    else: move_score = 1
    if vol > 500000:  vol_score = 10
    elif vol > 100000: vol_score = 7
    elif vol > 10000:  vol_score = 4
    elif vol > 0:      vol_score = 2
    else: vol_score = 0
    return min(move_score + vol_score, 25), pct, vol

def _score_supply_deficit(commodity_key: str) -> tuple:
    """Score 0-25 based on supply deficit signals."""
    signals = SUPPLY_SIGNALS.get(commodity_key, [])
    if not signals: return 0, []
    total_severity = sum(s["severity"] for s in signals)
    score = min(round(total_severity / len(signals) / 10 * 25), 25)
    return score, signals

def _score_seasonal_consistency(commodity_key: str, now_month: int) -> tuple:
    """Score 0-20 based on historical seasonal pattern for current month."""
    seasonal = SEASONAL_MOVES.get(commodity_key, {})
    month_data = seasonal.get("monthly", {}).get(now_month, {})
    hist_move = month_data.get("avg_move", 0)
    is_hot = month_data.get("hot", False)
    reason = month_data.get("reason", "")
    demand = month_data.get("demand", "בינוני")
    if is_hot and hist_move > 3:   score = 20
    elif is_hot and hist_move > 1: score = 15
    elif hist_move > 2:            score = 12
    elif hist_move > 0:            score = 8
    elif hist_move > -2:           score = 4
    else: score = 1
    return score, hist_move, reason, demand

def compute_hot_score(commodity_key: str, holdings_cache: dict, now_month: int) -> dict:
    sym = COMMODITY_SYMBOLS.get(commodity_key, {})
    live = fetch_commodity_live(commodity_key)
    time.sleep(0.12)

    s1, inst_val, inst_list   = _score_institutional_volume(commodity_key, holdings_cache)
    s2, pct_chg, volume       = _score_live_movement(live)
    s3, supply_signals        = _score_supply_deficit(commodity_key)
    s4, hist_move, sea_reason, demand = _score_seasonal_consistency(commodity_key, now_month)

    total = s1 + s2 + s3 + s4

    # Direction signal
    if live.get("change_pct", 0) > 0 and hist_move > 0:
        direction = "BULLISH"
    elif live.get("change_pct", 0) < 0 and hist_move < 0:
        direction = "BEARISH"
    else:
        direction = "MIXED"

    return {
        "key": commodity_key,
        "name": sym.get("name", commodity_key),
        "emoji": sym.get("emoji", "📦"),
        "total_score": total,
        "score_institutional": s1,
        "score_live": s2,
        "score_supply": s3,
        "score_seasonal": s4,
        "inst_value_m": inst_val,
        "inst_list": inst_list,
        "live_pct": live.get("change_pct", 0),
        "live_price": live.get("price", 0),
        "live_volume": volume,
        "supply_signals": supply_signals,
        "hist_move": hist_move,
        "seasonal_reason": sea_reason,
        "demand": demand,
        "direction": direction,
        "month_name": MONTHS_HE.get(now_month, ""),
    }

def rank_all_commodities(holdings_cache: dict) -> list:
    now_month = datetime.now().month
    results = []
    for key in COMMODITY_SYMBOLS:
        score_data = compute_hot_score(key, holdings_cache, now_month)
        results.append(score_data)
        time.sleep(0.1)
    results.sort(key=lambda x: x["total_score"], reverse=True)
    for i, r in enumerate(results):
        r["rank"] = i + 1
    return results
