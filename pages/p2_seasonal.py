import streamlit as st
import pandas as pd
from datetime import datetime
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.rtl_utils import inject_rtl
from src.commodities_data import SEASONAL_MOVES, MONTHS_HE, DEMAND_COLOR, SUPPLY_COLOR


inject_rtl()
st.markdown("""
<style>
.hot-card{border-radius:12px;padding:16px;margin:6px;border:2px solid #e67e22;background:#fff8f0}
.cold-card{border-radius:12px;padding:14px;margin:6px;border:0.5px solid #e0e0e0;background:#f9f9f9}
.move-pos{color:#c0392b;font-size:22px;font-weight:700}
.move-neg{color:#27ae60;font-size:22px;font-weight:700}
.badge{display:inline-block;padding:3px 9px;border-radius:10px;font-size:11px;font-weight:600;color:#fff}
</style>
""", unsafe_allow_html=True)

st.title("📈 לוח מסחר עונתי — הסחורה הכי חמה לכל חודש")
st.caption("ממוצע תנועות היסטוריות | מטרה: לזהות את ההזדמנות הטובה ביותר לכל עונה")

now_month = datetime.now().month

tab1, tab2, tab3 = st.tabs([
    "🔥 הסחורה החמה עכשיו",
    "📅 סרגל שנתי",
    "📊 היסטוריית תנועות",
])

