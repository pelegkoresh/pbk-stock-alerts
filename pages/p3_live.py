import streamlit as st
import pandas as pd
from datetime import datetime
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.rtl_utils import inject_rtl
from src.commodities_live import fetch_all_commodities_live, fetch_commodity_live, COMMODITY_SYMBOLS
from src.commodities_data import SEASONAL_MOVES, MONTHS_HE
from src.institutional_overlay import find_institutional_holders, render_institutional_holders, COMMODITY_INSTITUTION_MAP


inject_rtl()
st.markdown("""
<style>
.live-card{border-radius:12px;padding:16px;margin:4px;text-align:center}
.big-price{font-size:22px;font-weight:700;margin:4px 0}
.change-up{color:#c0392b;font-size:16px;font-weight:600}
.change-dn{color:#27ae60;font-size:16px;font-weight:600}
.vol-text{font-size:12px;color:#888;margin-top:4px}
</style>
""", unsafe_allow_html=True)

st.title("📡 סחורות בזמן אמת — מחיר, ווליום ותנודה")
st.caption(f"עדכון: {datetime.now().strftime('%H:%M:%S')} | מקור: Twelve Data + Yahoo Finance")

now_month = datetime.now().month

col_refresh, col_info = st.columns([1, 4])
with col_refresh:
    if st.button("🔄 רענן נתונים"):
        st.cache_data.clear()
        st.rerun()
with col_info:
    st.caption(f"חודש נוכחי: **{MONTHS_HE[now_month]}** | הסחורות ממוינות לפי % תנודה")

tab1, tab2, tab3 = st.tabs([
    "🔥 הכי חמות עכשיו",
    "📋 טבלה מלאה",
    "🔍 פירוט סחורה",
])

@st.cache_data(ttl=300)
def load_live():
    return fetch_all_commodities_live()

@st.cache_data(ttl=3600)
def load_holdings_cache():
    from src.sec_edgar import get_recent_13f_filings, get_holdings_from_filing, KNOWN_INSTITUTIONS
    import time
    cache = {}
    for cik in list(KNOWN_INSTITUTIONS.keys())[:5]:
        filings = get_recent_13f_filings(cik, limit=1)
        if filings:
            h = get_holdings_from_filing(cik, filings[0]['accession'])
            cache[cik] = {'holdings': h, 'filing_date': filings[0]['date']}
        time.sleep(0.2)
    return cache

with st.spinner("שולף נתונים חיים..."):
    live_data = load_live()

# ── TAB 1 — Hot right now ─────────────────────────────────
with tab1:
    st.subheader("🔥 הסחורות עם התנודה הגדולה ביותר היום")

    top_up   = [d for d in live_data if d.get("change_pct", 0) > 0 and not d.get("error")][:4]
    top_down = [d for d in live_data if d.get("change_pct", 0) < 0 and not d.get("error")][:4]

    col_up, col_dn = st.columns(2)

    with col_up:
        st.markdown("### 📈 עולות")
        for d in top_up:
            seasonal = SEASONAL_MOVES.get(d["key"], {})
            season_hot = seasonal.get("monthly", {}).get(now_month, {}).get("hot", False)
            border = "2px solid #c0392b" if season_hot else "1px solid #fadbd8"
            vol_str = f"{d['volume']:,}" if d['volume'] > 0 else "—"
            st.markdown(f"""
<div class="live-card" style="border:{border};background:#fff8f8">
  <div style="font-size:26px">{d['emoji']}</div>
  <div style="font-weight:600;font-size:15px">{d['name']}</div>
  <div class="big-price">${d['price']:,.3f}</div>
  <div class="change-up">▲ +{d['change_pct']}%</div>
  <div class="vol-text">ווליום: {vol_str}</div>
  {'<div style="font-size:11px;color:#e67e22;margin-top:4px">🔥 עונה חמה היסטורית</div>' if season_hot else ''}
  <div style="font-size:10px;color:#bbb;margin-top:4px">{d['source']}</div>
</div>
""", unsafe_allow_html=True)

    with col_dn:
        st.markdown("### 📉 יורדות")
        for d in top_down:
            seasonal = SEASONAL_MOVES.get(d["key"], {})
            season_note = seasonal.get("monthly", {}).get(now_month, {}).get("reason", "")
            vol_str = f"{d['volume']:,}" if d['volume'] > 0 else "—"
            st.markdown(f"""
<div class="live-card" style="border:1px solid #d5f5e3;background:#f9fff9">
  <div style="font-size:26px">{d['emoji']}</div>
  <div style="font-weight:600;font-size:15px">{d['name']}</div>
  <div class="big-price">${d['price']:,.3f}</div>
  <div class="change-dn">▼ {d['change_pct']}%</div>
  <div class="vol-text">ווליום: {vol_str}</div>
  <div style="font-size:10px;color:#bbb;margin-top:4px">{d['source']}</div>
</div>
""", unsafe_allow_html=True)

    st.divider()
    st.subheader("⚡ מיזוג עונתיות + נתוני היום")
    st.caption("כשגם ההיסטוריה וגם הנתון של היום מצביעים על אותה כיוון — סיגנל חזק יותר")

    signals = []
    for d in live_data:
        if d.get("error") or d.get("price", 0) == 0:
            continue
        seasonal = SEASONAL_MOVES.get(d["key"], {})
        month_data = seasonal.get("monthly", {}).get(now_month, {})
        hist_move = month_data.get("avg_move", 0)
        live_move = d.get("change_pct", 0)
        season_hot = month_data.get("hot", False)

        if hist_move > 0 and live_move > 0:
            alignment = "🟢 חזק — שניהם עולים"
            score = hist_move + live_move
        elif hist_move < 0 and live_move < 0:
            alignment = "🔴 ירידה כפולה"
            score = hist_move + live_move
        elif season_hot and live_move > 0:
            alignment = "🟡 עונה חמה + עולה היום"
            score = hist_move
        else:
            alignment = "⚪ לא מיושר"
            score = 0

        signals.append({
            "סחורה": f"{d['emoji']} {d['name']}",
            "מחיר": f"${d['price']:,.3f}",
            "% היום": f"{'+' if live_move>0 else ''}{live_move}%",
            "ממוצע היסטורי": f"{'+' if hist_move>0 else ''}{hist_move}%",
            "סיגנל": alignment,
            "ציון": round(score, 1),
        })

    signals.sort(key=lambda x: abs(x["ציון"]), reverse=True)
    df_sig = pd.DataFrame(signals)
    if not df_sig.empty:
        df_sig.index = range(1, len(df_sig)+1)
        st.dataframe(df_sig, use_container_width=True, hide_index=True)

