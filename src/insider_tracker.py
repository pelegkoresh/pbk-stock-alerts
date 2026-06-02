import requests
import re
import time
from datetime import datetime, timedelta
from xml.etree import ElementTree as ET

BASE = "https://www.sec.gov"
EFTS = "https://efts.sec.gov/LATEST/search-index"
HEADERS = {"User-Agent": "MarketMonitor contact@marketmonitor.local", "Accept-Encoding": "gzip, deflate"}

TRANSACTION_CODES = {
    "P": ("קנייה בשוק הפתוח", "🟢", "BUY"),
    "S": ("מכירה בשוק הפתוח", "🔴", "SELL"),
    "A": ("הענקת אופציות/מניות", "🟡", "GRANT"),
    "D": ("החזרה לחברה", "⚪", "RETURN"),
    "F": ("ניכוי מס", "⚪", "TAX"),
    "M": ("מימוש אופציה", "🟡", "OPTION"),
    "G": ("מתנה", "⚪", "GIFT"),
    "I": ("ירושה", "⚪", "INHERIT"),
}

ROLE_LABELS = {
    "CEO": "מנכ\"ל",
    "CFO": "מנכ\"כ",
    "COO": "סמנכ\"ל תפעול",
    "CTO": "סמנכ\"ל טכנולוגיה",
    "President": "נשיא",
    "Director": "דירקטור",
    "Chairman": "יו\"ר",
    "EVP": "סגן נשיא בכיר",
    "SVP": "סגן נשיא",
    "VP": "סגן נשיא",
    "10%": "בעל מניות 10%+",
}