# ══════════════════════════════════════════════
# TAB 1 — Hot right now
# ══════════════════════════════════════════════
with tab1:
    st.subheader(f"🔥 {MONTHS_HE[now_month]} — הסחורות הכי חמות החודש")

    month_data = []
    for key, com in SEASONAL_MOVES.items():
        m = com["monthly"][now_month]
        month_data.append({
            "key": key, "name": com["name"], "emoji": com["emoji"],
            **m
        })
    month_data.sort(key=lambda x: abs(x["avg_move"]), reverse=True)

    hot = [d for d in month_data if d["hot"]]
    cold = [d for d in month_data if not d["hot"]]

    if hot:
        st.markdown("### 🚀 הזדמנויות מסחר — החודש")
        cols = st.columns(len(hot))
        for i, d in enumerate(hot):
            sign = "+" if d["avg_move"] > 0 else ""
            arrow = "🟢" if d["avg_move"] > 0 else "🔴"
            with cols[i]:
                dem_color = DEMAND_COLOR.get(d["demand"], "#888")
                sup_color = SUPPLY_COLOR.get(d["supply"], "#888")
                st.markdown(f"""
<div class="hot-card">
  <div style="font-size:30px;text-align:center">{d['emoji']}</div>
  <div style="font-size:16px;font-weight:700;text-align:center;margin:6px 0">{d['name']}</div>
  <div style="text-align:center;font-size:26px;font-weight:800;color:{'#c0392b' if d['avg_move']>0 else '#27ae60'}">
    {arrow} {sign}{d['avg_move']}%
  </div>
  <div style="font-size:12px;color:#555;text-align:center;margin:8px 0">{d['reason']}</div>
  <div style="display:flex;justify-content:space-between;margin-top:10px">
    <span><span class="badge" style="background:{dem_color}">ביקוש: {d['demand']}</span></span>
    <span><span class="badge" style="background:{sup_color}">היצע: {d['supply']}</span></span>
  </div>
</div>
""", unsafe_allow_html=True)

    st.divider()

    if cold:
        st.markdown("### ❄️ חלשות החודש — הימנע או שקול שורט")
        cols2 = st.columns(len(cold))
        for i, d in enumerate(cold):
            sign = "+" if d["avg_move"] > 0 else ""
            with cols2[i]:
                st.markdown(f"""
<div class="cold-card">
  <div style="font-size:22px;text-align:center">{d['emoji']}</div>
  <div style="font-size:14px;font-weight:600;text-align:center">{d['name']}</div>
  <div style="text-align:center;font-size:18px;font-weight:700;color:{'#e67e22' if d['avg_move']>0 else '#2980b9'}">
    {sign}{d['avg_move']}%
  </div>
  <div style="font-size:11px;color:#777;text-align:center;margin-top:6px">{d['reason']}</div>
</div>
""", unsafe_allow_html=True)

    st.divider()
    st.markdown("### 📋 טבלת המלצות — " + MONTHS_HE[now_month])
    rec_rows = []
    for d in month_data:
        action = "🟢 קנה" if d["avg_move"] > 2 else "🔴 מכור/שורט" if d["avg_move"] < -2 else "⚪ המתן"
        sign = "+" if d["avg_move"] > 0 else ""
        rec_rows.append({
            "סחורה": f"{d['emoji']} {d['name']}",
            "תנועה ממוצעת": f"{sign}{d['avg_move']}%",
            "ביקוש": d["demand"],
            "היצע": d["supply"],
            "פעולה מומלצת": action,
            "סיבה": d["reason"],
        })
    df_rec = pd.DataFrame(rec_rows)
    st.dataframe(df_rec, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════
# TAB 2 — Annual bar / calendar
# ══════════════════════════════════════════════
with tab2:
    st.subheader("📅 סרגל שנתי — עליות וירידות לפי חודש")

    selected_com = st.selectbox(
        "בחר סחורה",
        options=list(SEASONAL_MOVES.keys()),
        format_func=lambda x: f"{SEASONAL_MOVES[x]['emoji']} {SEASONAL_MOVES[x]['name']}"
    )
    com = SEASONAL_MOVES[selected_com]

    bar_rows = []
    for m in range(1, 13):
        md = com["monthly"][m]
        bar_rows.append({
            "חודש": MONTHS_HE[m],
            "תנועה %": md["avg_move"],
            "ביקוש": md["demand"],
            "היצע": md["supply"],
            "חם": "🔥 כן" if md["hot"] else "❄️ לא",
            "סיבה": md["reason"],
        })
    df_bar = pd.DataFrame(bar_rows).set_index("חודש")

    st.bar_chart(df_bar[["תנועה %"]])

    st.divider()
    st.subheader("פירוט חודשי מלא")

    for m in range(1, 13):
        md = com["monthly"][m]
        is_now = (m == now_month)
        sign = "+" if md["avg_move"] > 0 else ""
        color = "#c0392b" if md["avg_move"] > 0 else "#27ae60"
        border = "2px solid #f39c12" if is_now else "0.5px solid #e0e0e0"
        bg = "#fffbf0" if is_now else "#fff"
        dem_c = DEMAND_COLOR.get(md["demand"], "#888")
        sup_c = SUPPLY_COLOR.get(md["supply"], "#888")
        st.markdown(f"""
<div style="border:{border};border-radius:10px;padding:12px 18px;margin:5px 0;background:{bg};display:flex;align-items:center;gap:16px;flex-wrap:wrap">
  <div style="min-width:80px;font-weight:{'700' if is_now else '400'};font-size:14px">
    {'👉 ' if is_now else ''}{MONTHS_HE[m]}
  </div>
  <div style="color:{color};font-size:18px;font-weight:700;min-width:70px">{sign}{md['avg_move']}%</div>
  <div style="flex:1;font-size:13px;color:#555">{md['reason']}</div>
  <div style="display:flex;gap:6px">
    <span class="badge" style="background:{dem_c};color:#fff;padding:3px 8px;border-radius:8px;font-size:11px">ביקוש: {md['demand']}</span>
    <span class="badge" style="background:{sup_c};color:#fff;padding:3px 8px;border-radius:8px;font-size:11px">היצע: {md['supply']}</span>
    {'<span style="background:#f39c12;color:#fff;padding:3px 8px;border-radius:8px;font-size:11px">🔥 חם</span>' if md['hot'] else ''}
  </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# TAB 3 — Heatmap all commodities all months
# ══════════════════════════════════════════════
with tab3:
    st.subheader("📊 מפת חום — כל הסחורות × כל החודשים")

    rows = []
    for m in range(1, 13):
        row = {"חודש": MONTHS_HE[m]}
        for key, com in SEASONAL_MOVES.items():
            row[com["name"]] = com["monthly"][m]["avg_move"]
        rows.append(row)
    df_heat = pd.DataFrame(rows).set_index("חודש")

    def color_move(val):
        if val > 4:  return "background-color:#c0392b;color:white;font-weight:700"
        if val > 2:  return "background-color:#e67e22;color:white;font-weight:600"
        if val > 0:  return "background-color:#f39c12;color:white"
        if val > -2: return "background-color:#82ccdd;color:#333"
        if val > -4: return "background-color:#27ae60;color:white;font-weight:600"
        return            "background-color:#1a7a1a;color:white;font-weight:700"

    st.dataframe(df_heat.style.map(color_move), use_container_width=True, height=460)

    st.markdown("""
<div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:8px;font-size:12px">
  <span style="background:#c0392b;color:#fff;padding:2px 8px;border-radius:6px">+4% ומעלה — שיא עלייה</span>
  <span style="background:#e67e22;color:#fff;padding:2px 8px;border-radius:6px">+2% עד +4% — עלייה חזקה</span>
  <span style="background:#f39c12;color:#fff;padding:2px 8px;border-radius:6px">0% עד +2% — עלייה קלה</span>
  <span style="background:#82ccdd;color:#333;padding:2px 8px;border-radius:6px">0% עד -2% — ירידה קלה</span>
  <span style="background:#27ae60;color:#fff;padding:2px 8px;border-radius:6px">-2% עד -4% — ירידה חזקה</span>
  <span style="background:#1a7a1a;color:#fff;padding:2px 8px;border-radius:6px">-4% ומטה — שיא ירידה</span>
</div>
""", unsafe_allow_html=True)

    st.divider()
    st.subheader("🏆 דירוג: איזו סחורה הכי חמה לפי חודש")
    ranking = []
    for m in range(1, 13):
        best = max(SEASONAL_MOVES.items(), key=lambda x: x[1]["monthly"][m]["avg_move"])
        worst = min(SEASONAL_MOVES.items(), key=lambda x: x[1]["monthly"][m]["avg_move"])
        bm = best[1]["monthly"][m]
        wm = worst[1]["monthly"][m]
        ranking.append({
            "חודש": MONTHS_HE[m],
            "🔥 הכי חם": f"{best[1]['emoji']} {best[1]['name']} (+{bm['avg_move']}%)",
            "❄️ הכי קר": f"{worst[1]['emoji']} {worst[1]['name']} ({wm['avg_move']}%)",
        })
    df_rank = pd.DataFrame(ranking).set_index("חודש")
    st.dataframe(df_rank, use_container_width=True, height=460)
