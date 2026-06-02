import streamlit as st
import pandas as pd
from datetime import datetime
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.rtl_utils import inject_rtl
from src.market_signals import (
    fetch_fear_greed, fetch_stock_fear_greed,
    fetch_13dg_filings, fetch_finra_short_interest
)

try:
    from src.finnhub_data import get_full_finnhub
    FINNHUB_OK = True
except ImportError:
    FINNHUB_OK = False

inject_rtl()

st.title("🌡️ סיגנלים גלובליים")
st.caption("כל נתון כולל הסבר מה לעשות איתו — לא רק מה הוא מראה")

if st.button("🔄 רענן"):
    st.cache_data.clear()
    st.rerun()

@st.cache_data(ttl=300,  show_spinner=False)
def load_fg():        return fetch_fear_greed()
@st.cache_data(ttl=300,  show_spinner=False)
def load_stock_fg():  return fetch_stock_fear_greed("SPY")
@st.cache_data(ttl=3600, show_spinner=False)
def load_13dg(days):  return fetch_13dg_filings(days_back=days)
@st.cache_data(ttl=3600, show_spinner=False)
def load_short(t):    return fetch_finra_short_interest(t)
@st.cache_data(ttl=600,  show_spinner=False)
def load_finnhub(t):  return get_full_finnhub(t) if FINNHUB_OK else {}

tab1, tab2, tab3, tab4 = st.tabs([
    "😱 Fear & Greed",
    "🎯 Form 13D/G",
    "📉 Short Interest",
    "📊 Finnhub",
])

# ══════════════════════════════════════════════════════════
# TAB 1 — FEAR & GREED
# ══════════════════════════════════════════════════════════
with tab1:
    st.subheader("😱 Fear & Greed — מדד סנטימנט השוק")

    with st.container(border=True):
        st.markdown("#### 🧠 למה זה אחד הכלים הכי חשובים?")
        st.markdown("""
**Warren Buffett אמר:** *"היה פוחד כשאחרים חמדניים, היה חמדן כשאחרים פוחדים"*

המדד הזה מודד **את הרגשות של השוק** — לא את הנתונים הכלכליים.
כשכולם פוחדים ומוכרים בפאניקה — המחירים יורדים מתחת לשווי האמיתי.
כשכולם קונים מתוך התלהבות עיוורת — המחירים עולים מעל הגיוני.
        """)
        c1, c2 = st.columns(2)
        with c1:
            st.error("**מרץ 2020 — Fear & Greed = 3** (פחד קיצוני)\nמי שקנה S&P 500 → +80% תוך שנה")
        with c2:
            st.success("**נובמבר 2021 — Fear & Greed = 84** (חמדנות קיצונית)\nמי שמכר Bitcoin חסך ירידה של -70%")

    st.divider()

    col_c, col_s = st.columns(2)

    with col_c:
        st.markdown("#### 🪙 קריפטו — Fear & Greed עכשיו")
        with st.spinner("טוען..."):
            fg = load_fg()

        if fg:
            value = fg["value"]
            color = fg["color"]

            st.markdown(f"""
<div style="text-align:center;border:3px solid {color};border-radius:50%;
     width:100px;height:100px;display:flex;align-items:center;justify-content:center;
     margin:auto;font-size:32px;font-weight:900;color:{color}">{value}</div>
<div style="text-align:center;margin-top:8px;font-size:16px;font-weight:700;color:{color}">{fg['label']}</div>
""", unsafe_allow_html=True)

            st.divider()
            st.markdown(f"**מה המדד אומר עכשיו:** {fg['signal']}")

            # Action box
            action = fg["action"]
            if action == "קנה":
                st.success(f"✅ **פעולה מומלצת:** {action} — פחד קיצוני הוא בדרך כלל הזדמנות")
            elif action == "מכור":
                st.warning(f"⚠️ **פעולה מומלצת:** {action} — חמדנות קיצונית היא סיגנל זהירות")
            else:
                st.info(f"ℹ️ **פעולה מומלצת:** {action} — אין סיגנל חד")

            if fg.get("history"):
                st.markdown("**7 ימים אחרונים:**")
                df_h = pd.DataFrame([{"תאריך": h["date"], "ציון": h["value"], "מצב": h["label"]}
                                      for h in fg["history"]])
                st.dataframe(df_h, use_container_width=True, hide_index=True, height=200)
        else:
            st.warning("לא ניתן לטעון")

    with col_s:
        st.markdown("#### 📈 מניות S&P 500 — לחץ שוק")
        with st.spinner("מחשב..."):
            sfg = load_stock_fg()

        if sfg:
            rsi = sfg["rsi"]
            c1, c2 = st.columns(2)
            c1.metric("RSI שוק", f"{rsi:.1f}", help="מתחת ל-30 = oversold, מעל 70 = overbought")
            c2.metric("SPY", f"${sfg['price']:,.2f}", delta=f"{sfg['pct_from_ma']:+.2f}% מ-MA20")

            st.divider()
            if rsi < 30:
                st.success(f"""
**RSI = {rsi:.1f} — שוק OVERSOLD**

המשמעות: המניות ירדו יותר ממה שהכלכלה מצדיקה.
**מה לעשות:** הזדמנות היסטורית לכניסה.
כל פעם ש-RSI ירד מתחת ל-30 ב-20 שנה האחרונות — השוק עלה תוך 12 חודש.
""")
            elif rsi > 70:
                st.warning(f"""
**RSI = {rsi:.1f} — שוק OVERBOUGHT**

המשמעות: המניות עלו מהר מדי יחסית לכלכלה.
**מה לעשות:** שקול להפחית חשיפה או להמתין לתיקון.
""")
            else:
                st.info(f"""
**RSI = {rsi:.1f} — שוק נייטרלי**

המשמעות: אין סיגנל חד בכיוון מסוים.
**מה לעשות:** עקוב אחרי סיגנלים אחרים (מוסדיים, Insider).
""")

