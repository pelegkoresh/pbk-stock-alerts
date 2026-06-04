import streamlit as st
import sys, os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.rtl_utils import inject_rtl

inject_rtl()

st.title("🐋 PBK Stock Alerts")
st.subheader("מערכת ניטור שוק מוסדי — מה תראה כאן ומאיפה זה מגיע")
st.caption(f"עודכן: {datetime.now().strftime('%H:%M %d/%m/%Y')}")

st.divider()

# ── מה זה Feed ────────────────────────────────────────────
with st.container(border=True):
    st.markdown("#### 📡 מה זה Feed — ולמה זה חשוב?")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
**Feed = זרם נתונים ישיר**

חשוב על זה כמו ברז מים:
- **Bloomberg** משלמים $24,000/שנה על ברז **ישיר** מהבורסה — המים מגיעים ברגע שהעסקה מתבצעת
- **אנחנו** משתמשים ב-SEC EDGAR — הברז הממשלתי הרשמי, חינמי לחלוטין

שני הברזים נותנים **אותם מים** — רק מהירות שונה.
המידע שתראה כאן הוא **אמיתי, רשמי ומדויק** — רק עם עיכוב של שעות ביחס לבלומברג.
        """)
    with col2:
        st.success("✅ **המקורות שלנו — חינמיים ורשמיים:**\n\nSEC EDGAR | CFTC | FINRA | Yahoo Finance | CoinGecko | Google News")
        st.warning("⏱️ **עיכוב ביחס לבלומברג:**\n\nForm 4: עד 48 שעות\n8-K: עד 4 ימים\nחדשות: 15-30 דקות")

st.divider()

# ── מקורות המידע ──────────────────────────────────────────
st.markdown("### 🗂️ מאיפה כל נתון מגיע?")

sources = [
    {
        "emoji": "🏛️",
        "name": "SEC EDGAR — רשות ניירות ערך האמריקאית",
        "what": "דיווחים חובה של כל חברה ציבורית גדולה בארה\"ב",
        "data": ["13F — אחזקות רבעוניות של קרנות ענק", "Form 4 — קנייה/מכירה של מנהלים", "8-K — אירועים מהותיים", "S-1 — הנפקה ראשונית לציבור (IPO)"],
        "cost": "חינם לחלוטין",
        "update": "מיד עם הגשת הדיווח",
        "color": "success",
    },
    {
        "emoji": "📊",
        "name": "CFTC — רגולטור החוזים האמריקאי",
        "what": "פוזיציות שבועיות של קרנות גידול בסחורות",
        "data": ["COT Report — כמה קרנות לונג/שורט על נפט, זהב, חיטה ועוד"],
        "cost": "חינם לחלוטין",
        "update": "כל יום שישי",
        "color": "info",
    },
    {
        "emoji": "📈",
        "name": "Twelve Data + Yahoo Finance",
        "what": "מחירים, ווליום ואינדיקטורים טכניים",
        "data": ["RSI — האם מניה/סחורה זולה או יקרה היסטורית", "% שינוי יומי", "ווליום מסחר"],
        "cost": "Twelve Data: API key קיים | Yahoo: חינם",
        "update": "בזמן אמת",
        "color": "success",
    },
    {
        "emoji": "🪙",
        "name": "CoinGecko",
        "what": "נתוני קריפטו",
        "data": ["Top 100 מטבעות", "שווי שוק", "ווליום 24 שעות"],
        "cost": "חינם",
        "update": "כל 2 דקות",
        "color": "success",
    },
    {
        "emoji": "📰",
        "name": "Google News RSS",
        "what": "חדשות מאוחדות מכל האתרים הגדולים",
        "data": ["Reuters, Bloomberg, CNBC, MarketWatch — כולם יחד", "מסונן לפי מניה/מוסד/נושא"],
        "cost": "חינם",
        "update": "כל 15-30 דקות",
        "color": "info",
    },
    {
        "emoji": "📉",
        "name": "FINRA",
        "what": "Short Interest — כמה שורטיסטים על כל מניה",
        "data": ["Days to Cover", "Short Interest % of Float", "פוטנציאל Short Squeeze"],
        "cost": "חינם",
        "update": "פעמיים בחודש",
        "color": "warning",
    },
]

for src in sources:
    with st.container(border=True):
        col_icon, col_main, col_meta = st.columns([0.5, 4, 1.5])
        with col_icon:
            st.markdown(f"<div style='font-size:32px;text-align:center'>{src['emoji']}</div>", unsafe_allow_html=True)
        with col_main:
            st.markdown(f"**{src['name']}**")
            st.caption(src["what"])
            for d in src["data"]:
                st.caption(f"• {d}")
        with col_meta:
            if src["color"] == "success":
                st.success(f"⏱️ {src['update']}")
            elif src["color"] == "info":
                st.info(f"⏱️ {src['update']}")
            else:
                st.warning(f"⏱️ {src['update']}")
            st.caption(src["cost"])

st.divider()

# ── מה לא זמין בחינם ──────────────────────────────────────
with st.expander("❓ מה לא ניתן לראות בלי תשלום?"):
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**מה חסר לנו ביחס לבלומברג:**")
        items = [
            ("Dark Pool — עסקאות בלתי נראות", "$2,000/חודש", "ניתן לזהות 48 שעות אחרי דרך Form 4"),
            ("ציוצי Elon Musk בשנייה", "$100/חודש", "Google News — 15 דקות אחרי"),
            ("Reuters real-time", "$500/חודש", "RSS חינמי — שעה אחרי"),
            ("Bloomberg Terminal", "$24,000/שנה", "לא רלוונטי לרוב המשקיעים"),
        ]
        for name, cost, alt in items:
            st.markdown(f"- **{name}** ({cost})\n  ↳ *חלופה: {alt}*")
    with col2:
        st.info("""