# ── TAB 2 — Full table ────────────────────────────────────
with tab2:
    st.subheader("📋 כל הסחורות — נתונים מלאים")

    rows = []
    for d in live_data:
        vol_str = f"{d['volume']:,}" if d.get("volume", 0) > 0 else "—"
        sign = "▲" if d.get("change_pct", 0) > 0 else "▼"
        rows.append({
            "סחורה": f"{d['emoji']} {d['name']}",
            "מחיר": f"${d.get('price', 0):,.3f}",
            "פתיחה": f"${d.get('open', 0):,.3f}" if d.get("open") else "—",
            "גבוה": f"${d.get('high', 0):,.3f}" if d.get("high") else "—",
            "נמוך": f"${d.get('low', 0):,.3f}" if d.get("low") else "—",
            "% שינוי": f"{sign} {abs(d.get('change_pct',0)):.2f}%",
            "ווליום": vol_str,
            "מקור": d.get("source", "—"),
        })

    df_full = pd.DataFrame(rows)
    df_full.index = range(1, len(df_full)+1)

    def color_change(val):
        if "▲" in str(val): return "color:#c0392b;font-weight:600"
        if "▼" in str(val): return "color:#27ae60;font-weight:600"
        return ""

    st.dataframe(df_full.style.map(color_change, subset=["% שינוי"]),
                 use_container_width=True, height=400)

    st.divider()
    st.subheader("גרף % שינוי — כל הסחורות")
    chart_data = pd.DataFrame([
        {"סחורה": f"{d['emoji']} {d['name']}", "% שינוי": d.get("change_pct", 0)}
        for d in live_data if not d.get("error")
    ]).set_index("סחורה")
    st.bar_chart(chart_data)

# ── TAB 3 — Single commodity detail ──────────────────────
with tab3:
    sel = st.selectbox(
        "בחר סחורה לפירוט",
        options=list(COMMODITY_SYMBOLS.keys()),
        format_func=lambda x: f"{COMMODITY_SYMBOLS[x]['emoji']} {COMMODITY_SYMBOLS[x]['name']}"
    )

    d = next((x for x in live_data if x["key"] == sel), None)
    if not d:
        with st.spinner("שולף..."):
            d = fetch_commodity_live(sel)

    if d and not d.get("error"):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("מחיר נוכחי", f"${d['price']:,.3f}")
        c2.metric("% שינוי יומי",
                  f"+{d['change_pct']}%" if d['change_pct'] > 0 else f"{d['change_pct']}%",
                  delta=f"{d['change_pct']}%")
        c3.metric("ווליום", f"{d['volume']:,}" if d['volume'] > 0 else "—")
        c4.metric("מקור", d["source"])

        if d.get("high") and d.get("low"):
            c5, c6, c7 = st.columns(3)
            c5.metric("פתיחה", f"${d['open']:,.3f}")
            c6.metric("גבוה יומי", f"${d['high']:,.3f}")
            c7.metric("נמוך יומי", f"${d['low']:,.3f}")

    seasonal = SEASONAL_MOVES.get(sel, {})
    if seasonal:
        st.divider()
        month_data = seasonal.get("monthly", {}).get(now_month, {})
        st.subheader(f"עונתיות {MONTHS_HE[now_month]} — {seasonal['name']}")
        col_a, col_b = st.columns(2)
        with col_a:
            hist = month_data.get("avg_move", 0)
            sign = "+" if hist > 0 else ""
            st.metric("ממוצע היסטורי לחודש זה", f"{sign}{hist}%")
            st.metric("ביקוש", month_data.get("demand", "—"))
        with col_b:
            st.metric("היצע", month_data.get("supply", "—"))
            hot = month_data.get("hot", False)
            st.metric("עונה חמה?", "🔥 כן" if hot else "❄️ לא")
        st.info(f"**סיבה היסטורית:** {month_data.get('reason','')}")

    st.divider()
    st.caption("נתונים חיים: Twelve Data + Yahoo Finance | עונתיות: ניתוח היסטורי")