# ══════════════════════════════════════════════════════════
# TAB 2 — FORM 13D/G
# ══════════════════════════════════════════════════════════
with tab2:
    st.subheader("🎯 Form 13D/G — כשמישהו גדול נכנס")

    with st.container(border=True):
        st.markdown("#### 🧠 למה זה הסיגנל הכי חזק לאחרי Insider?")
        st.markdown("""
**מה זה:** כשמשקיע קונה יותר מ-**5%** ממניה — חוק SEC מחייב אותו לדווח תוך 10 ימים.

**ההבדל בין 13D ל-13G:**
- **13D = אקטיביסט** — מתכנן לדרוש שינויים בהנהלה, מכירת החברה, חלוקת דיבידנד. **הכי חזק.**
- **13G = פסיבי** — קנה להשקעה בלבד. חשוב אבל פחות דרמטי.

**דוגמאות היסטוריות:**
        """)
        c1, c2 = st.columns(2)
        with c1:
            st.success("**2022 — Carl Icahn קנה 9.7% ב-McDonald's**\nהגיש 13D → המניה עלתה +23%")
        with c2:
            st.success("**2023 — Ackman גילה 9.9% ב-Howard Hughes**\n13G → מניה עלתה +45% תוך 6 חודשים")

        st.warning("**כלל הזהב:** כשאקטיביסט נכנס — הוא לא יוצא לפני שהמניה עולה. הוא שם עשרות מיליונים.")

    st.divider()

    days_13dg = st.select_slider("כמה ימים אחורה?", options=[3, 5, 7, 14, 30], value=7)

    with st.spinner("שולף דיווחי 13D/G מ-SEC EDGAR..."):
        filings_13dg = load_13dg(days_13dg)

    if not filings_13dg:
        st.info("לא נמצאו דיווחים חדשים בטווח זה. נסה טווח ארוך יותר.")
    else:
        activist = [f for f in filings_13dg if f["is_activist"]]
        passive  = [f for f in filings_13dg if not f["is_activist"]]

        c1, c2, c3 = st.columns(3)
        c1.metric("סה\"כ דיווחים", len(filings_13dg))
        c2.metric("🔴 אקטיביסטים", len(activist), help="הכי חשוב לעקוב")
        c3.metric("🟡 פסיביים", len(passive))

        if activist:
            st.markdown("### 🔴 אקטיביסטים — פעל מהר")
            st.caption("אקטיביסט נכנס = לרוב תחילת תהליך שיעלה את המניה. בדוק את החברה ושקול כניסה.")
            for f in activist[:8]:
                with st.container(border=True):
                    c1, c2 = st.columns([4, 1])
                    with c1:
                        st.markdown(f"**{f['entity']}**")
                        if f["display_names"]:
                            st.caption(f"מדווח: {', '.join(f['display_names'][:2])}")
                        st.caption(f"📅 {f['file_date']} | סוג: {f['form_type']}")
                    with c2:
                        st.error("אקטיביסט")

        if passive:
            st.markdown("### 🟡 כניסות פסיביות — מעניין לעקוב")
            rows = [{"חברה": f["entity"], "סוג": f["form_type"], "תאריך": f["file_date"]}
                    for f in passive[:15]]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════