def fetch_recent_form4(days_back: int = 3, limit: int = 50) -> list:
    """Fetch recent Form 4 filings from SEC EDGAR full-text search."""
    try:
        params = {
            "q": '""',
            "dateRange": "custom",
            "startdt": (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d"),
            "enddt": datetime.now().strftime("%Y-%m-%d"),
            "forms": "4",
            "hits.hits._source": "period_of_report,display_names,file_date,entity_name",
            "hits.hits.total": limit,
        }
        url = "https://efts.sec.gov/LATEST/search-index?q=%22%22&forms=4&dateRange=custom"
        url += f"&startdt={params['startdt']}&enddt={params['enddt']}"
        r = requests.get(url, headers=HEADERS, timeout=12)
        r.raise_for_status()
        data = r.json()
        hits = data.get("hits", {}).get("hits", [])
        results = []
        for h in hits[:limit]:
            src = h.get("_source", {})
            results.append({
                "filing_id": h.get("_id", ""),
                "entity": src.get("entity_name", ""),
                "display_names": src.get("display_names", []),
                "file_date": src.get("file_date", ""),
                "period": src.get("period_of_report", ""),
            })
        return results
    except Exception:
        return []

def fetch_form4_details(accession_number: str, cik: str) -> dict:
    """Parse a Form 4 XML filing for transaction details."""
    acc_clean = accession_number.replace("-", "")
    url = f"{BASE}/Archives/edgar/data/{cik}/{acc_clean}/{accession_number}.xml"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        root = ET.fromstring(r.content)
    except Exception:
        return {}

    def gt(tag):
        el = root.find(f".//{tag}")
        return el.text.strip() if el is not None and el.text else ""

    issuer    = gt("issuerName")
    ticker    = gt("issuerTradingSymbol")
    owner     = gt("rptOwnerName")
    role_raw  = gt("officerTitle") or gt("relationship")
    role_he   = next((v for k, v in ROLE_LABELS.items() if k.lower() in role_raw.lower()), role_raw)

    transactions = []
    for txn in root.findall(".//nonDerivativeTransaction"):
        def g(tag):
            el = txn.find(f".//{tag}")
            return el.text.strip() if el is not None and el.text else ""

        code    = g("transactionCode")
        shares  = g("transactionShares")
        price   = g("transactionPricePerShare")
        date    = g("transactionDate")
        owned   = g("sharesOwnedFollowingTransaction")
        acq_dis = g("transactionAcquiredDisposedCode")

        code_info = TRANSACTION_CODES.get(code, (code, "⚪", "OTHER"))
        try:
            shares_f = float(shares.replace(",","")) if shares else 0
            price_f  = float(price.replace(",",""))  if price  else 0
            total    = shares_f * price_f
        except Exception:
            shares_f, price_f, total = 0, 0, 0

        if code in ("P", "S", "M") and shares_f > 0:
            transactions.append({
                "date":       date,
                "code":       code,
                "label":      code_info[0],
                "emoji":      code_info[1],
                "direction":  code_info[2],
                "shares":     shares_f,
                "price":      price_f,
                "total_usd":  total,
                "owned_after": float(owned.replace(",","")) if owned else 0,
                "acq_dis":    acq_dis,
            })

    return {
        "issuer":       issuer,
        "ticker":       ticker,
        "owner":        owner,
        "role":         role_raw,
        "role_he":      role_he,
        "transactions": transactions,
    }

def search_insider_by_ticker(ticker: str, days_back: int = 30) -> list:
    """Search recent Form 4 filings for a specific ticker."""
    try:
        url = "https://efts.sec.gov/LATEST/search-index"
        params = {
            "q": f'"{ticker}"',
            "forms": "4",
            "dateRange": "custom",
            "startdt": (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d"),
            "enddt": datetime.now().strftime("%Y-%m-%d"),
        }
        r = requests.get(url, params=params, headers=HEADERS, timeout=12)
        data = r.json()
        hits = data.get("hits", {}).get("hits", [])
        results = []
        for h in hits[:20]:
            src = h.get("_source", {})
            filing_id = h.get("_id", "")
            results.append({
                "filing_id":    filing_id,
                "entity":       src.get("entity_name", ""),
                "display_names": src.get("display_names", []),
                "file_date":    src.get("file_date", ""),
                "period":       src.get("period_of_report", ""),
            })
        return results
    except Exception:
        return []

def get_insider_signal(ticker: str, days_back: int = 14) -> dict:
    """
    Quick signal: net insider buying vs selling for a ticker.
    Returns sentiment score and summary.
    """
    filings = search_insider_by_ticker(ticker, days_back)
    buys, sells, total_buy_usd, total_sell_usd = 0, 0, 0.0, 0.0
    names = []

    for f in filings[:10]:
        fid = f["filing_id"]
        parts = fid.split(":")
        if len(parts) < 2:
            continue
        acc = parts[0]
        try:
            cik_match = re.search(r"edgar/data/(\d+)/", fid)
            cik = cik_match.group(1) if cik_match else ""
            if not cik:
                continue
            details = fetch_form4_details(acc, cik)
            for txn in details.get("transactions", []):
                if txn["direction"] == "BUY":
                    buys += 1
                    total_buy_usd += txn["total_usd"]
                    if details["owner"] not in names:
                        names.append(f"{details['owner']} ({details['role_he']})")
                elif txn["direction"] == "SELL":
                    sells += 1
                    total_sell_usd += txn["total_usd"]
        except Exception:
            continue
        time.sleep(0.2)

    net = buys - sells
    if net >= 3 or total_buy_usd > 1_000_000:
        signal, color, score = "INSIDER BUY חזק", "#c0392b", 90
    elif net >= 1:
        signal, color, score = "INSIDER BUY", "#e67e22", 70
    elif net == 0 and buys == 0:
        signal, color, score = "אין נתונים", "#888", 50
    elif net < 0:
        signal, color, score = "INSIDER SELL", "#27ae60", 20
    else:
        signal, color, score = "מעורב", "#2980b9", 50

    return {
        "ticker": ticker,
        "buys": buys,
        "sells": sells,
        "total_buy_usd": total_buy_usd,
        "total_sell_usd": total_sell_usd,
        "signal": signal,
        "color": color,
        "score": score,
        "buyers": names[:5],
        "filings_count": len(filings),
        "days_back": days_back,
    }

def fetch_biggest_insider_buys(days_back: int = 5) -> list:
    """
    Fetch the most significant insider purchases in last N days.
    These are the market-moving signals.
    """
    filings = fetch_recent_form4(days_back=days_back, limit=100)
    big_trades = []

    for f in filings[:40]:
        fid = f["filing_id"]
        try:
            cik_match = re.search(r"edgar/data/(\d+)/", fid)
            if not cik_match:
                continue
            cik = cik_match.group(1)
            acc = fid.split(":")[0]
            details = fetch_form4_details(acc, cik)

            for txn in details.get("transactions", []):
                if txn["direction"] == "BUY" and txn["total_usd"] > 50_000:
                    big_trades.append({
                        "issuer":   details.get("issuer", f["entity"]),
                        "ticker":   details.get("ticker", ""),
                        "owner":    details.get("owner", ""),
                        "role_he":  details.get("role_he", ""),
                        "date":     txn["date"],
                        "shares":   txn["shares"],
                        "price":    txn["price"],
                        "total_usd": txn["total_usd"],
                        "file_date": f["file_date"],
                    })
        except Exception:
            continue
        time.sleep(0.2)

    big_trades.sort(key=lambda x: x["total_usd"], reverse=True)
    return big_trades[:20]
