import streamlit as st
import requests
import time
import re
from typing import Optional
import xml.etree.ElementTree as ET

BASE_URL = "https://data.sec.gov"
WWW_BASE = "https://www.sec.gov"
HEADERS = {"User-Agent": "MarketMonitor contact@marketmonitor.local", "Accept-Encoding": "gzip, deflate"}

KNOWN_INSTITUTIONS = {
    "0001067983": "Berkshire Hathaway",
    "0001364742": "Pershing Square (Ackman)",
    "0001336528": "Bridgewater Associates",
    "0000102909": "Vanguard Group",
    "0000880285": "BlackRock",
    "0001037389": "Renaissance Technologies",
    "0001035674": "Tiger Global",
    "0001603466": "Citadel Advisors",
}

INSTITUTION_PROFILES = {
    "0001067983": {
        "name_he": "ברקשייר האת'אווי",
        "manager": "וורן באפט",
        "title": "האורקל מאומהה",
        "style": "ערך לטווח ארוך",
        "aum": "~$300 מיליארד",
        "founded": "1965",
        "desc": (
            "חברת האחזקות הגדולה בעולם. באפט מחזיק מניות לעשרות שנים ומחפש "
            "חברות עם יתרון תחרותי ברור במחיר סביר. ידוע בציטוטיו על "
            "'פחד כשאחרים חמדניים, חמדן כשאחרים פוחדים'."
        ),
    },
    "0001364742": {
        "name_he": "פרשינג סקוור",
        "manager": "ביל אקמן",
        "title": "המשקיע האקטיביסט",
        "style": "אקטיביזם והתערבות",
        "aum": "~$18 מיליארד",
        "founded": "2004",
        "desc": (
            "קרן גידור אגרסיבית. אקמן קונה אחזקות גדולות בחברות ולוחץ על "
            "ההנהלה לשינויים. מוכן להמר נגד חברות בצורה פומבית ודרמטית."
        ),
    },
    "0001336528": {
        "name_he": "ברידג'ווטר אסושיאייטס",
        "manager": "ריי דאליו",
        "title": "הקרן הגדולה בעולם",
        "style": "מאקרו גלובלי",
        "aum": "~$124 מיליארד",
        "founded": "1975",
        "desc": (
            "הקרן הגדולה ביותר בעולם. דאליו מנתח מחזורים כלכליים ומשקיע "
            "לפי התמונה הגלובלית — מניות, איגרות חוב, סחורות ומטבעות יחד."
        ),
    },
    "0000102909": {
        "name_he": "ואנגארד",
        "manager": "סאלם אברהים (CEO)",
        "title": "מלך קרנות המדד",
        "style": "השקעה פסיבית",
        "aum": "~$8 טריליון",
        "founded": "1975",
        "desc": (
            "החברה שהמציאה קרנות המדד הפסיביות. מנהלת את ה-S&P 500 עבור "
            "מיליוני משקיעים. עמלות של 0.03% — הנמוכות בתעשייה."
        ),
    },
    "0000880285": {
        "name_he": "בלקרוק",
        "manager": "לארי פינק",
        "title": "מנהל הנכסים הגדול בעולם",
        "style": "פסיבי + אקטיבי",
        "aum": "~$10 טריליון",
        "founded": "1988",
        "desc": (
            "הגוף הפיננסי הגדול ביותר בעולם. מחזיק מניות בכמעט כל חברה "
            "ציבורית. פינק ידוע במכתביו השנתיים על אחריות תאגידית ו-ESG."
        ),
    },
    "0001037389": {
        "name_he": "רנסנס טכנולוגיות",
        "manager": "פיטר בראון (CEO)",
        "title": "קרן הקוונטים הסודית",
        "style": "אלגוריתמי-כמותי",
        "aum": "~$130 מיליארד",
        "founded": "1982",
        "desc": (
            "הקרן המסתורית ביותר בוול סטריט. המייסד ג'ים סיימונס הניב תשואה "
            "שנתית של 66% ל-30 שנה. עובדת רק עם מתמטיקה ואלגוריתמים."
        ),
    },
    "0001035674": {
        "name_he": "טייגר גלובל",
        "manager": "צ'ייס קולמן",
        "title": "מלך ה-VC וטק",
        "style": "טכנולוגיה וצמיחה",
        "aum": "~$58 מיליארד",
        "founded": "2001",
        "desc": (
            "קרן המתמחה בחברות טכנולוגיה. השקיעה מוקדם ב-Facebook, LinkedIn "
            "ו-Spotify. הפסידה מיליארדים ב-2022 עם קריסת מניות הצמיחה."
        ),
    },
    "0001603466": {
        "name_he": "סיטדל",
        "manager": "קן גריפין",
        "title": "מכונת ההשקעות",
        "style": "רב-אסטרטגי",
        "aum": "~$63 מיליארד",
        "founded": "1990",
        "desc": (
            "אחת מקרנות הגידור הרווחיות בהיסטוריה. גריפין מפעיל עשרות "
            "אסטרטגיות במקביל. ב-2022 הרוויח 16 מיליארד דולר — שיא עולמי."
        ),
    },
}

