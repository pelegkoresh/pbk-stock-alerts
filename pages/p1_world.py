import streamlit as st
import pandas as pd
import sys, os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.rtl_utils import inject_rtl
from src.commodities_data import COMMODITIES, MONTHS_HE, TREND_COLOR


inject_rtl()
st.markdown("""
<style>
.season-card{border-radius:10px;padding:12px 16px;margin:6px 0;border:0.5px solid #e0e0e0}
.trend-chip{display:inline-block;padding:3px 10px;border-radius:12px;font-size:12px;font-weight:500;color:#fff;margin:2px}
</style>
""", unsafe_allow_html=True)

st.title("🌍 לוח סחורות עולמי — עונות, מדינות ומחירים")
st.caption("דפוסי ייצור ומחיר היסטוריים של סחורות עולמיות מרכזיות")

now_month = datetime.now().month
st.info(f"🗓️ החודש הנוכחי: **{MONTHS_HE[now_month]}** — הסיגנלים הרלוונטיים מוסמנים למטה")

tab_overview, tab_detail, tab_compare = st.tabs([
    "📊 סקירה כללית",
    "🔍 פירוט לפי סחורה",
    "🏆 השוואת מדינות",
])

# ── TAB 1 ─────────────────────────────────────
with tab_overview:
    st.subheader(f"סיגנלי מחיר לחודש {MONTHS_HE[now_month]}")
    cols = st.columns(len(COMMODITIES))
    for idx, (key, com) in enumerate(COMMODITIES.items()):
        current_trend, current_reason = "—", ""
        for ps in com["price_seasons"]:
            if now_month in ps["months"]:
                current_trend = ps["trend"]
                current_reason = ps["reason"]
                break
        color = TREND_COLOR.get(current_trend, "#888")
        with cols[idx]:
            st.markdown(f"""
<div style="border:1.5px solid {color}44;border-radius:12px;padding:14px;text-align:center;background:{color}08">
  <div style="font-size:28px">{com['emoji']}</div>
  <div style="font-size:14px;font-weight:600;margin:4px 0">{com['name']}</div>
  <div style="font-size:13px;font-weight:700;color:{color}">{current_trend}</div>
  <div style="font-size:11px;color:#666;margin-top:4px">{current_reason}</div>
</div>
""", unsafe_allow_html=True)

    st.divider()
    st.subheader("טבלת עונות שנתית — כל הסחורות")
    month_rows = []
    for m in range(1, 13):
        row = {"חודש": MONTHS_HE[m]}
        for key, com in COMMODITIES.items():
            for ps in com["price_seasons"]:
                if m in ps["months"]:
                    row[com["name"]] = ps["trend"]
                    break
        month_rows.append(row)
    df_months = pd.DataFrame(month_rows).set_index("חודש")

    def color_trend(val):
        c = TREND_COLOR.get(val, "#888")
        return f"background-color:{c}22;color:{c};font-weight:500"

    st.dataframe(df_months.style.map(color_trend), use_container_width=True, height=460)

# ── TAB 2 ─────────────────────────────────────
with tab_detail:
    selected_key = st.selectbox(
        "בחר סחורה",
        options=list(COMMODITIES.keys()),
        format_func=lambda x: f"{COMMODITIES[x]['emoji']} {COMMODITIES[x]['name']}"
    )
    com = COMMODITIES[selected_key]
    st.subheader(f"{com['emoji']} {com['name']}")
    st.caption(com["season_note"])

    col_s, col_p = st.columns(2)
    with col_s:
        st.markdown("#### 📅 עונות מחיר")
        for ps in com["price_seasons"]:
            months_str = ", ".join([MONTHS_HE[m] for m in ps["months"]])
            color = TREND_COLOR.get(ps["trend"], "#888")
            st.markdown(f"""
<div class="season-card">
  <span class="trend-chip" style="background:{color}">{ps['trend']}</span>
  <strong>{months_str}</strong><br>
  <span style="font-size:13px;color:#555">{ps['reason']}</span>
</div>""", unsafe_allow_html=True)

    with col_p:
        st.markdown("#### 🌐 מדינות מייצרות")
        for p in com["producers"]:
            bar_color = "#1565c0" if p["share_pct"] > 20 else "#2196f3" if p["share_pct"] > 10 else "#64b5f6"
            pct = min(p["share_pct"] * 3, 100)
            st.markdown(f"""
<div style="margin:8px 0">
  <div style="display:flex;justify-content:space-between;font-size:13px;margin-bottom:3px">
    <span>{p['flag']} <strong>{p['country']}</strong></span>
    <span style="color:{bar_color};font-weight:600">{p['share_pct']}%</span>
  </div>
  <div style="background:#e3f2fd;border-radius:4px;height:18px">
    <div style="width:{pct}%;height:100%;background:{bar_color};border-radius:4px"></div>
  </div>
  <div style="font-size:11px;color:#777;margin-top:2px">קציר: {p['peak_months']} | {p['notes']}</div>
</div>""", unsafe_allow_html=True)

    st.divider()
    prod_rows = [{"מדינה": f"{p['flag']} {p['country']}", "נתח %": p["share_pct"],
                  "תחילת עונה": p["season_start"], "חודשי שיא": p["peak_months"], "הערות": p["notes"]}
                 for p in com["producers"]]
    st.dataframe(pd.DataFrame(prod_rows), use_container_width=True, hide_index=True)

# ── TAB 3 ─────────────────────────────────────
with tab_compare:
    st.subheader("🏆 נתח ייצור לפי מדינה וסחורה")
    country_data = {}
    for key, com in COMMODITIES.items():
        for p in com["producers"]:
            cname = f"{p['flag']} {p['country']}"
            if cname not in country_data:
                country_data[cname] = {}
            country_data[cname][com["name"]] = p["share_pct"]

    df_c = pd.DataFrame(country_data).T.fillna(0).astype(int)
    df_c["סה\"כ"] = df_c.sum(axis=1)
    df_c = df_c.sort_values("סה\"כ", ascending=False)
    st.dataframe(df_c.style.background_gradient(cmap="Blues"), use_container_width=True, height=400)

    st.divider()
    st.subheader("גרף השוואה — Top 5 מדינות לכל סחורה")
    for key, com in COMMODITIES.items():
        top5 = sorted(com["producers"], key=lambda x: x["share_pct"], reverse=True)[:5]
        chart_df = pd.DataFrame([{"מדינה": f"{p['flag']} {p['country']}", "נתח %": p["share_pct"]} for p in top5]).set_index("מדינה")
        st.markdown(f"**{com['emoji']} {com['name']}**")
        st.bar_chart(chart_df)
        st.divider()