**המסקנה:**

אנשים שמשלמים $24,000 לבלומברג
מקבלים אותו מידע שאנחנו מקבלים —
רק **מהר יותר בכמה שעות**.

עבור משקיע שמחפש כיוון לטווח בינוני-ארוך,
המידע שלנו **מספיק לחלוטין**.
        """)

st.divider()

# ── ניווט לדפים ───────────────────────────────────────────
st.markdown("### 🧭 מה יש במערכת?")

pages = [
    ("🐋", "Whale Tracker", "Top 20 מניות לפי ווליום מוסדי — מה הלוויתנים קונים"),
    ("🔥", "סחורות חיות Top 50", "מחיר + ווליום + % שינוי — 50 סחורות בזמן אמת"),
    ("🪙", "קריפטו", "CoinGecko Top 50 + מחזיקים מוסדיים"),
    ("💱", "Forex", "18 זוגות מטבע + פוזיציות מוסדיות"),
    ("🚀", "Tesla & SpaceX", "מעקב ייעודי + חדשות + Telegram"),
    ("🚨", "פקודות מוסדיות", "Form 4 Insider — מנהלים שקונים/מוכרים"),
    ("🌡️", "סיגנלים גלובליים", "Fear & Greed + Short Interest + 13D/G"),
    ("💡", "ניתוח השקעה", "ציון 0-100 לכל נכס — 7 סיגנלים משולבים"),
]

cols = st.columns(4)
for i, (emoji, name, desc) in enumerate(pages):
    with cols[i % 4]:
        with st.container(border=True):
            st.markdown(f"**{emoji} {name}**")
            st.caption(desc)

st.divider()

# ── Disclaimer ────────────────────────────────────────────
st.caption("⚠️ כל המידע באתר לצרכי מחקר בלבד — אינו ייעוץ השקעות. תמיד התייעץ עם יועץ מורשה לפני כל השקעה.")
st.caption(f"PBK Stock Alerts | מקורות: SEC EDGAR, CFTC, FINRA, Twelve Data, CoinGecko, Yahoo Finance, Finnhub | {datetime.now().strftime('%Y')}")
