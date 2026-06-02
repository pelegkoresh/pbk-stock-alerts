import requests
import re
import time
from datetime import datetime
from xml.etree import ElementTree as ET

INSTITUTION_SEARCH_TERMS = {
    "0001067983": "Berkshire Hathaway Warren Buffett",
    "0001364742": "Pershing Square Bill Ackman",
    "0001336528": "Bridgewater Associates Ray Dalio",
    "0000102909": "Vanguard Group",
    "0000880285": "BlackRock Larry Fink",
    "0001037389": "Renaissance Technologies",
    "0001035674": "Tiger Global",
    "0001603466": "Citadel Ken Griffin",
}

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def _clean(text: str) -> str:
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'&amp;', '&', text)
    text = re.sub(r'&quot;', '"', text)
    text = re.sub(r'&lt;', '<', text)
    text = re.sub(r'&gt;', '>', text)
    text = re.sub(r'&#\d+;', '', text)
    return text.strip()

def fetch_news(cik: str, max_results: int = 5) -> list:
    query = INSTITUTION_SEARCH_TERMS.get(cik, "")
    if not query:
        return []

    query_encoded = requests.utils.quote(query)
    url = f"https://news.google.com/rss/search?q={query_encoded}+finance&hl=en-US&gl=US&ceid=US:en"

    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
    except Exception:
        return []

    try:
        root = ET.fromstring(r.content)
    except ET.ParseError:
        return []

    items = root.findall(".//item")
    news = []
    for item in items[:max_results]:
        title_el = item.find("title")
        desc_el = item.find("description")
        link_el = item.find("link")
        pub_el = item.find("pubDate")

        title = _clean(title_el.text) if title_el is not None and title_el.text else ""
        desc = _clean(desc_el.text) if desc_el is not None and desc_el.text else ""
        link = link_el.text.strip() if link_el is not None and link_el.text else ""
        pub = pub_el.text.strip() if pub_el is not None and pub_el.text else ""

        # shorten description to ~120 chars
        if len(desc) > 120:
            desc = desc[:120].rsplit(" ", 1)[0] + "..."

        # parse date
        date_str = ""
        if pub:
            try:
                dt = datetime.strptime(pub[:25], "%a, %d %b %Y %H:%M:%S")
                date_str = dt.strftime("%d/%m/%Y %H:%M")
            except Exception:
                date_str = pub[:16]

        if title:
            news.append({"title": title, "summary": desc, "link": link, "date": date_str})

    return news
