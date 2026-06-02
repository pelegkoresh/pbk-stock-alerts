import requests
import time
import re
from datetime import datetime, timedelta

HEADERS = {"User-Agent": "MarketMonitor contact@marketmonitor.local", "Accept-Encoding": "gzip, deflate"}

# ── Fear & Greed Index (Alternative.me) ──────────────────
def fetch_fear_greed() -> dict:
    """
    Crypto Fear & Greed Index from alternative.me
    0 = Extreme Fear (buy signal), 100 = Extreme Greed (sell signal)
    """
    try:
        r = requests.get("https://api.alternative.me/fng/?limit=7", timeout=8)
        data = r.json().get("data", [])
        if not data:
            return {}

        latest = data[0]
        value = int(latest.get("value", 50))
        label = latest.get("value_classification", "")

        history = [{"date": d["timestamp"], "value": int(d["value"]),
                    "label": d["value_classification"]} for d in data[:7]]

        if value <= 20:
            signal, color, action = "פחד קיצוני — הזדמנות קנייה היסטורית", "#c0392b", "קנה"
        elif value <= 40:
            signal, color, action = "פחד — שוק לחוץ", "#e67e22", "שקול קנייה"
        elif value <= 60:
            signal, color, action = "נייטרלי", "#2980b9", "המתן"
        elif value <= 80:
            signal, color, action = "חמדנות — שוק מתחמם", "#f39c12", "זהירות"
        else:
            signal, color, action = "חמדנות קיצונית — שקול מכירה", "#27ae60", "מכור"

        return {
            "value":   value,
            "label":   label,
            "signal":  signal,
            "color":   color,
            "action":  action,
            "history": history,
            "updated": latest.get("timestamp", ""),
        }
    except Exception:
        return {}

# ── Stock Fear & Greed (CNN-style calculation) ────────────
def fetch_stock_fear_greed(ticker: str = "SPY") -> dict:
    """
    Simple stock market fear/greed proxy using RSI + Yahoo data.
    """
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"},
                         params={"interval": "1d", "range": "30d"}, timeout=8)
        data = r.json()
        closes = data["chart"]["result"][0]["indicators"]["quote"][0].get("close", [])
        closes = [c for c in closes if c]

        if len(closes) < 14:
            return {}

        # Simple RSI calculation
        gains = [max(closes[i]-closes[i-1], 0) for i in range(1, len(closes))]
        losses = [max(closes[i-1]-closes[i], 0) for i in range(1, len(closes))]
        avg_gain = sum(gains[-14:]) / 14
        avg_loss = sum(losses[-14:]) / 14
        rs = avg_gain / avg_loss if avg_loss > 0 else 100
        rsi = 100 - (100 / (1 + rs))

        current = closes[-1]
        ma20 = sum(closes[-20:]) / 20
        above_ma = current > ma20
        pct_from_ma = (current - ma20) / ma20 * 100

        score = rsi
        return {
            "rsi": round(rsi, 1),
            "price": round(current, 2),
            "ma20":  round(ma20, 2),
            "above_ma": above_ma,
            "pct_from_ma": round(pct_from_ma, 2),
            "fear_score": round(100 - rsi, 1),
        }
    except Exception:
        return {}

# ── SEC Form 13D/G — Major stake changes ────────────────
def fetch_13dg_filings(days_back: int = 7) -> list:
    """
    Form 13D = activist investor bought 5%+ (must report within 10 days)
    Form 13G = passive investor bought 5%+ (less aggressive)
    These are often precursors to M&A, activist campaigns, takeovers.
    """
    try:
        start = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        end   = datetime.now().strftime("%Y-%m-%d")
        url   = f"https://efts.sec.gov/LATEST/search-index?q=%22%22&forms=SC+13D,SC+13G&dateRange=custom&startdt={start}&enddt={end}"
        r = requests.get(url, headers=HEADERS, timeout=12)
        r.raise_for_status()
        hits = r.json().get("hits", {}).get("hits", [])

        results = []
        for h in hits[:30]:
            src = h.get("_source", {})
            form_type = src.get("form_type", "")
            is_activist = "13D" in form_type

            results.append({
                "filing_id":     h.get("_id", ""),
                "form_type":     form_type,
                "entity":        src.get("entity_name", ""),
                "display_names": src.get("display_names", []),
                "file_date":     src.get("file_date", ""),
                "period":        src.get("period_of_report", ""),
                "is_activist":   is_activist,
                "signal":        "🔴 אקטיביסט — 5%+" if is_activist else "🟡 פסיבי — 5%+",
                "color":         "#c0392b" if is_activist else "#f39c12",
                "significance":  "גבוה מאוד" if is_activist else "בינוני",
            })
        return results
    except Exception:
        return []

def parse_13dg_issuer(filing_id: str) -> dict:
    """Extract company name and stake % from 13D/G filing."""
    try:
        acc = filing_id.split(":")[0]
        cik_match = re.search(r"edgar/data/(\d+)/", filing_id)
        if not cik_match:
            return {}
        cik = cik_match.group(1)
        acc_clean = acc.replace("-", "")
        url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc_clean}/{acc}.txt"
        r = requests.get(url, headers=HEADERS, timeout=10)

        text = r.text[:3000]
        issuer_match = re.search(r"ISSUER NAME[:\s]+([^\n]+)", text, re.IGNORECASE)
        pct_match    = re.search(r"(\d+\.?\d*)\s*%", text)
        cusip_match  = re.search(r"CUSIP[:\s]+([0-9A-Z]{9})", text, re.IGNORECASE)

        return {
            "issuer":    issuer_match.group(1).strip() if issuer_match else "",
            "stake_pct": pct_match.group(1) if pct_match else "",
            "cusip":     cusip_match.group(1) if cusip_match else "",
        }
    except Exception:
        return {}

# ── FINRA Short Interest (free endpoint) ────────────────
def fetch_finra_short_interest(ticker: str) -> dict:
    """
    FINRA bi-monthly short interest data.
    High short interest + rising price = SHORT SQUEEZE potential.
    """
    try:
        url = "https://api.finra.org/data/group/OTCMarket/name/otcMarketShortInterest"
        params = {
            "limit": 5,
            "filters": f'[{{"fieldName":"symbolCode","values":["{ticker}"]}}]',
            "fields": "symbolCode,shortInterestQty,settlementDate,averageDailyVolume,daysToCover",
        }
        r = requests.get(url, params=params, headers=HEADERS, timeout=10)
        data = r.json()

        if not data:
            return {"error": "No FINRA data"}

        latest = data[0]
        qty       = int(latest.get("shortInterestQty", 0))
        avg_vol   = int(latest.get("averageDailyVolume", 1) or 1)
        dtc       = float(latest.get("daysToCover", 0) or 0)
        date      = latest.get("settlementDate", "")

        if dtc > 10:
            signal, color = "SHORT SQUEEZE גבוה — DTC > 10", "#c0392b"
        elif dtc > 5:
            signal, color = "לחץ שורט — DTC 5-10", "#e67e22"
        elif dtc > 2:
            signal, color = "שורט בינוני", "#2980b9"
        else:
            signal, color = "שורט נמוך", "#27ae60"

        return {
            "ticker":      ticker,
            "short_qty":   qty,
            "avg_vol":     avg_vol,
            "days_to_cover": round(dtc, 1),
            "signal":      signal,
            "color":       color,
            "date":        date,
            "source":      "FINRA",
        }
    except Exception:
        return {"error": "FINRA not available"}
