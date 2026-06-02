import streamlit as st
import pandas as pd
from datetime import datetime
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.rtl_utils import inject_rtl
from src.hot_score import rank_all_commodities
from src.sec_edgar import get_recent_13f_filings, get_holdings_from_filing, KNOWN_INSTITUTIONS
from src.commodities_data import MONTHS_HE


inject_rtl()
st.markdown("""
<style>
.score-ring{display:inline-flex;align-items:center;justify-content:center;
  width:56px;height:56px;border-radius:50%;font-size:18px;font-weight:800;
  border:3px solid;flex-shrink:0}
.dir-bull{color:#c0392b;font-weight:700}
.dir-bear{color:#27ae60;font-weight:700}
.dir-mix{color:#888;font-weight:500}
.supply-item{font-size:12px;background:#fff3cd;border-radius:6px;
  padding:4px 8px;margin:2px 0;border-left:3px solid #f39c12}
.score-bar-outer{height:8px;background:#e0e0e0;border-radius:4px;margin-top:4px}
</style>
""", unsafe_allow_html=True)

st.title("🔥 סחורות חמות — דירוג מולטי-קריטריון")
st.caption("ציון 0–100 | 4 קריטריונים: ווליום מוסדי + תנודה חיה + גירעון היצע + עקביות עונתית")

now_month = datetime.now().month
st.info(f"🗓️ חודש נוכחי: **{MONTHS_HE[now_month]}** | נתונים חיים + ניתוח היסטורי משולבים")

@st.cache_data(ttl=3600, show_spinner=False)
def load_holdings():
    cache = {}
    for cik in list(KNOWN_INSTITUTIONS.keys())[:6]:
        filings = get_recent_13f_filings(cik, limit=1)
        if filings:
            h = get_holdings_from_filing(cik, filings[0]["accession"])
            cache[cik] = {"holdings": h, "filing_date": filings[0]["date"]}
        import time; time.sleep(0.2)
    return cache

col_run, col_note = st.columns([1, 4])
with col_run:
    run = st.button("🚀 חשב דירוג", type="primary")
with col_note:
    st.caption("שולף נתונים חיים + מחשב 4 ציונים לכל סחורה | ~60 שניות")

if run:
    with st.spinner("טוען אחזקות מוסדיות..."):
        hcache = load_holdings()
    with st.spinner("מחשב ציוני סחורות..."):
        ranked = rank_all_commodities(hcache)
    st.session_state["ranked"] = ranked

ranked = st.session_state.get("ranked", [])

if not ranked:
    st.info("לחץ 'חשב דירוג' כדי להתחיל")
    st.stop()

# ── Top 3 hero cards ──────────────────────────────────────
st.divider()
st.subheader("🥇 Top 3 — הסחורות הכי חמות עכשיו")
top3 = ranked[:3]
cols = st.columns(3)
medals = ["🥇", "🥈", "🥉"]
score_colors = ["#c0392b", "#e67e22", "#f39c12"]

for i, d in enumerate(top3):
    with cols[i]:
        color = score_colors[i]
        dir_text = "📈 BULLISH" if d["direction"] == "BULLISH" else "📉 BEARISH" if d["direction"] == "BEARISH" else "↔️ MIXED"
        pct_sign = "+" if d["live_pct"] > 0 else ""
        with st.container(border=True):
            st.markdown(f"## {medals[i]} {d['emoji']} {d['name']}")
            st.metric("ציון", d['total_score'], help="מתוך 100")
            st.metric("% היום", f"{pct_sign}{d['live_pct']}%")
            st.metric("מחיר", f"${d['live_price']:,.2f}")
            st.caption(d.get('seasonal_reason','')[:80])

# ── Full ranking table ────────────────────────────────────
st.divider()
st.subheader("📊 טבלת דירוג מלאה")

tab_table, tab_detail, tab_supply = st.tabs([
    "📋 טבלה מלאה",
    "🔍 פירוט ציונים",
    "🌍 סיגנלי היצע",
])