# TAB 3 — SHORT INTEREST
# ══════════════════════════════════════════════════════════
with tab3:
    st.subheader("📉 Short Interest — פוטנציאל Short Squeeze")

    with st.container(border=True):
        st.markdown("#### 🧠 מה זה Short Squeeze ולמה כדאי לדעת?")
        st.markdown("""
**שורטיסט** = מישהו שמהמר שהמניה תרד. הוא לווה מניות ומוכר אותן.
**הסיכון שלו:** אם המניה עולה — הוא חייב לקנות בחזרה בהפסד.

**כשיש הרבה שורטיסטים → Short Squeeze:**
אם המניה מתחילה לעלות — כל השורטיסטים **חייבים** לקנות בבת אחת כדי להגביל הפסד.
הקנייה הזו מדלקת את המניה עוד → יותר שורטיסטים נלחצים → עוד קנייה → ...
        """)
        st.error("""
**GameStop ינואר 2021:**
Short Interest = 140% | Days to Cover = 12
מחיר: מ-$5 → **$400** תוך שבועיים.
WallStreetBets זיהו את ה-short interest הגבוה וקנו. השורטיסטים נלחצו לקנות → Squeeze.
""")
        st.info("""
**Days to Cover = כמה ימים ייקח לסגור כל השורטים בנפח יומי רגיל**
DTC > 10 = פוטנציאל גבוה לסחיטה | DTC < 2 = לחץ שורט נמוך
""")

    st.divider()
    ticker_short = st.text_input("סימבול מניה לבדיקה", value="GME").upper()

    if ticker_short:
        with st.spinner(f"שולף Short Interest עבור {ticker_short}..."):
            short_data = load_short(ticker_short)

        if short_data.get("error"):
            st.warning("FINRA: נסה דרך Finnhub בטאב הבא (Short Interest מדויק יותר)")
        else:
            color = short_data["color"]
            c1, c2, c3 = st.columns(3)
            c1.metric("Days to Cover", short_data["days_to_cover"])
            c2.metric("כמות שורט", f"{short_data['short_qty']:,}")
            c3.metric("עדכון", short_data["date"])

            st.markdown(f"""
<div style="padding:14px;background:{color}22;border-radius:10px;
     border:2px solid {color};margin-top:8px">
  <div style="font-size:18px;font-weight:700;color:{color}">{short_data['signal']}</div>
  <div style="font-size:13px;color:#555;margin-top:6px">
    {"⚠️ פוטנציאל Short Squeeze — עקוב אחרי נפח מסחר וחדשות חיוביות" if short_data["days_to_cover"] > 5
     else "✅ לחץ שורט נמוך — סביר שלא יהיה Squeeze"}
  </div>
</div>
""", unsafe_allow_html=True)

            if short_data["days_to_cover"] > 5:
                st.warning("""
**מה לעשות עם Short Squeeze פוטנציאל:**
1. בדוק אם יש **קטליזטור** — חדשות טובות, Insider buying, Earnings beat
2. Short Squeeze לבד אינו סיבה לקנות — צריך גם פונדמנטלים
3. אם נכנסים — תקנו נקודת יציאה מראש. Squeeze יכול להיפוך מהיר.
""")

