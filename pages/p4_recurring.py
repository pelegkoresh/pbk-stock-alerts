import streamlit as st
import pandas as pd
from datetime import datetime
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.rtl_utils import inject_rtl
from src.recurring_actions import analyze_institution_patterns, get_all_recurring_by_commodity
from src.sec_edgar import KNOWN_INSTITUTIONS, INSTITUTION_PROFILES

QUARTERS_HE = {
    "Q1": "Q1 — ינואר-מרץ",
    "Q2": "Q2 — אפריל-יוני",
    "Q3": "Q3 — יולי-ספטמבר",
    "Q4": "Q4 — אוקטובר-דצמבר",
}

now_month = datetime.now().month
now_q = "Q1" if now_month <= 3 else "Q2" if now_month <= 6 else "Q3" if now_month <= 9 else "Q4"

inject_rtl()
st.title("🔁 פעולות מוסדיות חוזרות")
st.caption("זיהוי דפוסי השקעה קבועים — מוסד שקונה כל שנה באותו רבעון פועל לפי אסטרטגיה")

tab1, tab2, tab3 = st.tabs(["🏛️ לפי מוסד", "📅 פעולות עונתיות", "🌍 חוצה-מוסדות"])

with tab1:
    col_sel, col_info = st.columns([2, 3])
    with col_sel:
        selected_inst = st.selectbox(
            "בחר מוסד",
            options=list(KNOWN_INSTITUTIONS.keys()),
            format_func=lambda x: f"{INSTITUTION_PROFILES[x]['name_he']} — {KNOWN_INSTITUTIONS[x]}"
        )
        num_filings = st.select_slider("כמה דיווחים לנתח?", options=[3, 4, 5, 6], value=4)
    with col_info:
        p = INSTITUTION_PROFILES.get(selected_inst, {})
        st.info(f"**{p.get('name_he','')} — {p.get('manager','')}** | {p.get('style','')} | {p.get('aum','')} נכסים מנוהלים")

    with st.spinner(f"מנתח {num_filings} דיווחים..."):
        result = analyze_institution_patterns(selected_inst, num_filings=num_filings)

    if result.get("error"):
        st.warning(result["error"])
    else:
        st.success(f"נותחו {result['filings_analyzed']} דיווחים | תקופה: {result['date_range']}")
        patterns = result["patterns"]

        if not patterns:
            st.info("לא נמצאו דפוסים חוזרים.")
        else:
            buy_p  = [x for x in patterns if "קנייה" in x["pattern_type"]]
            sell_p = [x for x in patterns if "מכירה" in x["pattern_type"]]
            hold_p = [x for x in patterns if "החזקה" in x["pattern_type"]]
            seas_p = [x for x in patterns if x["is_seasonal"]]

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("קניות חוזרות", len(buy_p))
            c2.metric("מכירות חוזרות", len(sell_p))
            c3.metric("החזקות יציבות", len(hold_p))
            c4.metric("דפוסים עונתיים", len(seas_p))
            st.divider()

            if buy_p:
                st.markdown("### 🟢 קניות חוזרות")
                df_buy = pd.DataFrame([{
                    "שם נכס": x["name"],
                    "עקביות %": x["consistency_pct"],
                    "מקרים": f"{x['occurrences']}/{x['total_filings']}",
                    "ממוצע $M": f"${x['avg_value_m']:,.0f}M",
                    "עונה": QUARTERS_HE.get(x["dominant_quarter"], "") if x["is_seasonal"] else "",
                    "דיווח אחרון": x["latest_date"],
                } for x in buy_p[:10]])
                df_buy.index = range(1, len(df_buy)+1)
                st.dataframe(df_buy, use_container_width=True, hide_index=True)

            if sell_p:
                st.markdown("### 🔴 מכירות חוזרות")
                df_sell = pd.DataFrame([{
                    "שם נכס": x["name"],
                    "עקביות %": x["consistency_pct"],
                    "מקרים": f"{x['occurrences']}/{x['total_filings']}",
                    "ממוצע $M": f"${x['avg_value_m']:,.0f}M",
                } for x in sell_p[:8]])
                df_sell.index = range(1, len(df_sell)+1)
                st.dataframe(df_sell, use_container_width=True, hide_index=True)

            if hold_p:
                st.markdown("### 🔵 החזקות יציבות")
                df_hold = pd.DataFrame([{
                    "נכס": x["name"],
                    "עקביות %": x["consistency_pct"],
                    "ממוצע $M": x["avg_value_m"],
                    "דיווחים": f"{x['occurrences']}/{x['total_filings']}"
                } for x in hold_p[:10]])
                st.dataframe(df_hold, use_container_width=True, hide_index=True)

with tab2:
    st.subheader(f"📅 פעולות עונתיות — {QUARTERS_HE.get(now_q, now_q)}")
    inst_options = list(KNOWN_INSTITUTIONS.keys())
    selected_multi = st.multiselect(
        "בחר מוסדות",
        options=inst_options,
        default=inst_options[:3],
        format_func=lambda x: INSTITUTION_PROFILES[x]["name_he"]
    )

    if st.button("🔍 נתח פעולות עונתיות"):
        all_seasonal = []
        progress = st.progress(0)
        for idx, cik in enumerate(selected_multi):
            with st.spinner(f"מנתח {INSTITUTION_PROFILES[cik]['name_he']}..."):
                res = analyze_institution_patterns(cik, num_filings=5)
            if not res.get("error"):
                for x in res["patterns"]:
                    if x["is_seasonal"] and x["dominant_quarter"] == now_q:
                        all_seasonal.append({**x, "institution_he": res["institution_he"], "manager": res["manager"]})
            progress.progress((idx + 1) / max(len(selected_multi), 1))

        if all_seasonal:
            all_seasonal.sort(key=lambda x: x["consistency_pct"], reverse=True)
            st.success(f"נמצאו {len(all_seasonal)} דפוסים ל-{QUARTERS_HE[now_q]}")
            df_s = pd.DataFrame([{
                "נכס": x["name"], "פעולה": x["pattern_type"],
                "מוסד": x["institution_he"], "עקביות %": x["consistency_pct"],
                "ממוצע $M": f"${x['avg_value_m']:,.0f}M",
            } for x in all_seasonal])
            df_s.index = range(1, len(df_s)+1)
            st.dataframe(df_s, use_container_width=True, hide_index=True)
        else:
            st.info(f"לא נמצאו דפוסים עונתיים ל-{QUARTERS_HE[now_q]}")
    else:
        st.info("בחר מוסדות ולחץ 'נתח'")

with tab3:
    st.subheader("🌍 נכסים שמוסדות מרובים קונים עונתית")
    st.warning("ניתוח זה עשוי לקחת 3-5 דקות")
    if st.button("🔍 הפעל ניתוח חוצה-מוסדות"):
        with st.spinner("מנתח..."):
            cross = get_all_recurring_by_commodity()
        if not cross:
            st.info("לא נמצאו דפוסים.")
        else:
            st.success(f"נמצאו {len(cross)} נכסים עם דפוסים עונתיים")
            df_c = pd.DataFrame([{
                "נכס": item["name"],
                "# מוסדות": len(item["institutions"]),
                "מחזיקים": ", ".join(item["institutions"]),
                "רבעונים": " | ".join([f"{QUARTERS_HE.get(q,q)}: {len(v)}" for q, v in item["quarters"].items()]),
            } for item in cross[:20]])
            df_c.index = range(1, len(df_c)+1)
            st.dataframe(df_c, use_container_width=True, hide_index=True)
    else:
        st.info("לחץ 'הפעל ניתוח' כדי להתחיל.")
