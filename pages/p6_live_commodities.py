import streamlit as st
import pandas as pd
from datetime import datetime
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.rtl_utils import inject_rtl

try:
    from src.live_commodities_v2 import fetch_top_commodities, fetch_by_category, CATEGORIES, TOP_COMMODITIES
except ImportError as e:
    st.error(f"שגיאה: {e}")
    st.stop()

try:
    from src.cftc_data import fetch_all_cftc, COMMODITY_CODES
except ImportError:
    def fetch_all_cftc(): return []

inject_rtl()

st.title("🔥 סחורות חיות — Top 50")
st.caption(f"עדכון: {datetime.now().strftime('%H:%M:%S')} | מקורות: Twelve Data + Yahoo Finance + CFTC")

# ── Global controls ───────────────────────────────────────
col_ref, col_cat, col_sort = st.columns([1, 2, 2])
with col_ref:
    if st.button("🔄 רענן"):
        st.cache_data.clear()
        st.rerun()
with col_cat:
    selected_cat = st.selectbox("קטגוריה", ["הכל"] + CATEGORIES)
with col_sort:
    sort_by = st.selectbox("מיין לפי", ["% שינוי (הכי חם)", "ווליום", "מחיר"])

# ── Data loaders ──────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def load_commodities(cat):
    if cat == "הכל":
        return fetch_top_commodities(limit=50)
    return fetch_by_category(cat)

@st.cache_data(ttl=3600, show_spinner=False)
def load_cftc():
    return fetch_all_cftc()

tab1, tab2, tab3 = st.tabs(["🔥 הכי חמות", "📋 כל הסחורות", "🏛️ CFTC — מוסדיים"])

# ── TAB 1: Hot commodities ────────────────────────────────
with tab1:
    with st.spinner("שולף נתונים חיים..."):
        commodities = load_commodities(selected_cat)

    available = [c for c in commodities if c.get("available")]
    if not available:
        st.warning("לא ניתן לשלוף נתונים כרגע.")
        st.stop()

    # Sort
    if sort_by == "ווליום":
        available.sort(key=lambda x: x.get("volume", 0), reverse=True)
    elif sort_by == "מחיר":
        available.sort(key=lambda x: x.get("price", 0), reverse=True)

    up   = [c for c in available if c.get("change_pct", 0) > 0][:6]
    down = [c for c in available if c.get("change_pct", 0) < 0][:6]

    col_up, col_dn = st.columns(2)

    with col_up:
        st.markdown("### 📈 עולות")
        for c in up:
            pct = c["change_pct"]
            vol = f"{c['volume']:,}" if c.get("volume", 0) > 0 else "—"
            with st.container(border=True):
                a, b = st.columns([2, 1])
                with a:
                    st.markdown(f"**{c['emoji']} {c['name']}**")
                    st.caption(c["category"])
                with b:
                    st.metric("מחיר", f"${c['price']:,.3f}", delta=f"+{pct:.2f}%")
                st.caption(f"ווליום: {vol} | {c['source']}")

    with col_dn:
        st.markdown("### 📉 יורדות")
        for c in down:
            pct = c["change_pct"]
            vol = f"{c['volume']:,}" if c.get("volume", 0) > 0 else "—"
            with st.container(border=True):
                a, b = st.columns([2, 1])
                with a:
                    st.markdown(f"**{c['emoji']} {c['name']}**")
                    st.caption(c["category"])
                with b:
                    st.metric("מחיר", f"${c['price']:,.3f}", delta=f"{pct:.2f}%")
                st.caption(f"ווליום: {vol} | {c['source']}")

