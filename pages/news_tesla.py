"""
news_tesla.py
=============
Real-time news for Tesla, SpaceX, xAI, Elon Musk
Sources: Google News RSS, SEC 8-K, Reuters RSS
"""
import requests
import re
import time
from datetime import datetime
from xml.etree import ElementTree as ET

HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/rss+xml, application/xml"}

NEWS_SOURCES = [
    {"name": "Tesla — Google News",    "url": "https://news.google.com/rss/search?q=Tesla+TSLA+stock&hl=en-US&gl=US&ceid=US:en",   "tag": "TSLA"},
    {"name": "SpaceX — Google News",   "url": "https://news.google.com/rss/search?q=SpaceX+IPO+S-1&hl=en-US&gl=US&ceid=US:en",    "tag": "SPCX"},
    {"name": "xAI — Google News",      "url": "https://news.google.com/rss/search?q=xAI+Elon+Musk+Tesla+merger&hl=en-US&gl=US&ceid=US:en", "tag": "xAI"},
    {"name": "Elon Musk — Google News","url": "https://news.google.com/rss/search?q=Elon+Musk+investor&hl=en-US&gl=US&ceid=US:en","tag": "MUSK"},
]

# High-signal keywords that indicate market-moving news
SIGNAL_KEYWORDS = {
    "🔴 דחוף": ["merger", "acquisition", "SEC", "lawsuit", "recall", "crash", "bankruptcy", "מיזוג"],
    "🟢 חיובי": ["record", "profit", "beats", "growth", "contract", "deal", "partnership", "approved"],
    "🟡 IPO":   ["IPO", "S-1", "valuation", "shares", "offering", "roadshow", "listing"],
    "⚡ Insider":["insider", "Form 4", "bought", "sold", "stake", "13F", "13D"],
}

def _clean(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', text)
    for ent, ch in [('&amp;','&'),('&quot;','"'),('&lt;','<'),('&gt;','>'),('&#39;',"'")]:
        text = text.replace(ent, ch)
    return text.strip()

def _parse_date(pub_str: str) -> str:
    try:
        dt = datetime.strptime(pub_str[:25], "%a, %d %b %Y %H:%M:%S")
        return dt.strftime("%d/%m %H:%M")
    except Exception:
        return pub_str[:10] if pub_str else ""

def _get_signal(title: str, desc: str) -> tuple:
    text = (title + " " + desc).lower()
    for signal, keywords in SIGNAL_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in text:
                return signal
    return "📰 חדשות"

def fetch_news_source(source: dict, limit: int = 5) -> list:
    try:
        r = requests.get(source["url"], headers=HEADERS, timeout=10)
        r.raise_for_status()
        root = ET.fromstring(r.content)
        items = root.findall(".//item")
        news = []
        for item in items[:limit]:
            title = _clean(item.findtext("title") or "")
            desc  = _clean(item.findtext("description") or "")
            link  = (item.findtext("link") or "").strip()
            pub   = _parse_date(item.findtext("pubDate") or "")
            if len(desc) > 150:
                desc = desc[:150].rsplit(" ", 1)[0] + "..."
            if title:
                news.append({
                    "title":   title,
                    "desc":    desc,
                    "link":    link,
                    "date":    pub,
                    "tag":     source["tag"],
                    "source":  source["name"],
                    "signal":  _get_signal(title, desc),
                })
        return news
    except Exception:
        return []

def fetch_all_tesla_news(limit_per_source: int = 5) -> list:
    all_news = []
    for src in NEWS_SOURCES:
        news = fetch_news_source(src, limit_per_source)
        all_news.extend(news)
        time.sleep(0.2)
    # Sort: urgent first, then by signal type
    signal_order = {"🔴 דחוף": 0, "🟡 IPO": 1, "⚡ Insider": 2, "🟢 חיובי": 3, "📰 חדשות": 4}
    all_news.sort(key=lambda x: signal_order.get(x["signal"], 5))
    return all_news[:30]
