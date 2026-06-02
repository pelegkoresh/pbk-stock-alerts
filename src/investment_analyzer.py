import requests
import time
from datetime import datetime

from .secrets_loader import TWELVE_KEY
HEADERS = {"User-Agent": "MarketMonitor contact@marketmonitor.local"}

# ── Signal weights ────────────────────────────────────────
WEIGHTS = {
    "institutional_volume":  20,
    "insider_signal":        20,  # Form 4 — מנהלים קונים/מוכרים
    "rsi_signal":            18,
    "momentum":              18,
    "seasonal":              12,
    "supply_demand":          7,
    "consistency":            5,
}

def _get_rsi(symbol: str) -> float:
    try:
        r = requests.get("https://api.twelvedata.com/rsi",
                         params={"symbol": symbol, "interval": "1day",
                                 "time_period": 14, "apikey": TWELVE_KEY}, timeout=8)
        vals = r.json().get("values", [])
        return float(vals[0]["rsi"]) if vals else 0
    except Exception:
        return 0

def _get_quote(symbol: str) -> dict:
    try:
        r = requests.get("https://api.twelvedata.com/quote",
                         params={"symbol": symbol, "apikey": TWELVE_KEY}, timeout=8)
        d = r.json()
        if "code" in d or d.get("status") == "error":
            return {}
        return {
            "price":      float(d.get("close") or 0),
            "change_pct": float(d.get("percent_change") or 0),
            "high":       float(d.get("high") or 0),
            "low":        float(d.get("low") or 0),
            "volume":     int(float(d.get("volume") or 0)),
        }
    except Exception:
        return {}

def _get_yahoo(ticker: str) -> dict:
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
        r = requests.get(url, headers=HEADERS,
                         params={"interval": "1d", "range": "5d"}, timeout=8)
        data = r.json()
        meta = data["chart"]["result"][0]["meta"]
        price      = float(meta.get("regularMarketPrice") or 0)
        prev_close = float(meta.get("previousClose") or price)
        change_pct = ((price - prev_close) / prev_close * 100) if prev_close else 0
        closes = data["chart"]["result"][0].get("indicators", {}).get("quote", [{}])[0].get("close", [])
        closes = [c for c in closes if c]
        week_change = ((closes[-1] - closes[0]) / closes[0] * 100) if len(closes) >= 2 else 0
        return {
            "price":       round(price, 4),
            "change_pct":  round(change_pct, 2),
            "week_change": round(week_change, 2),
            "volume":      int(meta.get("regularMarketVolume") or 0),
        }
    except Exception:
        return {}

def score_signal(value: float, thresholds: dict) -> tuple:
    """Return (score 0-100, label, color)"""
    for threshold, (score, label, color) in sorted(thresholds.items(), reverse=True):
        if value >= threshold:
            return score, label, color
    return 0, "חלש", "#888"

