import requests
import time
import re
from datetime import datetime, timedelta

HEADERS = {"User-Agent": "MarketMonitor contact@marketmonitor.local", "Accept-Encoding": "gzip, deflate"}
EDGAR_BASE = "https://data.sec.gov"
WWW_EDGAR  = "https://www.sec.gov"

# CIKs
TESLA_CIK   = "0001318605"
SPACEX_CIK  = "0001181412"
from .secrets_loader import TWELVE_KEY

# ── Telegram ──────────────────────────────────────────────
from .secrets_loader import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_IDS

def send_telegram(message: str, chat_id: str = None) -> bool:
    """שולח הודעה ל-chat_id ספציפי, או לכל הרשימה אם לא צוין."""
    if "ENTER" in TELEGRAM_BOT_TOKEN:
        return False

    targets = [chat_id] if chat_id else TELEGRAM_CHAT_IDS
    success = True

    for cid in targets:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            r = requests.post(url, json={
                "chat_id": cid,
                "text": message,
                "parse_mode": "HTML",
            }, timeout=8)
            if r.status_code != 200:
                success = False
        except Exception:
            success = False
        time.sleep(0.1)

    return success

def add_subscriber(chat_id: str) -> bool:
    """הוסף מנוי חדש ושלח לו הודעת ברוך הבא."""
    if chat_id not in TELEGRAM_CHAT_IDS:
        TELEGRAM_CHAT_IDS.append(chat_id)
    welcome = (
        "🎉 <b>ברוך הבא ל-PBKStockAlerts!</b>\n\n"
        "תקבל התראות על:\n"
        "📊 Volume Spike ב-$TSLA\n"
        "🚀 עדכוני SpaceX S-1\n"
        "🚨 Form 4 Insider Activity\n"
        "📋 8-K Material Events\n\n"
        "המערכת פעילה ✅"
    )
    return send_telegram(welcome, chat_id)

# ── SEC EDGAR ─────────────────────────────────────────────
def fetch_recent_filings(cik: str, forms: list, days_back: int = 3) -> list:
    try:
        url = f"{EDGAR_BASE}/submissions/CIK{cik.zfill(10)}.json"
        r = requests.get(url, headers=HEADERS, timeout=12)
        r.raise_for_status()
        data = r.json()
        recent       = data.get("filings", {}).get("recent", {})
        form_list    = recent.get("form", [])
        dates        = recent.get("filingDate", [])
        accessions   = recent.get("accessionNumber", [])
        descriptions = recent.get("primaryDocument", [])
        cutoff = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        results = []
        for i, form in enumerate(form_list):
            if form not in forms:
                continue
            if dates[i] < cutoff:
                continue
            results.append({
                "form":      form,
                "date":      dates[i],
                "accession": accessions[i],
                "url":       f"{WWW_EDGAR}/Archives/edgar/data/{int(cik)}/{accessions[i].replace('-','')}/{descriptions[i] if i < len(descriptions) else ''}",
                "edgar_url": f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type={form}&dateb=&owner=include&count=5",
                "company":   data.get("name", cik),
                "cik":       cik,
            })
        return results
    except Exception:
        return []

def check_spacex_s1() -> dict:
    try:
        url = f"{EDGAR_BASE}/submissions/CIK{SPACEX_CIK.zfill(10)}.json"
        r = requests.get(url, headers=HEADERS, timeout=12)
        r.raise_for_status()
        data = r.json()
        recent     = data.get("filings", {}).get("recent", {})
        forms      = recent.get("form", [])
        dates      = recent.get("filingDate", [])
        accessions = recent.get("accessionNumber", [])
        s1_filings = []
        for i, form in enumerate(forms):
            if "S-1" in form:
                s1_filings.append({
                    "form":      form,
                    "date":      dates[i],
                    "accession": accessions[i],
                    "url":       f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={SPACEX_CIK}&type=S-1",
                })
        latest     = s1_filings[0] if s1_filings else {}
        amendments = [f for f in s1_filings if "A" in f["form"]]
        return {
            "company":       data.get("name", "SpaceX"),
            "cik":           SPACEX_CIK,
            "latest_filing": latest,
            "s1_count":      len(s1_filings),
            "amendments":    len(amendments),
            "has_pricing":   any("S-1/A" in f["form"] for f in s1_filings[:3]),
            "all_s1":        s1_filings[:5],
            "status":        "📋 S-1 מוגש — ממתין לתמחור" if s1_filings else "❌ לא נמצא S-1",
        }
    except Exception:
        return {"status": "❌ שגיאה בשליפה", "company": "SpaceX"}