# ── TAB 2: Full table ─────────────────────────────────────
with tab2:
    with st.spinner("טוען טבלה מלאה..."):
        all_data = load_commodities(selected_cat)

    rows = []
    for i, c in enumerate(all_data, 1):
        if not c.get("available"):
            continue
        pct = c.get("change_pct", 0)
        rows.append({
            "#": i,
            "סחורה": f"{c['emoji']} {c['name']}",
            "קטגוריה": c["category"],
            "מחיר": f"${c['price']:,.4f}",
            "% שינוי": f"{'+' if pct > 0 else ''}{pct:.2f}%",
            "ווליום": f"{c['volume']:,}" if c.get("volume", 0) > 0 else "—",
            "מקור": c.get("source", "—"),
        })

    df = pd.DataFrame(rows).set_index("#")

    def color_pct(val):
        if "+" in str(val): return "color:#c0392b;font-weight:600"
        if str(val).startswith("-"): return "color:#27ae60;font-weight:600"
        return ""

    st.subheader(f"כל הסחורות — {len(rows)} רשומות")
    st.dataframe(df.style.map(color_pct, subset=["% שינוי"]),
                 use_container_width=True, height=600)

    st.subheader("גרף % שינוי")
    chart_rows = [{"שם": f"{c['emoji']} {c['name']}", "% שינוי": c.get("change_pct", 0)}
                  for c in all_data if c.get("available")][:20]
    if chart_rows:
        st.bar_chart(pd.DataFrame(chart_rows).set_index("שם"))

# ── TAB 3: CFTC Institutional ────────────────────────────
with tab3:
    st.subheader("🏛️ CFTC — דוחות Commitments of Traders")
    st.caption("מקור רשמי: CFTC.gov | מתעדכן כל יום שישי | מציג פוזיציות של קרנות גידור ומשקיעים מוסדיים")

    with st.spinner("שולף דוחות CFTC..."):
        cftc_data = load_cftc()

    if not cftc_data:
        st.warning("לא ניתן לשלוף נתוני CFTC כרגע.")
        st.info("CFTC מפרסם את הדוח כל יום שישי ב-15:30 שעון מזרחי")
    else:
        with_data = [c for c in cftc_data if c.get("net_noncom") is not None and c.get("net_noncom") != 0]
        if with_data:
            bullish = [c for c in with_data if c.get("sentiment") == "BULLISH"]
            bearish = [c for c in with_data if c.get("sentiment") == "BEARISH"]

            b1, b2 = st.columns(2)
            b1.metric("BULLISH (קרנות לונג)", len(bullish))
            b2.metric("BEARISH (קרנות שורט)", len(bearish))
            st.divider()

            rows_cftc = []
            for c in with_data:
                rows_cftc.append({
                    "סחורה": f"{c['emoji']} {c['name_he']}",
                    "תאריך דוח": c.get("report_date", "—"),
                    "קרנות LONG": f"{c.get('noncom_long', 0):,}",
                    "קרנות SHORT": f"{c.get('noncom_short', 0):,}",
                    "NET": f"{c.get('net_noncom', 0):,}",
                    "שינוי שבועי": f"{c.get('change_week', 0):,}",
                    "סנטימנט": "📈 BULLISH" if c.get("sentiment") == "BULLISH" else "📉 BEARISH",
                    "OI": f"{c.get('open_interest', 0):,}",
                })

            df_cftc = pd.DataFrame(rows_cftc)
            df_cftc.index = range(1, len(df_cftc)+1)

            def color_sent(val):
                if "BULLISH" in str(val): return "color:#1a7a1a;font-weight:700"
                if "BEARISH" in str(val): return "color:#c0392b;font-weight:700"
                return ""

            st.dataframe(df_cftc.style.map(color_sent, subset=["סנטימנט"]),
                         use_container_width=True, height=500)
        else:
            st.info("נתוני CFTC זמינים חלקית — נסה שוב מחר לאחר עדכון שבועי")

    st.divider()
    st.caption("מקור: CFTC Commitments of Traders (cftc.gov) | עדכון: כל יום שישי 15:30 ET")
    st.caption("COT = Commitments of Traders | Non-Commercial = קרנות גידור וספקולנטים גדולים")