def _get_json(url):
    for i in range(3):
        try:
            r = requests.get(url, headers=HEADERS, timeout=12)
            r.raise_for_status()
            return r.json()
        except Exception:
            if i < 2: time.sleep(1.5)
    return None

def _get_raw(url):
    for i in range(3):
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            r.raise_for_status()
            return r.content
        except Exception:
            if i < 2: time.sleep(1.5)
    return None

@st.cache_data(ttl=3600, show_spinner=False)
def get_recent_13f_filings(cik, limit=5):
    data = _get_json(f"{BASE_URL}/submissions/CIK{cik.zfill(10)}.json")
    if not data:
        return []
    recent = data.get("filings", {}).get("recent", {})
    filings = []
    for i, form in enumerate(recent.get("form", [])):
        if form in ("13F-HR", "13F-HR/A") and len(filings) < limit:
            filings.append({
                "cik": cik,
                "institution": KNOWN_INSTITUTIONS.get(cik, data.get("name", cik)),
                "form": form,
                "date": recent["filingDate"][i],
                "accession": recent["accessionNumber"][i].replace("-", ""),
                "accession_raw": recent["accessionNumber"][i],
            })
    return filings

def _find_infotable_filename(cik, accession, accession_raw):
    url = f"{WWW_BASE}/Archives/edgar/data/{int(cik)}/{accession}/{accession_raw}-index.htm"
    content = _get_raw(url)
    if not content:
        return None
    html = content.decode("utf-8", errors="replace")
    for href in re.findall(r'href="(/Archives/[^"]+\.xml)"', html):
        if "xslForm" not in href and "primary_doc" not in href:
            return href.split("/")[-1]
    return None

def _parse_holdings_xml(content):
    holdings = []
    try:
        text = content.decode("utf-8", errors="replace")
        text_clean = re.sub(r'\sxmlns[^=]*="[^"]*"', '', text)
        text_clean = re.sub(r'<[a-zA-Z0-9_]+:', '<', text_clean)
        text_clean = re.sub(r'</[a-zA-Z0-9_]+:', '</', text_clean)
        root = ET.fromstring(text_clean.encode("utf-8"))
        for entry in root.findall(".//infoTable"):
            def g(tag):
                el = entry.find(tag)
                return el.text.strip() if el is not None and el.text else ""
            name = g("nameOfIssuer")
            value = g("value")
            shares = g("sshPrnamt")
            cusip = g("cusip")
            if name and value:
                try:
                    holdings.append({
                        "name": name,
                        "cusip": cusip,
                        "value_thousands": int(value.replace(",", "")),
                        "shares": int(shares.replace(",", "")) if shares else 0,
                    })
                except ValueError:
                    continue
    except ET.ParseError:
        pass

    if not holdings:
        text = content.decode("utf-8", errors="replace")
        for m in re.finditer(
            r"<nameOfIssuer>\s*([^<]+?)\s*</nameOfIssuer>.*?"
            r"<cusip>\s*([^<]*?)\s*</cusip>.*?"
            r"<value>\s*([\d,]+)\s*</value>.*?"
            r"<sshPrnamt>\s*([\d,]*)\s*</sshPrnamt>",
            text, re.DOTALL
        ):
            try:
                holdings.append({
                    "name": m.group(1).strip(),
                    "cusip": m.group(2).strip(),
                    "value_thousands": int(m.group(3).replace(",", "")),
                    "shares": int(m.group(4).replace(",", "")) if m.group(4) else 0,
                })
            except ValueError:
                continue

    holdings.sort(key=lambda x: x["value_thousands"], reverse=True)
    return holdings[:50]

@st.cache_data(ttl=3600, show_spinner=False)
def get_holdings_from_filing(cik, accession):
    acc_raw = f"{accession[:10]}-{accession[10:12]}-{accession[12:]}"
    filename = _find_infotable_filename(cik, accession, acc_raw)
    if filename:
        url = f"{WWW_BASE}/Archives/edgar/data/{int(cik)}/{accession}/{filename}"
        content = _get_raw(url)
        if content:
            holdings = _parse_holdings_xml(content)
            if holdings:
                return holdings
    for fname in ["infotable.xml", "form13fInfoTable.xml"]:
        content = _get_raw(f"{WWW_BASE}/Archives/edgar/data/{int(cik)}/{accession}/{fname}")
        if content:
            holdings = _parse_holdings_xml(content)
            if holdings:
                return holdings
    return []

def fetch_all_institutions():
    all_data = []
    for cik, name in KNOWN_INSTITUTIONS.items():
        filings = get_recent_13f_filings(cik, limit=1)
        if filings:
            latest = filings[0]
            holdings = get_holdings_from_filing(cik, latest["accession"])
            all_data.append({
                "institution": name, "cik": cik,
                "filing_date": latest["date"], "accession": latest["accession_raw"],
                "holdings": holdings,
                "total_value_m": sum(h["value_thousands"] for h in holdings) / 1000,
            })
        time.sleep(0.2)
    return all_data