with tab_table:
    rows = []
    for d in ranked:
        pct_sign = "+" if d["live_pct"] > 0 else ""
        rows.append({
            "#": d["rank"],
            "סחורה": f"{d['emoji']} {d['name']}",
            "ציון כולל": d["total_scale"] if "total_scale" in d else d["total_score"],
            "🏛️ מוסדי": d["score_institutional"],
            "📈 תנודה": d["score_live"],
            "🌍 גירעון": d["score_supply"],
            "🔁 עונתי": d["score_seasonal"],
            "% היום": f"{pct_sign}{d['live_pct']}%",
            "מחיר": f"${d['live_price']:,.3f}",
            "כיוון": "📈" if d["direction"] == "BULLISH" else "📉" if d["direction"] == "BEARISH" else "↔️",
        })
    df = pd.DataFrame(rows).set_index("#")

    def color_score(val):
        try:
            v = float(val)
            if v >= 70: return "background-color:#c0392b22;color:#c0392b;font-weight:700"
            if v >= 50: return "background-color:#e67e2222;color:#e67e22;font-weight:600"
            if v >= 30: return "background-color:#f39c1222;color:#f39c12"
            return ""
        except: return ""

    def color_pct(val):
        if "+" in str(val): return "color:#c0392b;font-weight:600"
        if str(val).startswith("-"): return "color:#27ae60;font-weight:600"
        return ""

    st.dataframe(
        df.style.map(color_score, subset=["ציון כולל"]).map(color_pct, subset=["% היום"]),
        use_container_width=True, height=380
    )

with tab_detail:
    sel = st.selectbox("בחר סחורה לפירוט", [f"{d['emoji']} {d['name']}" for d in ranked])
    sel_data = next((d for d in ranked if f"{d['emoji']} {d['name']}" == sel), None)
    if sel_data:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("ציון כולל", sel_data["total_score"], help="0-100")
        c2.metric("ווליום מוסדי $M", f"${sel_data['inst_value_m']:,.0f}M")
        c3.metric("תנודה יומית", f"{'+' if sel_data['live_pct']>0 else ''}{sel_data['live_pct']}%")
        c4.metric("עקביות עונתית", f"{'+' if sel_data['hist_move']>0 else ''}{sel_data['hist_move']}%")

        st.divider()
        st.markdown("#### פירוט ציונים")
        score_breakdown = pd.DataFrame([
            {"קריטריון": "🏛️ ווליום מוסדי (30%)", "ציון": sel_data["score_institutional"], "מקסימום": 30},
            {"קריטריון": "📈 תנודה + ווליום (25%)", "ציון": sel_data["score_live"], "מקסימום": 25},
            {"קריטריון": "🌍 גירעון היצע (25%)", "ציון": sel_data["score_supply"], "מקסימום": 25},
            {"קריטריון": "🔁 עקביות עונתית (20%)", "ציון": sel_data["score_seasonal"], "מקסימום": 20},
        ])
        st.dataframe(score_breakdown, use_container_width=True, hide_index=True)

        if sel_data["inst_list"]:
            st.markdown(f"**🏛️ מוסדות מושקעים:** {', '.join(sel_data['inst_list'])}")

        st.markdown(f"**📅 עונתיות {sel_data['month_name']}:** {sel_data['seasonal_reason']}")
        st.markdown(f"**📊 ביקוש:** {sel_data['demand']}")

        if sel_data["supply_signals"]:
            st.markdown("#### 🌍 סיגנלי גירעון היצע")
            for sig in sel_data["supply_signals"]:
                severity_color = "#c0392b" if sig["severity"] >= 8 else "#e67e22" if sig["severity"] >= 6 else "#f39c12"
                st.warning(f"🚨 **{sig['country']}** — {sig['signal']} | חומרה: {sig['severity']}/10")

with tab_supply:
    st.subheader("🌍 כל סיגנלי גירעון ההיצע — לפי חומרה")
    all_signals = []
    for d in ranked:
        for sig in d.get("supply_signals", []):
            all_signals.append({
                "סחורה": f"{d['emoji']} {d['name']}",
                "מדינה": sig["country"],
                "סיגנל": sig["signal"],
                "חומרה": sig["severity"],
                "ציון סחורה": d["total_score"],
            })
    if all_signals:
        df_sup = pd.DataFrame(all_signals).sort_values("חומרה", ascending=False)
        df_sup.index = range(1, len(df_sup)+1)
        def color_sev(val):
            try:
                v = int(val)
                if v >= 8: return "color:#c0392b;font-weight:700"
                if v >= 6: return "color:#e67e22;font-weight:600"
                return "color:#f39c12"
            except: return ""
        st.dataframe(df_sup.style.map(color_sev, subset=["חומרה"]), use_container_width=True, height=400)