# ══════════════════════════════════════════════════════════
# TAB 4 — FINNHUB
# ══════════════════════════════════════════════════════════
with tab4:
    st.subheader("📊 Finnhub — סנטימנט + Earnings + אנליסטים")

    with st.container(border=True):
        st.markdown("#### 🧠 למה 3 הנתונים האלה חשובים?")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.info("""
**סנטימנט חדשות**
כמה % מהמאמרים BULLISH.
מעל 60% = שוק אופטימי לגבי המניה.
פחות מ-40% = לחץ תקשורתי — לפעמים הזדמנות.
""")
        with c2:
            st.info("""
**Earnings Surprise**
האם החברה עברה את הציפיות?
3/4 רבעונים — הכי אמין.
Beat עקבי = ניהול שיודע לספר.
""")
        with c3:
            st.info("""
**המלצות אנליסטים**
60%+ Buy = קונסנסוס חיובי.
לא לפעול לבד — אנליסטים טועים.
אבל מעל 70% Buy = כסף מוסדי יגיע.
""")

    st.divider()

    if not FINNHUB_OK:
        st.warning("Finnhub לא מוגדר עדיין.")
        with st.container(border=True):
            st.markdown("#### הוספת Finnhub — 2 דקות, חינמי לחלוטין")
            st.markdown("""
**שלב 1:** כנס ל-[finnhub.io/register](https://finnhub.io/register)
**שלב 2:** הרשם (חינמי — אין כרטיס אשראי)
**שלב 3:** העתק את ה-API key
**שלב 4:** פתח `C:\\StockApp\\src\\finnhub_data.py`
**שלב 5:** שנה את השורה הראשונה:
""")
            st.code('FINNHUB_KEY = "הכנס_כאן_את_ה_KEY_שלך"')
            st.success("זהו. הדף יתמלא אוטומטית בנתונים.")
    else:
        ticker_finn = st.text_input("סימבול לניתוח", value="AAPL").upper()

        if ticker_finn:
            with st.spinner(f"מנתח {ticker_finn}..."):
                finn = load_finnhub(ticker_finn)

            if finn:
                sent = finn.get("sentiment", {})
                if sent:
                    bull = sent.get("score", 0)
                    bear = sent.get("bearish_pct", 0)
                    sig  = sent.get("signal", "")
                    color = "#1a7a1a" if "BULL" in sig else "#c0392b" if "BEAR" in sig else "#888"
                    st.metric("סנטימנט חדשות", f"BULLISH: {bull}%",
                              delta=f"BEARISH: {bear}%")
                    st.markdown(f"<div style='padding:8px;background:{color}22;border-radius:6px;color:{color};font-weight:700'>{sig} — {sent.get('articles_weekly',0)} מאמרים השבוע</div>",
                                unsafe_allow_html=True)
                    st.divider()

                earn = finn.get("earnings", {})
                if earn and earn.get("recent"):
                    beats = earn["beats"]
                    total = earn["total"]
                    avg   = earn["avg_surprise"]
                    c1, c2 = st.columns(2)
                    c1.metric("הכה הערכות", f"{beats}/{total} רבעונים")
                    c2.metric("הפתעה ממוצעת", f"{avg:+.1f}%")
                    if beats >= 3:
                        st.success("הכאת ציפיות עקבית — ניהול אמין שמספק תוצאות")
                    elif beats <= 1:
                        st.warning("מפספסת ציפיות — בדוק מדוע לפני כניסה")
                    df_earn = pd.DataFrame(earn["recent"])
                    df_earn.columns = ["רבעון","בפועל","הערכה","הפתעה %","הכה?"]
                    st.dataframe(df_earn, use_container_width=True, hide_index=True)
                    st.divider()

                recs = finn.get("recommendations", {})
                if recs:
                    buy_pct = recs.get("buy_pct", 0)
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Buy + Strong Buy", f"{recs.get('strong_buy',0)+recs.get('buy',0)}")
                    c2.metric("Hold", recs.get("hold",0))
                    c3.metric("Sell", recs.get("sell",0)+recs.get("strong_sell",0))
                    if buy_pct > 70:
                        st.success(f"{buy_pct}% מהאנליסטים ממליצים קנייה — קונסנסוס חזק")
                    elif buy_pct > 50:
                        st.info(f"{buy_pct}% קנייה — רוב אופטימי אבל לא חד")
                    else:
                        st.warning(f"רק {buy_pct}% קנייה — אנליסטים סקפטיים")

    st.divider()
    st.caption("מקורות: alternative.me | SEC EDGAR | FINRA | Finnhub.io | כל הנתונים לצרכי מחקר בלבד")
