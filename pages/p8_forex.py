import streamlit as st
import pandas as pd
from datetime import datetime
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.rtl_utils import inject_rtl
from src.forex_data import fetch_all_forex, get_forex_institutional_positions, CATEGORIES, FOREX_PAIRS

inject_rtl()

st.title("💱 Forex — מטבעות עולמיים + מוסדיים")
st.caption(f"עדכון: {datetime.now().strftime('%H:%M:%S')} | מקורות: Twelve Data + Yahoo Finance + CFTC")

@st.cache_data(ttl=180, show_spinner=False)
def load_forex():
    return fetch_all_forex()

col_ref, col_cat = st.columns([1, 2])
with col_ref:
    if st.button("🔄 רענן"):
        st.cache_data.clear()
        st.rerun()
with col_cat:
    selected_cat = st.selectbox("קטגוריה", ["הכל"] + CATEGORIES)

with st.spinner("שולף שערי מטבע..."):
    forex_data = load_forex()

if selected_cat != "הכל":
    forex_data = [f for f in forex_data if f["category"] == selected_cat]

available = [f for f in forex_data if f.get("available")]

if not available:
    st.warning("לא ניתן לשלוף נתוני Forex כרגע.")
    st.stop()

tab1, tab2, tab3 = st.tabs(["🔥 הכי תנודתיים", "📋 כל הזוגות", "🏛️ מוסדיים"])

# ── TAB 1: Hot ────────────────────────────────────────────
with tab1:
    top_up   = sorted(available, key=lambda x: x.get("change_pct", 0), reverse=True)[:6]
    top_down = sorted(available, key=lambda x: x.get("change_pct", 0))[:6]

    c_up, c_dn = st.columns(2)
    with c_up:
        st.markdown("### 📈 עולים")
        for f in top_up:
            pct = f.get("change_pct", 0)
            if pct <= 0:
                continue
            with st.container(border=True):
                a, b = st.columns([2, 1])
                with a:
                    st.markdown(f"**{f['emoji']} {f['name']}**")
                    st.caption(f["category"])
                with b:
                    st.metric(f["pair"], f"{f['price']:.5f}", delta=f"+{pct:.4f}%")
                st.caption(f"מקור: {f['source']}")

    with c_dn:
        st.markdown("### 📉 יורדים")
        for f in top_down:
            pct = f.get("change_pct", 0)
            if pct >= 0:
                continue
            with st.container(border=True):
                a, b = st.columns([2, 1])
                with a:
                    st.markdown(f"**{f['emoji']} {f['name']}**")
                    st.caption(f["category"])
                with b:
                    st.metric(f["pair"], f"{f['price']:.5f}", delta=f"{pct:.4f}%")
                st.caption(f"מקור: {f['source']}")

# ── TAB 2: Full table ─────────────────────────────────────
with tab2:
    rows = []
    for i, f in enumerate(available, 1):
        pct = f.get("change_pct", 0)
        rows.append({
            "#": i,
            "זוג": f"{f['emoji']} {f['pair']}",
            "שם": f["name"],
            "שער": f"{f['price']:.5f}",
            "% שינוי": f"{'+' if pct>0 else ''}{pct:.4f}%",
            "קטגוריה": f["category"],
            "מקור": f.get("source","—"),
        })

    df = pd.DataFrame(rows).set_index("#")

    def color_pct(val):
        if str(val).startswith("+"): return "color:#1a7a1a;font-weight:600"
        if str(val).startswith("-"): return "color:#c0392b;font-weight:600"
        return ""

    st.dataframe(df.style.map(color_pct, subset=["% שינוי"]),
                 use_container_width=True, height=600)

# ── TAB 3: Institutional positions ───────────────────────
with tab3:
    st.subheader("🏛️ פוזיציות מוסדיות ידועות ב-Forex")
    st.caption("מקורות: CFTC COT, דוחות בנקים מרכזיים, Bloomberg")

    positions = get_forex_institutional_positions()
    for pos in positions:
        sentiment = pos["position"]
        color = "#1a7a1a" if "LONG" in sentiment or "BULLISH" in sentiment else "#c0392b" if "SHORT" in sentiment or "BEARISH" in sentiment else "#888"
        with st.container(border=True):
            c1, c2, c3 = st.columns([2, 1, 2])
            c1.markdown(f"**{pos['institution']}**")
            c2.markdown(f"**{pos['pair']}**")
            c3.markdown(f"**{pos['position']}**")
            st.caption(pos["note"])

    st.divider()
    st.subheader("📊 CFTC COT — פוזיציות ספקולנטים בוולוטות מרכזיות")
    st.info("נתוני CFTC מפורטים על Forex זמינים בטאב CFTC בדף הסחורות החיות")

    st.divider()
    st.subheader("🏦 יתרות מטבע חוץ — בנקים מרכזיים (IMF COFER)")
    reserve_data = [
        {"מדינה": "🇺🇸 ארה\"ב", "USD%": 59, "EUR%": 20, "JPY%": 6, "הערה": "דולר שומר על דומיננטיות"},
        {"מדינה": "🇨🇳 סין",    "USD%": 58, "EUR%": 20, "JPY%": 3, "הערה": "מגדילה זהב ויואן"},
        {"מדינה": "🇯🇵 יפן",    "USD%": 55, "EUR%": 22, "JPY%": 2, "הערה": "BoJ מתערב בשוק"},
        {"מדינה": "🇸🇦 סעודיה", "USD%": 70, "EUR%": 15, "JPY%": 3, "הערה": "פג נפט-דולר נחלש"},
    ]
    df_res = pd.DataFrame(reserve_data)
    st.dataframe(df_res, use_container_width=True, hide_index=True)

    st.caption("מקורות: IMF COFER, CFTC.gov, Bloomberg, Reuters | אינו ייעוץ השקעות")