def get_tesla_price() -> dict:
    try:
        r = requests.get("https://api.twelvedata.com/quote",
                         params={"symbol": "TSLA", "apikey": TWELVE_KEY}, timeout=8)
        d = r.json()
        if "code" not in d:
            return {
                "price":      float(d.get("close") or 0),
                "open":       float(d.get("open") or 0),
                "high":       float(d.get("high") or 0),
                "low":        float(d.get("low") or 0),
                "change_pct": float(d.get("percent_change") or 0),
                "volume":     int(float(d.get("volume") or 0)),
                "prev_close": float(d.get("previous_close") or 0),
                "source":     "Twelve Data",
            }
    except Exception:
        pass
    try:
        r = requests.get("https://query1.finance.yahoo.com/v8/finance/chart/TSLA",
                         headers={"User-Agent": "Mozilla/5.0"},
                         params={"interval": "1d", "range": "2d"}, timeout=8)
        meta   = r.json()["chart"]["result"][0]["meta"]
        price  = float(meta.get("regularMarketPrice") or 0)
        prev   = float(meta.get("previousClose") or price)
        volume = int(meta.get("regularMarketVolume") or 0)
        change = ((price - prev) / prev * 100) if prev else 0
        return {
            "price":      round(price, 2),
            "change_pct": round(change, 2),
            "volume":     volume,
            "prev_close": round(prev, 2),
            "source":     "Yahoo Finance",
        }
    except Exception:
        return {}

def get_volume_spike(ticker: str = "TSLA") -> dict:
    try:
        r = requests.get("https://query1.finance.yahoo.com/v8/finance/chart/TSLA",
                         headers={"User-Agent": "Mozilla/5.0"},
                         params={"interval": "1d", "range": "25d"}, timeout=8)
        data    = r.json()["chart"]["result"][0]
        volumes = [v for v in data["indicators"]["quote"][0].get("volume", []) if v]
        if len(volumes) < 5:
            return {}
        avg20 = sum(volumes[-21:-1]) / 20 if len(volumes) >= 21 else sum(volumes[:-1]) / len(volumes[:-1])
        today = volumes[-1]
        spike = today / avg20 if avg20 > 0 else 1
        return {
            "today_volume": today,
            "avg20_volume": round(avg20),
            "spike_ratio":  round(spike, 2),
            "is_spike":     spike > 2,
            "spike_label":  f"פי {spike:.1f} מהממוצע" if spike > 1.5 else "נורמלי",
            "signal":       "🚨 SPIKE — ווליום חריג" if spike > 2 else ("⚡ גבוה" if spike > 1.5 else "✅ נורמלי"),
        }
    except Exception:
        return {}

def get_tesla_insider_activity(days_back: int = 14) -> list:
    return fetch_recent_filings(TESLA_CIK, ["4"], days_back=days_back)

def get_tesla_material_events(days_back: int = 30) -> list:
    return fetch_recent_filings(TESLA_CIK, ["8-K", "8-K/A"], days_back=days_back)

def build_alert_message(event_type: str, data: dict) -> str:
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    if event_type == "SEC_FILING":
        return (
            f"🚨 <b>[SEC FILING - {data['company']}]</b>\n"
            f"📋 סוג: <b>{data['form']}</b>\n"
            f"📅 תאריך: {data['date']}\n"
            f"🔗 <a href='{data['url']}'>פתח ב-SEC EDGAR</a>\n"
            f"⏰ {now}"
        )
    elif event_type == "VOLUME_SPIKE":
        return (
            f"⚡ <b>[TSLA VOLUME SPIKE]</b>\n"
            f"📊 ווליום: {data['today_volume']:,}\n"
            f"📈 פי {data['spike_ratio']} מהממוצע 20 ימים\n"
            f"💰 מחיר: ${data.get('price', 0):,.2f}\n"
            f"⏰ {now}"
        )
    elif event_type == "SPACEX_S1":
        return (
            f"🚀 <b>[SPACEX S-1 UPDATE]</b>\n"
            f"📋 {data.get('status','')}\n"
            f"📅 עדכון אחרון: {data.get('latest_filing',{}).get('date','')}\n"
            f"🔗 <a href='https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001181412&type=S-1'>SEC EDGAR</a>\n"
            f"⏰ {now}"
        )
    return f"📢 {event_type}: {now}"