def analyze_asset(
    name: str,
    asset_type: str,        # "stock" | "commodity" | "crypto" | "forex"
    symbol: str = "",       # Twelve Data symbol
    yahoo_ticker: str = "", # Yahoo Finance ticker
    inst_value_m: float = 0,       # ווליום מוסדי ב-$M
    inst_count: int = 0,           # מספר מוסדות מחזיקים
    inst_consistency_pct: int = 0, # עקביות פעולות חוזרות
    seasonal_score: int = 0,       # ציון עונתיות (0-20)
    supply_score: int = 0,         # ציון גירעון היצע (0-10)
    custom_notes: list = None,     # הערות נוספות
) -> dict:
    """
    Run full investment analysis for any asset.
    Returns scored signals + final recommendation.
    """
    signals = {}
    now = datetime.now().strftime("%d/%m/%Y %H:%M")

    # ── 1. Get market data ────────────────────────────────
    quote = {}
    if symbol:
        quote = _get_quote(symbol)
        time.sleep(0.2)
    if not quote.get("price") and yahoo_ticker:
        quote = _get_yahoo(yahoo_ticker)

    price      = quote.get("price", 0)
    change_pct = quote.get("change_pct", 0)
    week_change = quote.get("week_change", change_pct)
    volume     = quote.get("volume", 0)

    # ── 2. RSI ────────────────────────────────────────────
    rsi = 0
    if symbol:
        rsi = _get_rsi(symbol)
        time.sleep(0.2)

    if rsi > 0:
        if rsi < 25:
            rsi_score, rsi_label, rsi_color = 95, "OVERSOLD חזק — הזדמנות קנייה", "#c0392b"
        elif rsi < 35:
            rsi_score, rsi_label, rsi_color = 75, "OVERSOLD — ביקוש נמוך, פוטנציאל", "#e67e22"
        elif rsi < 55:
            rsi_score, rsi_label, rsi_color = 50, "נייטרלי — אין סיגנל חד", "#2980b9"
        elif rsi < 70:
            rsi_score, rsi_label, rsi_color = 30, "ממוצע-גבוה — שמור זהירות", "#f39c12"
        else:
            rsi_score, rsi_label, rsi_color = 10, "OVERBOUGHT — שקול המתנה", "#27ae60"
    else:
        rsi_score, rsi_label, rsi_color = 50, "RSI לא זמין", "#888"

    signals["rsi"] = {
        "label": "RSI (14 ימים)",
        "value": round(rsi, 1) if rsi else "—",
        "score": rsi_score,
        "signal": rsi_label,
        "color": rsi_color,
        "weight": WEIGHTS["rsi_signal"],
        "weighted_score": round(rsi_score * WEIGHTS["rsi_signal"] / 100, 1),
        "explanation": "RSI מודד האם הנכס נרכש/נמכר יתר על המידה. מתחת 30 = זול היסטורית.",
    }

    # ── 3. Momentum ───────────────────────────────────────
    mom_raw = abs(change_pct) + abs(week_change) * 0.5
    if mom_raw > 5:
        mom_score, mom_label = 90, "מומנטום גבוה מאוד"
        mom_color = "#c0392b" if change_pct > 0 else "#27ae60"
    elif mom_raw > 2:
        mom_score, mom_label = 65, "מומנטום בינוני-גבוה"
        mom_color = "#e67e22"
    elif mom_raw > 0.5:
        mom_score, mom_label = 40, "מומנטום נמוך"
        mom_color = "#2980b9"
    else:
        mom_score, mom_label = 15, "שוק דשדוש"
        mom_color = "#888"

    direction = "BULLISH" if change_pct > 0 else "BEARISH" if change_pct < 0 else "נייטרלי"
    signals["momentum"] = {
        "label": "מומנטום מחיר",
        "value": f"{'+' if change_pct>0 else ''}{change_pct:.2f}% יומי | {'+' if week_change>0 else ''}{week_change:.2f}% שבועי",
        "score": mom_score,
        "signal": f"{mom_label} — {direction}",
        "color": mom_color,
        "weight": WEIGHTS["momentum"],
        "weighted_score": round(mom_score * WEIGHTS["momentum"] / 100, 1),
        "explanation": "תנודתיות גבוהה + כיוון ברור = סיגנל מסחר. שוק דשדוש = המתן.",
    }

    # ── 4. Institutional volume ───────────────────────────
    if inst_value_m > 50000:
        inst_score, inst_label = 95, "ווליום מוסדי עצום — כסף חכם גדול"
        inst_color = "#c0392b"
    elif inst_value_m > 10000:
        inst_score, inst_label = 80, "ווליום מוסדי גבוה"
        inst_color = "#e67e22"
    elif inst_value_m > 1000:
        inst_score, inst_label = 60, "ווליום מוסדי בינוני"
        inst_color = "#f39c12"
    elif inst_value_m > 100:
        inst_score, inst_label = 40, "ווליום מוסדי נמוך"
        inst_color = "#2980b9"
    elif inst_count > 0:
        inst_score, inst_label = 25, f"{inst_count} מוסדות מחזיקים"
        inst_color = "#888"
    else:
        inst_score, inst_label = 10, "אין נתוני מוסדיים"
        inst_color = "#aaa"

    signals["institutional"] = {
        "label": "ווליום מוסדי",
        "value": f"${inst_value_m:,.0f}M | {inst_count} מוסדות",
        "score": inst_score,
        "signal": inst_label,
        "color": inst_color,
        "weight": WEIGHTS["institutional_volume"],
        "weighted_score": round(inst_score * WEIGHTS["institutional_volume"] / 100, 1),
        "explanation": "כשהכסף החכם (Berkshire, BlackRock) נכנס — לעיתים זה לפני מהלך גדול.",
    }

    # ── 5. Seasonal ───────────────────────────────────────
    if seasonal_score >= 18:
        sea_label, sea_color = "עונה חמה ביותר — היסטורי חזק", "#c0392b"
        sea_score = 90
    elif seasonal_score >= 12:
        sea_label, sea_color = "עונה חיובית", "#e67e22"
        sea_score = 65
    elif seasonal_score >= 6:
        sea_label, sea_color = "עונה נייטרלית", "#2980b9"
        sea_score = 40
    else:
        sea_label, sea_color = "עונה חלשה היסטורית", "#888"
        sea_score = 15

    signals["seasonal"] = {
        "label": "עונתיות היסטורית",
        "value": f"ציון {seasonal_score}/20",
        "score": sea_score,
        "signal": sea_label,
        "color": sea_color,
        "weight": WEIGHTS["seasonal"],
        "weighted_score": round(sea_score * WEIGHTS["seasonal"] / 100, 1),
        "explanation": "דפוסי מחיר חוזרים לאורך שנים. לא מבטיח עתיד — אבל מוסיף הקשר.",
    }

    # ── 6. Supply/Demand ──────────────────────────────────
    if supply_score >= 8:
        sup_label, sup_color = "גירעון היצע חמור — ביקוש עולה על היצע", "#c0392b"
        sup_s = 90
    elif supply_score >= 5:
        sup_label, sup_color = "לחץ היצע — ביקוש גבוה", "#e67e22"
        sup_s = 60
    elif supply_score >= 2:
        sup_label, sup_color = "מאוזן", "#2980b9"
        sup_s = 35
    else:
        sup_label, sup_color = "היצע עולה על ביקוש", "#27ae60"
        sup_s = 15

    signals["supply_demand"] = {
        "label": "היצע וביקוש",
        "value": f"ציון {supply_score}/10",
        "score": sup_s,
        "signal": sup_label,
        "color": sup_color,
        "weight": WEIGHTS["supply_demand"],
        "weighted_score": round(sup_s * WEIGHTS["supply_demand"] / 100, 1),
        "explanation": "בסחורות — גירעון ייצור (בצורת, קיצוץ OPEC) מעלה מחיר.",
    }

    # ── 7. Consistency ────────────────────────────────────
    if inst_consistency_pct >= 80:
        con_label, con_color = "עקביות גבוהה — אסטרטגיה ברורה", "#c0392b"
        con_score = 90
    elif inst_consistency_pct >= 60:
        con_label, con_color = "עקביות בינונית-גבוהה", "#e67e22"
        con_score = 65
    elif inst_consistency_pct >= 40:
        con_label, con_color = "עקביות בינונית", "#2980b9"
        con_score = 40
    else:
        con_label, con_color = "אין דפוס עקבי", "#888"
        con_score = 15

    signals["consistency"] = {
        "label": "עקביות מוסדית",
        "value": f"{inst_consistency_pct}%",
        "score": con_score,
        "signal": con_label,
        "color": con_color,
        "weight": WEIGHTS["consistency"],
        "weighted_score": round(con_score * WEIGHTS["consistency"] / 100, 1),
        "explanation": "מוסד שקונה באותו רבעון כל שנה — זו אסטרטגיה, לא מקרה.",
    }

    # ── Final score ───────────────────────────────────────
    total = sum(s["weighted_score"] for s in signals.values())
    total = round(min(total, 100), 1)

    if total >= 75:
        recommendation = "קנייה חזקה"
        rec_color = "#c0392b"
        rec_emoji = "🟢"
        rec_detail = "רוב הסיגנלים חיוביים — כסף חכם נכנס, RSI תומך, עונה חיובית"
    elif total >= 60:
        recommendation = "שקול כניסה"
        rec_color = "#e67e22"
        rec_emoji = "🟡"
        rec_detail = "סיגנלים חיוביים עם כמה סימני זהירות — כניסה חלקית אפשרית"
    elif total >= 45:
        recommendation = "המתן ועקוב"
        rec_color = "#2980b9"
        rec_emoji = "⚪"
        rec_detail = "מעורב — אין סיגנל ברור. עקוב אחרי שינויים ב-RSI ומוסדיים"
    elif total >= 30:
        recommendation = "זהירות — לא עכשיו"
        rec_color = "#f39c12"
        rec_emoji = "🟠"
        rec_detail = "סיגנלים שליליים רבים — המתן לשינוי כיוון"
    else:
        recommendation = "הימנע"
        rec_color = "#888"
        rec_emoji = "🔴"
        rec_detail = "רוב הסיגנלים שליליים — אין כניסה עכשיו"

    return {
        "name": name,
        "asset_type": asset_type,
        "symbol": symbol,
        "price": price,
        "change_pct": change_pct,
        "rsi": rsi,
        "volume": volume,
        "signals": signals,
        "total_score": total,
        "recommendation": recommendation,
        "rec_color": rec_color,
        "rec_emoji": rec_emoji,
        "rec_detail": rec_detail,
        "timestamp": now,
        "custom_notes": custom_notes or [],
        "disclaimer": "אינו ייעוץ השקעות. המידע לצרכי מחקר בלבד.",
    }

