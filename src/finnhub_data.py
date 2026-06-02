import requests
import time
from datetime import datetime, timedelta

# Free tier: 60 calls/minute
# Register at finnhub.io/register
from .secrets_loader import FINNHUB_KEY
BASE = "https://finnhub.io/api/v1"
HEADERS = {"X-Finnhub-Token": FINNHUB_KEY}

def _get(endpoint: str, params: dict = {}) -> dict:
    try:
        r = requests.get(f"{BASE}/{endpoint}", headers=HEADERS, params=params, timeout=8)
        r.raise_for_status()
        return r.json()
    except Exception:
        return {}

def get_news_sentiment(ticker: str) -> dict:
    """Company news sentiment score."""
    try:
        data = _get("news-sentiment", {"symbol": ticker})
        if not data:
            return {}
        buzz = data.get("buzz", {})
        sentiment = data.get("sentiment", {})
        return {
            "score":           round(sentiment.get("bullishPercent", 0) * 100, 1),
            "bearish_pct":     round(sentiment.get("bearishPercent", 0) * 100, 1),
            "articles_weekly": buzz.get("articlesInLastWeek", 0),
            "buzz_weekly":     buzz.get("weeklyAverage", 0),
            "sector_avg":      round(data.get("sectorAverageBullishPercent", 0) * 100, 1),
            "signal":          "BULLISH" if sentiment.get("bullishPercent", 0) > 0.6 else
                               "BEARISH" if sentiment.get("bullishPercent", 0) < 0.4 else "נייטרלי",
        }
    except Exception:
        return {}

def get_short_interest(ticker: str) -> dict:
    """Short interest data from FINRA via Finnhub."""
    try:
        data = _get("stock/short-interest", {"symbol": ticker, "limit": 2})
        if not data or not data.get("data"):
            return {}
        latest = data["data"][0]
        prev   = data["data"][1] if len(data["data"]) > 1 else {}
        short_pct = latest.get("shortInterestRatio", 0)
        short_vol = latest.get("shortInterest", 0)
        days_to_cover = latest.get("daysToConver", 0)
        prev_pct = prev.get("shortInterestRatio", short_pct) if prev else short_pct
        change = short_pct - prev_pct

        if short_pct > 20:
            signal, color = "SHORT SQUEEZE פוטנציאל גבוה", "#c0392b"
        elif short_pct > 10:
            signal, color = "שורט גבוה — שים לב", "#e67e22"
        elif short_pct > 5:
            signal, color = "שורט בינוני", "#2980b9"
        else:
            signal, color = "שורט נמוך", "#27ae60"

        return {
            "short_pct":     round(short_pct, 2),
            "short_volume":  short_vol,
            "days_to_cover": round(days_to_cover, 1),
            "change":        round(change, 2),
            "signal":        signal,
            "color":         color,
            "date":          latest.get("date", ""),
        }
    except Exception:
        return {}

def get_earnings_surprise(ticker: str) -> dict:
    """Recent earnings surprises — beat/miss."""
    try:
        data = _get("stock/earnings", {"symbol": ticker, "limit": 4})
        if not data:
            return {}
        results = []
        for e in data[:4]:
            actual   = e.get("actual", 0) or 0
            estimate = e.get("estimate", 0) or 1
            surprise = ((actual - estimate) / abs(estimate) * 100) if estimate else 0
            results.append({
                "period":   e.get("period", ""),
                "actual":   round(actual, 2),
                "estimate": round(estimate, 2),
                "surprise": round(surprise, 1),
                "beat":     actual > estimate,
            })
        beats = sum(1 for r in results if r["beat"])
        avg_surprise = sum(r["surprise"] for r in results) / len(results) if results else 0
        return {
            "recent":      results,
            "beats":       beats,
            "total":       len(results),
            "avg_surprise": round(avg_surprise, 1),
            "signal":      "מכה הערכות עקבית" if beats >= 3 else
                           "מפספסת לפעמים" if beats == 2 else "מפספסת הערכות",
        }
    except Exception:
        return {}

def get_recommendation_trends(ticker: str) -> dict:
    """Analyst recommendations — buy/hold/sell."""
    try:
        data = _get("stock/recommendation", {"symbol": ticker})
        if not data:
            return {}
        latest = data[0]
        strong_buy = latest.get("strongBuy", 0)
        buy        = latest.get("buy", 0)
        hold       = latest.get("hold", 0)
        sell       = latest.get("sell", 0)
        strong_sell = latest.get("strongSell", 0)
        total = strong_buy + buy + hold + sell + strong_sell or 1
        buy_pct = round((strong_buy + buy) / total * 100, 1)
        return {
            "strong_buy":  strong_buy,
            "buy":         buy,
            "hold":        hold,
            "sell":        sell,
            "strong_sell": strong_sell,
            "buy_pct":     buy_pct,
            "period":      latest.get("period", ""),
            "signal":      "אנליסטים אופטימיים" if buy_pct > 60 else
                           "אנליסטים זהירים" if buy_pct > 40 else "אנליסטים שליליים",
        }
    except Exception:
        return {}

def get_full_finnhub(ticker: str) -> dict:
    """Full Finnhub analysis for a ticker."""
    sentiment = get_news_sentiment(ticker)
    time.sleep(0.15)
    short     = get_short_interest(ticker)
    time.sleep(0.15)
    earnings  = get_earnings_surprise(ticker)
    time.sleep(0.15)
    recs      = get_recommendation_trends(ticker)
    return {
        "ticker":    ticker,
        "sentiment": sentiment,
        "short":     short,
        "earnings":  earnings,
        "recommendations": recs,
    }