def analyze_with_insider(
    name: str,
    asset_type: str,
    symbol: str = "",
    yahoo_ticker: str = "",
    inst_value_m: float = 0,
    inst_count: int = 0,
    inst_consistency_pct: int = 0,
    seasonal_score: int = 0,
    supply_score: int = 0,
    custom_notes: list = None,
    include_insider: bool = True,
) -> dict:
    """Full analysis including Form 4 insider signal."""
    result = analyze_asset(
        name=name, asset_type=asset_type, symbol=symbol,
        yahoo_ticker=yahoo_ticker, inst_value_m=inst_value_m,
        inst_count=inst_count, inst_consistency_pct=inst_consistency_pct,
        seasonal_score=seasonal_score, supply_score=supply_score,
        custom_notes=custom_notes,
    )

    if include_insider and symbol and asset_type == "stock":
        try:
            from .insider_tracker import get_insider_signal
            ticker = symbol.split("/")[0].upper()
            ins = get_insider_signal(ticker, days_back=30)
            ins_score  = ins.get("score", 50)
            ins_signal = ins.get("signal", "אין נתונים")
            ins_color  = ins.get("color", "#888")
            buyers     = ins.get("buyers", [])
            total_buy  = ins.get("total_buy_usd", 0)

            insider_sig = {
                "label": "Insider Buying (Form 4)",
                "value": f"{ins['buys']} קניות | {ins['sells']} מכירות | ${total_buy/1e6:.2f}M",
                "score": ins_score,
                "signal": ins_signal,
                "color": ins_color,
                "weight": WEIGHTS["insider_signal"],
                "weighted_score": round(ins_score * WEIGHTS["insider_signal"] / 100, 1),
                "explanation": "מנהלים שקונים מניות של החברה שלהם עם כסף פרטי — הסיגנל הכי חזק בשוק.",
                "buyers": buyers,
            }
            result["signals"]["insider"] = insider_sig
            result["total_score"] = min(
                round(sum(s["weighted_score"] for s in result["signals"].values()), 1), 100
            )
            # Re-evaluate recommendation
            sc = result["total_score"]
            if sc >= 75:
                result.update({"recommendation": "קנייה חזקה", "rec_color": "#c0392b", "rec_emoji": "🟢",
                               "rec_detail": "רוב הסיגנלים חיוביים כולל Insider Buying"})
            elif sc >= 60:
                result.update({"recommendation": "שקול כניסה", "rec_color": "#e67e22", "rec_emoji": "🟡",
                               "rec_detail": "סיגנלים חיוביים — כניסה חלקית אפשרית"})
            elif sc >= 45:
                result.update({"recommendation": "המתן ועקוב", "rec_color": "#2980b9", "rec_emoji": "⚪",
                               "rec_detail": "מעורב — עקוב אחרי שינויים"})
            else:
                result.update({"recommendation": "זהירות", "rec_color": "#888", "rec_emoji": "🔴",
                               "rec_detail": "סיגנלים שליליים"})
        except Exception:
            pass

    return result
